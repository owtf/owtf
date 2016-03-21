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


def parse_options(cli_options, valid_groups, valid_types):
    parser = argparse.ArgumentParser(
        description="OWASP OWTF, the Offensive (Web) Testing Framework, is " \
                    "an OWASP+PTES-focused try to unite great tools and " \
                    "make pentesting more efficient @owtfp http://owtf.org" \
                    "\nAuthor: Abraham Aranguren <name.surname@owasp.org> - " \
                    "http://7-a.org - Twitter: @7a_")
    parser.add_argument(
        "-l", "--list_plugins",
        dest="list_plugins",
        default=None,
        choices=valid_groups,
        help="List available plugins in the plugin group (web, network or auxiliary)")
    parser.add_argument(
        "-f", "--force",
        dest="ForceOverwrite",
        action='store_true',
        help="Force plugin result overwrite (default is avoid overwrite)")
    parser.add_argument(
        "-i", "--interactive",
        dest="Interactive",
        default="yes",
        help="Interactive: yes (default, more control) / no (script-friendly)")
    parser.add_argument(
        "-e", "--except",
        dest="ExceptPlugins",
        default=None,
        help="Comma separated list of plugins to be ignored in the test")
    parser.add_argument(
        "-o", "--only",
        dest="OnlyPlugins",
        default=None,
        help="Comma separated list of the only plugins to be used in the test")
    parser.add_argument(
        "-p", "--inbound_proxy",
        dest="InboundProxy",
        default=None,
        help="(ip:)port - Setup an inbound proxy for manual site analysis")
    parser.add_argument(
        "-x", "--outbound_proxy",
        dest="OutboundProxy",
        default=None,
        help="type://ip:port - Send all OWTF requests using the proxy " \
             "for the given ip and port. The 'type' can be 'http'(default) " \
             "or 'socks'")
    parser.add_argument(
        "-xa", "--outbound_proxy_auth",
        dest="OutboundProxyAuth",
        default=None,
        help="username:password - Credentials if any for outbound proxy")
    parser.add_argument(
        "-T", "--tor",
        dest="TOR_mode",
        default=None,
        help="ip:port:tor_control_port:password:IP_renew_time - " \
             "Sends all OWTF requests through the TOR network. " \
             "For configuration help run -T help.")
    parser.add_argument(
        "-b", "--botnet-mode",
        dest="Botnet_mode",
        default=None,
        help="miner or list:path_of_list - Sends all OWTF requests " \
             "throw different proxies which can be mined or loaded " \
             "by a list file.")
    parser.add_argument(
        "-s", "--simulation",
        dest="Simulation",
        action='store_true',
        help="Do not do anything, simply simulate how plugins would run")
    parser.add_argument(
        "-m", "--custom_profile",
        dest="CustomProfile",
        default=None,
        help="<g:f,w:f,n:f,r:f,m:f> - Use my profile: 'f' = valid config file. " \
             "g: general config, w: web plugin order, n: network plugin order, " \
             "r: resources file, m: mappings file")
    parser.add_argument(
        "-g", "--plugin_group",
        dest="PluginGroup",
        default=None,
        choices=valid_groups,
        help="<web/network/auxiliary> - Initial plugin group: web (default) = " \
             "targets are interpreted as URLs = web assessment only\n" \
             "network = targets are interpreted as hosts/network ranges = " \
             "traditional network discovery and probing\nauxiliary = targets " \
             "are NOT interpreted, it is up to the plugin/resource " \
             "definition to decide what to do with the target")
    parser.add_argument(
        "-t", "--plugin_type",
        dest="PluginType",
        default="all",
        choices=valid_types,
        help="<plugin type> - For web plugins: passive, semi_passive, " \
             "quiet (passive + semi_passive), grep, active, all (default)\n" \
             "NOTE: grep plugins run automatically after semi_passive and " \
             "active in the default profile")
    parser.add_argument(
        "-port", "--port",
        dest="RPort",
        default=None,
        help="<port> - Port to run probes")
    parser.add_argument(
        "-portwaves", "--portwaves",
        dest="PortWaves",
        default="10,100,1000",
        help="<wave1,wave2,wave3> - Waves to run network scanning")
    parser.add_argument(
        "-proxy", "--proxy",
        dest="ProxyMode",
        default=True,
        action="store_true",
        help="Use this flag to run OWTF Inbound Proxy")
    parser.add_argument(
        "--update", "--update",
        dest="Update",
        action="store_true",
        help="Use this flag to update OWTF to stable version " \
             "(not bleeding edge)")
    parser.add_argument(
        '--nowebui',
        dest='nowebui',
        default=False,
        action='store_true',
        help='Run OWTF without its Web UI.')
    parser.add_argument('Targets', nargs='*', help='List of Targets')
    return parser.parse_args(cli_options)


def parse_update_options(cli_options):
    parser = argparse.ArgumentParser(
        description="OWASP OWTF, the Offensive (Web) Testing Framework, is " \
                    "an OWASP+PTES-focused try to unite great tools and " \
                    "make pentesting more efficient @owtfp http://owtf.org" \
                    "\nAuthor: Abraham Aranguren <name.surname@owasp.org> - " \
                    "http://7-a.org - Twitter: @7a_")
    parser.add_argument(
        "-x", "--outbound_proxy",
        dest="OutboundProxy",
        default=None,
        help="type://ip:port - Send all OWTF requests using the proxy for " \
             "the given ip and port. The 'type' can be 'http'(default) or " \
             "'socks'")
    parser.add_argument(
        "-xa", "--outbound_proxy_auth",
        dest="OutboundProxyAuth",
        default=None,
        help="username:password - Credentials if any for outbound proxy")
    parser.add_argument(
        "--update", "--update",
        dest="Update",
        action="store_true",
        help="Use this flag to update OWTF")
    return parser.parse_args(cli_options)
