from __future__ import print_function
import sys
import argparse


def usage(error_message):
    """Display the usage message describing how to use owtf."""
    full_path = sys.argv[0].strip()
    main = full_path.split('/')[-1]

    print("Current Path: " + full_path)
    print(
        "Syntax: " + main +
        " [ options ] <target1 target2 target3 ..> where target can be:"
        " <target URL / hostname / IP>"
        )
    print(
        "                    NOTE:"
        " targets can also be provided via a text file",
        end='\n'*3
        )
    print("Examples:", end='\n'*2)
    print(
        "Run all web plugins:                         " + main +
        " http://my.website.com"
        )
    print(
        "Run only passive + semi_passive plugins:             " + main +
        " -t quiet http://my.website.com"
        )
    print(
        "Run only active plugins:                     " + main +
        " -t active http://my.website.com"
        )
    print()
    print(
        "Run all plugins except 'OWASP-CM-001: Testing_for_SSL-TLS': " + main +
        " -e 'OWASP-CM-001' http://my.website.com"
        )
    print(
        "Run all plugins except 'OWASP-CM-001: Testing_for_SSL-TLS': " + main +
        " -e 'Testing_for_SSL-TLS' http://my.website.com"
        )
    print()
    print(
        "Run only 'OWASP-CM-001: Testing_for_SSL-TLS':             " + main +
        " -o 'OWASP-CM-001' http://my.website.com"
        )
    print(
        "Run only 'OWASP-CM-001: Testing_for_SSL-TLS':             " + main +
        " -o 'Testing_for_SSL-TLS' http://my.website.com"
        )
    print()
    print(
        "Run only OWASP-IG-005 and OWASP-WU-VULN:             " + main +
        " -o 'OWASP-IG-005,OWASP-WU-VULN' http://my.website.com"
        )
    print(
        "Run using my resources file and proxy:             " + main +
        " -m r:/home/me/owtf_resources.cfg"
        " -x 127.0.0.1:8080 http://my.website.com"
        )
    print()
    print(
        "Run using TOR network:                    " + main +
        " -o OWTF-WVS-001 http://my.website.com"
        " --tor 127.0.0.1:9050:9051:password:1"
        )
    print()
    print(
        "Run Botnet-mode using miner:                    " + main +
        " -o OWTF-WVS-001 http://my.website.com -b miner"
        )
    print()
    print(
        "Run Botnet-mode using custom proxy list:                  " + main +
        " -o OWTF-WVS-001 http://my.website.com -b list:proxy_list_path.txt"
        )
    if error_message:
        print("\nERROR: " + error_message)
    exit(-1)
