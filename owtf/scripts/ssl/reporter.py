#!/usr/bin/env python

from __future__ import print_function

import json
import os
import sys
import traceback

from template import RESULTS
from owtf.utils.file import FileOperations


if not os.path.isfile(sys.argv[1]):
    sys.exit(1)

data = None
try:
    data = FileOperations.open(json.loads(str(sys.argv[1])))
except Exception:
    sys.exit(1)

if data is None:
    sys.exit(1)

org_name = str(sys.argv[1]).split(".json", 1)[0]
try:
    if data[0]["status"] == "ERROR":
        print("[-] SSLLabs scan finished with errors")
        sys.exit(0)
except IndexError:
    print("Wrong format detected, exiting...")
    sys.exit(0)

print("RESULT IN SSL_TLS_TESTING_FUNCTIONALITY_FROM_SSLLABS_REPORT.html")

try:
    with open(org_name + "_report.html", "w") as f:
        content = RESULTS
        content = content.replace("{{host}}", data[0]["host"])
        content = content.replace("{{status_code}}", str(data[0]["endpoints"][0]["details"]["httpStatusCode"]))
        content = content.replace("{{ip_address}}", data[0]["endpoints"][0]["ipAddress"])
        content = content.replace("{{grade}}", data[0]["endpoints"][0]["grade"])
        content = content.replace("{{secondary_grade}}", data[0]["endpoints"][0]["gradeTrustIgnored"])
        content = content.replace("{{freak}}", str(data[0]["endpoints"][0]["details"]["freak"]))
        content = content.replace("{{poodle}}", str(data[0]["endpoints"][0]["details"]["poodleTls"]))

        insecureRenegotiationSuported = "true" if data[0]["endpoints"][0]["details"]["renegSupport"] == 1 else "false"
        content = content.replace("{{insecure_reneg}}", insecureRenegotiationSuported)

        content = content.replace("{{openssl_ccs}}", str(data[0]["endpoints"][0]["details"]["openSslCcs"]))

        if "dhUsesKnownPrimes" in data[0]["endpoints"][0]["details"]:
            insecureDH = "true" if data[0]["endpoints"][0]["details"]["dhUsesKnownPrimes"] == 2 else "false"
        content = content.replace("{{insecure_dh}}", insecureDH)

        protocol_str = ""
        for protocol in data[0]["endpoints"][0]["details"]["protocols"]:
            protocol_str += "<h2> Protocol SSL/TLS version supported : </h2>" + protocol["name"] + "  " + protocol[
                "version"
            ]
        content = content.replace("{{protocol}}", protocol_str)

        certificate_exp = "true" if data[0]["endpoints"][0]["details"]["chain"]["issues"] == 2 else "false"
        content = content.replace("{{cert_exp}}", certificate_exp)

        selfSigned = "true" if data[0]["endpoints"][0]["details"]["cert"]["issues"] == 64 else "false"
        content = content.replace("{{self_signed}}", selfSigned)

        content = content.replace("{{rc4}}", str(data[0]["endpoints"][0]["details"]["supportsRc4"]))
        content = content.replace("{{fwd_sec}}", str(data[0]["endpoints"][0]["details"]["forwardSecrecy"]))

        secureRenegotiationSuported = "true" if data[0]["endpoints"][0]["details"]["renegSupport"] == 2 else "false"
        content = content.replace("{{sec_reneg}}", secureRenegotiationSuported)

        cert_chains = ""
        for chainCert in data[0]["endpoints"][0]["details"]["chain"]["certs"]:
            cert_chains += "<h2> Chain Cert issue: </h2>" + str(
                chainCert["issues"]
            ) + "(1:certificate not yet valid,2:certificate expired,4:weak key,8:weak signature,16:blacklisted)"
            weakKey = "true" if chainCert["issues"] == 4 else "false"
            weakSignature = "true" if chainCert["issues"] == 8 else "false"
            cert_chains += "<h2> Weak private key: </h2>" + weakKey
            cert_chains += "<h2> Weak certificate: </h2>" + weakSignature
        content = content.replace("{{cert_chains}}", cert_chains)

        f.write(content)
        print("Done. Report write successful.")
except:
    print("Something went wrong when parsing result")
    print(traceback.format_exc())
    sys.exit(0)

sys.exit(0)
