#!/usr/bin/python
# Version: 1.0
"""
Script for retrieving certificate information items from PEM file.
"""

from __future__ import print_function
from OpenSSL.crypto import load_certificate, FILETYPE_PEM
from datetime import datetime
import argparse
import pem
import sys
import os


def format_x509_name(x509_name):
    """Formats X509Name object into string representation."""
    name = ""
    for c in x509_name.get_components():
        name += '/'
        name += c[0]
        name += '='
        name += c[1]
    return name


def from_asn1_date(asn1date):
    """Converts ASN1 formatted datetime into datetime object.
    """
    return datetime.strptime(asn1date, '%Y%m%d%H%M%SZ')


def get_certificate(file_name, index):
    """Retrieves certificate from PEM file. Returns None if certificate cannot
    be extracted and writes reason to stdout.
    """
    if os.path.isfile(file_name) and os.access(file_name, os.R_OK):
        entries = pem.parse_file(file_name)
        if index >= len(entries):
            print('Requested entry at index', index, 'while file has only',
                  len(entries), 'entries.')
        elif type(entries[index]) == pem.Certificate:
            return load_certificate(FILETYPE_PEM, entries[index].as_bytes())
        else:
            print('Entry at index', index, 'is not a certificate.')
    else:
        print('Unable to read file [' + file_name + '].')


def execute_command(command, cert):
    """Dispatches certificate to command function.
    """
    module = sys.modules[__name__]
    return getattr(module, 'cmd_' + command, None)(cert)


def cmd_status(cert):
    """Returns certificate status based on certificate validity period. Values:
    0 - valid
    1 - not yet valid
    2 - expired
    """
    not_before = from_asn1_date(cert.get_notBefore())
    not_after = from_asn1_date(cert.get_notAfter())
    at = datetime.now()
    if at < not_before:
        return 1
    elif at > not_after:
        return 2
    else:
        return 0


def cmd_startdate(cert):
    """Returns not before date of certificate.
    """
    return from_asn1_date(cert.get_notBefore())


def cmd_enddate(cert):
    """Returns not after date of certificate.
    """
    return from_asn1_date(cert.get_notAfter())


def cmd_serial(cert):
    """Returns serial number of certificate.
    """
    return cert.get_serial_number()


def cmd_subject(cert):
    """Returns subject of certificate.
    """
    return format_x509_name(cert.get_subject())


def cmd_subject_hash(cert):
    """Returns hash of certificate subject.
    """
    return cert.get_subject().hash()


def cmd_issuer(cert):
    """Returns issuer of certificate.
    """
    return format_x509_name(cert.get_issuer())


def cmd_issuer_hash(cert):
    """Returns hash of certificate issuer.
    """
    return cert.get_issuer().hash()


def cmd_fingerprint(cert):
    """Returns SHA-1 fingerprint of certificate.
    """
    return cert.digest('sha1')


def cmd_lifetime(cert):
    """Returns remaining lifetime of certificate in seconds.
    """
    delta = (from_asn1_date(cert.get_notAfter()) - datetime.now())
    return delta.days * 86400 + delta.seconds


def cmd_lifetime_days(cert):
    """Returns remaining lifetime of certificate in full days.
    """
    delta = (from_asn1_date(cert.get_notAfter()) - datetime.now())
    return delta.days


if __name__ == '__main__':
    commands = ['status', 'startdate', 'enddate', 'lifetime', 'lifetime_days',
                'serial', 'subject', 'issuer', 'subject_hash', 'issuer_hash',
                'fingerprint']
    # Define and parse arguments
    parser = argparse.ArgumentParser(
        description='Check certificate in PEM file')
    parser.add_argument('file', nargs='?', help='PEM file')
    parser.add_argument('index', nargs='?', type=int,
                        help='Certificate\'s index in file')
    parser.add_argument('stat', nargs='?', default='status',
                        choices=commands, help='Information to return')
    args = parser.parse_args()

    # Retrieve certificate and execute command function on it
    cert = get_certificate(args.file, args.index)
    if cert is not None:
        print(execute_command(args.stat, cert))
