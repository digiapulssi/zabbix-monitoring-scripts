#!/usr/bin/env python3
"""
Provides functionally extended version of py-zabbix ZabbixSender and pure python utility for
sending trapper data.
"""
from argparse import ArgumentParser
from configparser import RawConfigParser
from datetime import datetime
from io import StringIO
from typing import Callable, List, Optional, Tuple
import functools
import sys

from pyzabbix import ZabbixSender, ZabbixMetric, ZabbixResponse

# NOTE: Python 3 and OpenSSL development files required to install sslpsk
# Packages needed only during installation and can be removed afterwards
# ---------------------------------------------------------------------
# RedHat/CentOS: sudo yum install python3-devel openssl-devel ; pip install sslpsk

# Socket wrapper implementation adapted from GitHub issue:
# https://github.com/adubkov/py-zabbix/issues/114
class PyZabbixPSKSocketWrapper:
    """Implements ssl.wrap_socket with PSK instead of certificates.

    Proxies calls to a `socket` instance.
    """

    def __init__(self, sock, *, identity, psk):
        self.__sock = sock
        self.__identity = identity
        self.__psk = psk

    def connect(self, *args, **kwargs):
        """
        Opens socket connection.
        """
        # PSK is optional to use so SSL dependencies are only imported when actually needed
        # Otherwise script would require bunch of system packages to be installed unnecessarily
        import ssl  # pylint: disable=import-outside-toplevel
        import sslpsk  # pylint: disable=import-outside-toplevel

        # `sslpsk.wrap_socket` must be called *after* socket.connect,
        # while the `ssl.wrap_socket` must be called *before* socket.connect.
        self.__sock.connect(*args, **kwargs)

        # `sslv3 alert bad record mac` exception means incorrect PSK
        self.__sock = sslpsk.wrap_socket(
            self.__sock,
            # https://github.com/zabbix/zabbix/blob/f0a1ad397e5653238638cd1a65a25ff78c6809bb/src/libs/zbxcrypto/tls.c#L3231
            ssl_version=ssl.PROTOCOL_TLSv1_2,
            # https://github.com/zabbix/zabbix/blob/f0a1ad397e5653238638cd1a65a25ff78c6809bb/src/libs/zbxcrypto/tls.c#L3179
            ciphers="PSK-AES128-CBC-SHA",
            psk=(self.__psk, self.__identity),
        )

    def __getattr__(self, name):
        return getattr(self.__sock, name)


class ZabbixSenderPSK(ZabbixSender):
    """
    Extends py-zabbix library's ZabbixSender by implementing PSK support and sending semantics
    of command line sender (command line version =>4.2).

    User can also specify error_listener function which is called in case send call fail. If
    listener raises another error, the send is terminated.

    This version always uses Zabbix agent configuration file.
    """

    def __init__(self,
                 config_file: str = None,
                 error_listener: Callable[[OSError], None] = None):
        if config_file is None:
            config_file = '/etc/zabbix/zabbix_agentd.conf'
        self.config_file = config_file
        self.error_listener = error_listener
        self._config = None

        psk_info = self._get_psk_info()
        if psk_info:
            wrapper = functools.partial(
                PyZabbixPSKSocketWrapper,
                identity=psk_info[0],
                psk=psk_info[1])
            ZabbixSender.__init__(self, use_config=config_file, socket_wrapper=wrapper)
        else:
            ZabbixSender.__init__(self, use_config=config_file)

    def _load_agent_config(self):
        if self._config is None:
            with open(self.config_file, 'r') as file_handle:
                config_file_data = '[root]\n' + file_handle.read()

            config_file_fp = StringIO(config_file_data)
            config = RawConfigParser(strict=False)
            config.read_file(config_file_fp)
            self._config = config
        return self._config

    def _get_psk_info(self) -> Optional[Tuple[str, bytearray]]:
        config = self._load_agent_config()

        tls_connect = config.get('root', 'TLSConnect', fallback=None)
        if tls_connect and tls_connect == 'psk':
            psk_identity = config.get('root', 'TLSPSKIdentity', fallback=None)
            if psk_identity is None:
                raise ValueError('Error in config file, TLSPSKIdentity missing')

            psk_file = config.get('root', 'TLSPSKFile', fallback=None)
            if psk_file is None:
                raise ValueError('Error in config file, TLSPSKFile missing.')

            with open(psk_file, 'r') as file_handle:
                psk_key = bytes.fromhex(file_handle.read().strip())

            return (psk_identity, psk_key)

        return None

    def get_agent_config(self):
        """
        Returns the agent configuration.
        """
        return self._load_agent_config()

    def send(self, metrics: List[ZabbixMetric]) -> ZabbixResponse:
        zabbix_uris = self.zabbix_uri
        response = None
        for uri in zabbix_uris:
            try:
                self.zabbix_uri = [uri]
                response = ZabbixSender.send(self, metrics)
            except OSError as ex:
                if self.error_listener:
                    self.error_listener(ex)
        self.zabbix_uri = zabbix_uris

        # Only last successful response is returned, this follows ZabbixSender semantics
        if response is None:
            raise OSError('Could not send values to any Zabbix server.')
        return response

def _print_cfg_value(config: RawConfigParser, key: str):
    print(f"{key}: {config.get('root', key, fallback='-')}")



def display_config(sender: ZabbixSenderPSK):
    """
    Prints trapper related Zabbix agent configuration options to stdout.
    """
    config = sender.get_agent_config()
    _print_cfg_value(config, 'ServerActive')
    _print_cfg_value(config, 'Hostname')
    _print_cfg_value(config, 'TLSConnect')
    _print_cfg_value(config, 'TLSPSKIdentity')
    _print_cfg_value(config, 'TLSPSKFile')


def send_from_file(sender: ZabbixSenderPSK, input_file: str, with_timestamps: bool = False):
    """
    Sends values from file to Zabbix server.
    """
    metrics = []
    with sys.stdin if input_file == '-' else open(input_file, 'r') as file_handle:
        for line in file_handle:
            line = line.strip() # Remove newline
            if with_timestamps:
                parts = line.split(' ', 4)
                metrics.append(ZabbixMetric(parts[0], parts[1], parts[3], clock(parts[2])))
            else:
                parts = line.split(' ', 3)
                metrics.append(ZabbixMetric(parts[0], parts[1], parts[2]))

    response = sender.send(metrics)
    print(response)


def send_value(sender: ZabbixSenderPSK, host: str, key: str, value: str, clock_value: int):
    """
    Sends single value to Zabbix server.
    """
    if host is None:
        config = sender.get_agent_config()
        host = config.get('root', 'Hostname', fallback=None)
    if host is None:
        raise ValueError('Cannot resolve trapper hostname.')
    metric = ZabbixMetric(host, key, value, clock_value)
    response = sender.send([metric])
    print(response)


def run_sender(args):
    """
    Executes the sender utility.
    """
    sender = ZabbixSenderPSK(args.config)
    if args.display_config:
        display_config(sender)
        sys.exit(0)

    if args.input_file:
        send_from_file(sender, args.input_file, args.with_timestamps)
    else:
        if args.key and args.value:
            send_value(sender, args.host, args.key, args.value, args.clock)
        else:
            sys.exit('Invalid arguments: specify either key and value or input file.')


def clock(value: str) -> int:
    """
    Tries to parse clock value from string in multiple formats.

    Supported formats:
    - Bare clock seconds value from unix epoch
    - ISO datetime without timezone
    """
    try:
        return int(value)
    except ValueError:
        return int(datetime.strptime(value, '%Y-%m-%dT%H:%M:%S').timestamp())


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-c', '--config', default=None,
                        help='Path to Zabbix agentd configuration file')
    parser.add_argument('-s', '--host', default=None,
                        help='Specify host name the item belongs to')
    parser.add_argument('-k', '--key',
                        help='Specify item key')
    parser.add_argument('-o', '--value',
                        help='Specify item value')
    parser.add_argument('-t', '--clock', type=clock, default=None,
                        help='Specify item clock')
    parser.add_argument('-i', '--input-file',
                        help='Load values from input file. Specify - for standard input.')
    parser.add_argument('-T', '--with-timestamps', action='store_true',
                        help='Each line of file contains whitespace delimited:\n' \
                             '<host> <key> <timestamp> <value>')
    parser.add_argument('-d', '--display-config', action='store_true',
                        help='Print trapper related Zabbix agent configuration')
    cmd_args = parser.parse_args()

    run_sender(cmd_args)
