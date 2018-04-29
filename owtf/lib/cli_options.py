"""
owtf.lib.cli_options
~~~~~~~~~~~~~~~~~~~~

Main CLI processing machine
"""
from __future__ import print_function

import argparse
import sys


def usage(error_message):
    """Display the usage message describing how to use owtf.

    :param error_message: Error message to display
    :type error_message: `str`
    :return: None
    :rtype: None
    """
    full_path = sys.argv[0].strip()
    main = full_path.split("/")[-1]

    print("Current Path: {}".format(full_path))
    print(
        "Syntax: {}"
        " [ options ] <target1 target2 target3 ..> where target can be:"
        " <target URL / hostname / IP>".format(main)
    )
    print("                    NOTE:" " targets can also be provided via a text file", end="\n" * 3)
    print("Examples: ", end="\n" * 2)
    print("Run all web plugins:                         {}" " http://my.website.com".format(main))
    print("Run only passive + semi_passive plugins:             {}" " -t quiet http://my.website.com".format(main))
    print("Run only active plugins:                     {}" " -t active http://my.website.com".format(main))
    print()
    print(
        "Run all plugins except 'OWASP-CM-001: Testing_for_SSL-TLS': {}"
        " -e 'OWASP-CM-001' http://my.website.com".format(main)
    )
    print(
        "Run all plugins except 'OWASP-CM-001: Testing_for_SSL-TLS': {}"
        " -e 'Testing_for_SSL-TLS' http://my.website.com".format(main)
    )
    print()
    print(
        "Run only 'OWASP-CM-001: Testing_for_SSL-TLS':             {}"
        " -o 'OWASP-CM-001' http://my.website.com".format(main)
    )
    print(
        "Run only 'OWASP-CM-001: Testing_for_SSL-TLS':             {}"
        " -o 'Testing_for_SSL-TLS' http://my.website.com".format(main)
    )
    print()
    print(
        "Run only OWASP-IG-005 and OWASP-WU-VULN:             {}"
        " -o 'OWASP-IG-005,OWASP-WU-VULN' http://my.website.com".format(main)
    )
    print(
        "Run using my resources file and proxy:             {}"
        " -m r:/home/me/owtf_resources.cfg"
        " -x 127.0.0.1:8080 http://my.website.com".format(main)
    )
    print()
    print(
        "Run using TOR network:                    {}"
        " -o OWTF-WVS-001 http://my.website.com"
        " --tor 127.0.0.1:9050:9051:password:1".format(main)
    )
    if error_message:
        print("\nERROR: {}".format(error_message))
    from owtf.core import finish

    finish()


def parse_options(cli_options, valid_groups, valid_types):
    """Main arguments processing for the CLI

    :param cli_options: CLI args Supplied by user
    :type cli_options: `dict`
    :param valid_groups: Plugin groups to chose from
    :type valid_groups: `list`
    :param valid_types: Plugin types to chose from
    :type valid_types: `list`
    :return:
    :rtype:
    """
    parser = argparse.ArgumentParser(
        prog="owtf",
        description="OWASP OWTF, the Offensive (Web) Testing Framework, is "
        "an OWASP+PTES-focused try to unite great tools and "
        "make pentesting more efficient @owtfp http://owtf.org"
        "\nAuthor: Abraham Aranguren <name.surname@owasp.org> - "
        "http://7-a.org - Twitter: @7a_",
    )
    parser.add_argument(
        "-l",
        "--list-plugins",
        dest="list_plugins",
        default=None,
        choices=valid_groups,
        help="List available plugins in the plugin group (web, network or auxiliary)",
    )
    parser.add_argument(
        "-f",
        "--force",
        dest="force_overwrite",
        action="store_true",
        help="Force plugin result overwrite (default is avoid overwrite)",
    )
    parser.add_argument(
        "-i",
        "--interactive",
        dest="interactive",
        default="yes",
        help="interactive: yes (default, more control) / no (script-friendly)",
    )
    parser.add_argument(
        "-e",
        "--except",
        dest="except_plugins",
        default=None,
        help="Comma separated list of plugins to be ignored in the test",
    )
    parser.add_argument(
        "-o",
        "--only",
        dest="only_plugins",
        default=None,
        help="Comma separated list of the only plugins to be used in the test",
    )
    parser.add_argument(
        "-p",
        "--inbound-proxy",
        dest="inbound_proxy",
        default=None,
        help="(ip:)port - Setup an inbound proxy for manual site analysis",
    )
    parser.add_argument(
        "-x",
        "--outbound-proxy",
        dest="outbound_proxy",
        default=None,
        help="type://ip:port - Send all OWTF requests using the proxy "
        "for the given ip and port. The 'type' can be 'http'(default) "
        "or 'socks'",
    )
    parser.add_argument(
        "-xa",
        "--outbound-proxy-auth",
        dest="outbound_proxy_auth",
        default=None,
        help="username:password - Credentials if any for outbound proxy",
    )
    parser.add_argument(
        "-T",
        "--tor",
        dest="tor_mode",
        default=None,
        help="ip:port:tor_control_port:password:IP_renew_time - "
        "Sends all OWTF requests through the TOR network. "
        "For configuration help run -T help.",
    )
    parser.add_argument(
        "-s",
        "--simulation",
        dest="Simulation",
        action="store_true",
        help="Do not do anything, simply simulate how plugins would run",
    )
    parser.add_argument(
        "-g",
        "--plugin-group",
        dest="plugin_group",
        default=None,
        choices=valid_groups,
        help="<web/network/auxiliary> - Initial plugin group: web (default) = "
        "targets are interpreted as URLs = web assessment only\n"
        "network = targets are interpreted as hosts/network ranges = "
        "traditional network discovery and probing\nauxiliary = targets "
        "are NOT interpreted, it is up to the plugin/resource "
        "definition to decide what to do with the target",
    )
    parser.add_argument(
        "-t",
        "--plugin-type",
        dest="plugin_type",
        default="all",
        choices=valid_types,
        help="<plugin type> - For web plugins: passive, semi_passive, "
        "quiet (passive + semi_passive), grep, active, all (default)\n"
        "NOTE: grep plugins run automatically after semi_passive and "
        "active in the default profile",
    )
    parser.add_argument("-port", "--port", dest="rport", default=None, help="<port> - Port to run probes")
    parser.add_argument(
        "-portwaves",
        "--portwaves",
        dest="port_waves",
        default="10,100,1000",
        help="<wave1,wave2,wave3> - Waves to run network scanning",
    )
    parser.add_argument(
        "-proxy",
        "--proxy",
        dest="proxy_mode",
        default=True,
        action="store_true",
        help="Use this flag to run OWTF Inbound Proxy",
    )
    parser.add_argument(
        "--nowebui", dest="nowebui", default=False, action="store_true", help="Run OWTF without its Web UI."
    )
    parser.add_argument("targets", nargs="*", help="List of targets")
    return parser.parse_args(cli_options)
