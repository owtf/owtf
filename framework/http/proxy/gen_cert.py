#!/usr/bin/env python
'''
# Inbound Proxy Module developed by Bharadwaj Machiraju (blog.tunnelshade.in)
#                     as a part of Google Summer of Code 2013
'''
from OpenSSL import crypto
import os
import hashlib
import re
from framework.lib.filelock import FileLock


def gen_signed_cert(domain, ca_crt, ca_key, ca_pass, certs_folder):
    """
    This function takes a domain name as a parameter and then creates a certificate and key with the
    domain name(replacing dots by underscores), finally signing the certificate using specified CA and
    returns the path of key and cert files. If you are yet to generate a CA then check the top comments
    """
    key_path = os.path.join(certs_folder, re.sub('[^-0-9a-zA-Z_]', '_', domain) + ".key")
    cert_path = os.path.join(certs_folder, re.sub('[^-0-9a-zA-Z_]', '_', domain) + ".crt")

    # The first conditions checks if file exists, and does nothing if true
    # If file doenst exist lock is obtained for writing (Other processes in race must wait)
    # After obtaining lock another check to handle race conditions gracefully
    if os.path.exists(key_path) and os.path.exists(cert_path):
        pass
    else:
        with FileLock(cert_path, timeout=2):
            # Check happens if the certificate and key pair already exists for a domain
            if os.path.exists(key_path) and os.path.exists(cert_path):
                pass
            else:
                # Serial Generation - Serial number must be unique for each certificate,
                # so serial is generated based on domain name
                md5_hash = hashlib.md5()
                md5_hash.update(domain)
                serial = int(md5_hash.hexdigest(), 36)

                # The CA stuff is loaded from the same folder as this script
                ca_cert = crypto.load_certificate(crypto.FILETYPE_PEM, open(ca_crt).read())
                # The last parameter is the password for your CA key file
                ca_key = crypto.load_privatekey(crypto.FILETYPE_PEM, open(ca_key).read(), ca_pass)

                key = crypto.PKey()
                key.generate_key(crypto.TYPE_RSA, 2048)

                cert = crypto.X509()
                cert.get_subject().C = "IN"
                cert.get_subject().ST = "AP"
                cert.get_subject().L = "127.0.0.1"
                cert.get_subject().O = "OWTF"
                cert.get_subject().OU = "Inbound-Proxy"
                cert.get_subject().CN = domain
                cert.gmtime_adj_notBefore(0)
                cert.gmtime_adj_notAfter(365 * 24 * 60 * 60)
                cert.set_serial_number(serial)
                cert.set_issuer(ca_cert.get_subject())
                cert.set_pubkey(key)
                cert.sign(ca_key, "sha1")

                # The key and cert files are dumped and their paths are returned
                domain_key = open(key_path, "w")
                domain_key.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, key))

                domain_cert = open(cert_path, "w")
                domain_cert.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
                # print(("[*] Generated signed certificate for %s" % (domain)))
    return key_path, cert_path
