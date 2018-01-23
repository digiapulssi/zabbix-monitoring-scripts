#!/usr/bin/python
# Version: 1.0
"""
Zabbix discovery for certificates stored in PEM files.
"""

from __future__ import print_function
from OpenSSL.crypto import load_certificate, FILETYPE_PEM
import sys
import pem
import os
import json


class CertEntry():
    """Certificate entry model."""

    def __init__(self, file_name, index, cert):
        self.file_name = file_name
        self.index = index
        self.cert = cert

    def __str__(self):
        return (self.file_name + "[" + str(self.index) + "]:" +
                str(self.cert.get_subject()))


def get_certificates_from_pem(file_name, certificates):
    """Finds all certificate entries from PEM file and adds them to given list.
    """
    entries = pem.parse_file(file_name)
    index = 0
    for entry in entries:
        if type(entry) == pem.Certificate:
            cert = load_certificate(FILETYPE_PEM, entry.as_bytes())
            certificates.append(CertEntry(file_name, index, cert))
        index = index + 1


def format_x509_name(x509_name):
    """Formats X509Name object into string representation."""
    name = ""
    for c in x509_name.get_components():
        name += '/'
        name += c[0]
        name += '='
        name += c[1]
    return name


def get_name_component(x509_name, component):
    """Gets single name component from X509 name."""
    value = ""
    for c in x509_name.get_components():
        if c[0] == component:
            value = c[1]
    return value


def json_output(entries):
    """Outputs list of certificate entries as Zabbix compatible discovery JSON.
    """
    data = []
    output = {
        'data': data
    }
    for entry in entries:
        data.append({
            '{#CRT_FILE}': entry.file_name,
            '{#CRT_INDEX}': entry.index,
            '{#CRT_SUBJECT}': format_x509_name(entry.cert.get_subject()),
            '{#CRT_CN}': get_name_component(entry.cert.get_subject(), 'CN')
        })
    print(json.dumps(output))


def search_certificates(path, entries):
    """Searches certificates from PEM files in given path recursively.
    """
    if os.path.isdir(path) and os.access(path, os.R_OK):
        for child in os.listdir(path):
            search_certificates(os.path.join(path, child), entries)
    elif os.path.isfile(path) and os.access(path, os.R_OK):
        get_certificates_from_pem(path, entries)


if __name__ == '__main__':
    entries = []
    for path in sys.argv[1:]:
        search_certificates(path, entries)

    json_output(entries)
