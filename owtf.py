#!/usr/bin/env python
"""

owtf is an OWASP+PTES-focused try to unite great tools and facilitate pen testing
Copyright (c) 2011, Abraham Aranguren <name.surname@gmail.com> Twitter: @7a_ http://7-a.org
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.
    * Neither the name of the copyright owner nor the
      names of its contributors may be used to endorse or promote products
      derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

This is the command-line front-end:
In charge of processing arguments and call the framework.

"""

from __future__ import print_function

import argparse
import sys
import os

from framework import core
from framework.lib.general import *
from framework import update


def banner():
    print("""
                  __       ___  
                 /\ \__  /'___\ 
  ___   __  __  _\ \ ,_\/\ \__/ 
 / __`\/\ \/\ \/\ \\ \ \/\ \ ,__\ 
/\ \_\ \ \ \_/ \_/ \\ \ \_\ \ \_/
\ \____/\ \___x___/'\ \__\\\ \_\ 
 \/___/  \/__//__/   \/__/ \/_/ 

    """)


def get_args(core, args):
    valid_plugin_groups = core.DB.Plugin.GetAllGroups()
    valid_plugin_types = core.DB.Plugin.GetAllTypes() + ['all', 'quiet']

    parser = argparse.ArgumentParser(description="OWASP OWTF, the Offensive (Web) Testing Framework, is an OWASP+PTES-focused try to unite great tools and make pentesting more efficient @owtfp http://owtf.org\nAuthor: Abraham Aranguren <name.surname@owasp.org> - http://7-a.org - Twitter: @7a_")
    parser.add_argument("-l", "--list_plugins",
                         dest="ListPlugins",
                         default=None,
                         choices=valid_plugin_groups,
                         help="List available plugins in the plugin group (web, net or aux)")
    parser.add_argument("-f", "--force",
                        dest="ForceOverwrite",
                        action='store_true',
                        help="Force plugin result overwrite (default is avoid overwrite)")
    parser.add_argument("-i", "--interactive",
                        dest="Interactive",
                        default="yes",
                        help="Interactive: yes (default, more control) / no (script-friendly)")
    parser.add_argument("-e", "--except",
                        dest="ExceptPlugins",
                        default=None,
                        help="Comma separated list of plugins to be ignored in the test")
    parser.add_argument("-o", "--only",
                        dest="OnlyPlugins",
                        default=None,
                        help="Comma separated list of the only plugins to be used in the test")
    parser.add_argument("-p", "--inbound_proxy",
                        dest="InboundProxy",
                        default=None,
                        help="(ip:)port - Setup an inbound proxy for manual site analysis")
    parser.add_argument("-x", "--outbound_proxy",
                        dest="OutboundProxy",
                        default=None,
                        help="type://ip:port - Send all OWTF requests using the proxy for the given ip and port. The 'type' can be 'http'(default) or 'socks'")
    parser.add_argument("-xa", "--outbound_proxy_auth",
                        dest="OutboundProxyAuth",
                        default=None,
                        help="username:password - Credentials if any for outbound proxy")
    parser.add_argument("-T", "--tor",
                        dest="TOR_mode",
                        default=None,
                        help="ip:port:tor_control_port:password:IP_renew_time - Sends all OWTF requests through the TOR network. For configuration help run -T help.")
    parser.add_argument("-s", "--simulation",
                        dest="Simulation",
                        action='store_true',
                        help="Do not do anything, simply simulate how plugins would run")
    parser.add_argument("-m", "--custom_profile",
                        dest="CustomProfile",
                        default=None,
                        help="<g:f,w:f,n:f,r:f> - Use my profile: 'f' = valid config file. g: general config, w: web plugin order, n: net plugin order, r: resources file")
    """
    parser.add_argument("-a", "--algorithm",
                        dest="Algorithm",
                        default="breadth", choices=core.Config.Get('ALGORITHMS'),
                        help="<depth/breadth> - Multi-target algorithm: breadth (default)=each plugin runs for all targets first | depth=all plugins run for each target first")
    """
    parser.add_argument("-g", "--plugin_group",
                        dest="PluginGroup",
                        default="web",
                        choices=valid_plugin_groups,
                        help="<web/net/aux> - Initial plugin group: web (default) = targets are interpreted as URLs = web assessment only\nnet = targets are interpreted as hosts/network ranges = traditional network discovery and probing\naux = targets are NOT interpreted, it is up to the plugin/resource definition to decide what to do with the target")
    parser.add_argument("-t", "--plugin_type",
                        dest="PluginType",
                        default="all",
                        choices=valid_plugin_types,
                        help="<plugin type> - For web plugins: passive, semi_passive, quiet (passive + semi_passive), grep, active, all (default)\nNOTE: grep plugins run automatically after semi_passive and active in the default profile")
    parser.add_argument("-port", "--port",
                        dest="RPort",
                        default=None,
                        help="<port> - Port to run probes")
    parser.add_argument("-portwaves", "--portwaves",
                        dest="PortWaves",
                        default="10,100,1000",
                        help="<wave1,wave2,wave3> - Waves to run network scanning")
    parser.add_argument("-proxy", "--proxy",
                        dest="ProxyMode",
                        default=True,
                        action="store_true",
                        help="Use this flag to run OWTF Inbound Proxy")
    parser.add_argument("--update", "--update",
                        dest="Update",
                        action="store_true",
                        help="Use this flag to update OWTF to stable version (not bleeding edge)")
    parser.add_argument('Targets', nargs='*', help='List of Targets')
    return parser.parse_args(args)

def get_args_for_update(args):
    parser = argparse.ArgumentParser(description="OWASP OWTF, the Offensive (Web) Testing Framework, is an OWASP+PTES-focused try to unite great tools and make pentesting more efficient @owtfp http://owtf.org\nAuthor: Abraham Aranguren <name.surname@owasp.org> - http://7-a.org - Twitter: @7a_")
    parser.add_argument("-x", "--outbound_proxy",
                        dest="OutboundProxy",
                        default=None,
                        help="type://ip:port - Send all OWTF requests using the proxy for the given ip and port. The 'type' can be 'http'(default) or 'socks'")
    parser.add_argument("-xa", "--outbound_proxy_auth",
                        dest="OutboundProxyAuth",
                        default=None,
                        help="username:password - Credentials if any for outbound proxy")
    parser.add_argument("--update", "--update",
                        dest="Update",
                        action="store_true",
                        help="Use this flag to update OWTF")
    return parser.parse_args(args)

def usage(error_message):
    """Display the usage message describing how to use owtf."""
    full_path = sys.argv[0].strip()
    main = full_path.split('/')[-1]

    print("Current Path: " + full_path)
    print("Syntax: " + main +
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
    if error_message:
        print("\nERROR: " + error_message)
    exit(-1)


def validate_one_plugin_group(plugin_groups):
    if len(plugin_groups) > 1:
        usage(
            "The plugins specified belong to several Plugin Groups: '" +
            str(plugin_groups) + "'")


def get_plugins_from_arg(core, arg):
    plugins = arg.split(',')
    plugin_groups = core.DB.Plugin.GetGroupsForPlugins(plugins)
    validate_one_plugin_group(plugin_groups)
    return [plugins, plugin_groups]


def process_options(core, user_args):
    try:
        arg = get_args(core, user_args)
    except KeyboardInterrupt: #Exception as e:
        usage("Invalid OWTF option(s) " + e)

    # Default settings:
    profiles = []
    plugin_group = arg.PluginGroup
    if arg.CustomProfile:  # Custom profiles specified
        # Quick pseudo-validation check
        for profile in arg.CustomProfile.split(','):
            chunks = profile.split(':')
            if len(chunks) != 2 or not os.path.exists(chunks[1]):
                usage("Invalid Profile")
            else:  # profile "ok" :)
                profiles.append(chunks)

    if arg.OnlyPlugins:
        arg.OnlyPlugins, plugin_groups = get_plugins_from_arg(
            core,
            arg.OnlyPlugins)
        try:
            # Set Plugin Group according to plugin list specified
            plugin_group = plugin_groups[0]
        except IndexError:
            usage("Please use either OWASP/OWTF codes or Plugin names")
        cprint(
            "Defaulting Plugin Group to '" +
            plugin_group + "' based on list of plugins supplied")

    if arg.ExceptPlugins:
        arg.ExceptPlugins, plugin_groups = get_plugins_from_arg(
            core,
            arg.ExceptPlugins)
        print("ExceptPlugins=" + str(arg.ExceptPlugins))

    if arg.TOR_mode:
        arg.TOR_mode = arg.TOR_mode.split(":")
        print(arg.TOR_mode[0])
        if len(arg.TOR_mode) == 1:
            if arg.TOR_mode[0] != "help":
                usage("Invalid argument for TOR-mode")
        elif len(arg.TOR_mode) != 5:
            usage("Invalid argument for TOR-mode")
        else:
            #Enables OutboundProxy
            if arg.TOR_mode[0] == '':
                outbound_proxy_ip = "127.0.0.1"
            else:
                outbound_proxy_ip = arg.TOR_mode[0]
            if arg.TOR_mode[1] == '':
                outbound_proxy_port = "9050" #default TOR port
            else:
                outbound_proxy_port = arg.TOR_mode[1]
            arg.OutboundProxy = "socks://" + outbound_proxy_ip + ":" + outbound_proxy_port

    if arg.OutboundProxy:
        arg.OutboundProxy = arg.OutboundProxy.split('://')
        if len(arg.OutboundProxy) == 2:
            arg.OutboundProxy = arg.OutboundProxy + arg.OutboundProxy.pop().split(':')
            if arg.OutboundProxy[0] not in ["socks", "http"]:
                usage("Invalid argument for Outbound Proxy")
        else:
            arg.OutboundProxy = arg.OutboundProxy.pop().split(':') 
        if (len(arg.OutboundProxy) not in [2, 3]):  # OutboundProxy should be type://ip:port
            usage("Invalid argument for Outbound Proxy")
        else: # Check if the port is an int
            try:
                int(arg.OutboundProxy[-1])
            except ValueError:
                usage("Invalid port provided for Outbound Proxy")

    if arg.InboundProxy:
        arg.InboundProxy = arg.InboundProxy.split(':')
        # InboundProxy should be (ip:)port:
        if len(arg.InboundProxy) not in [1, 2]:
            usage("Invalid argument for Inbound Proxy")
        else:
            try:
                int(arg.InboundProxy[-1])
            except ValueError:
                usage("Invalid port for Inbound Proxy")


    plugin_types_for_group = core.DB.Plugin.GetTypesForGroup(plugin_group)
    if arg.PluginType == 'all':
        arg.PluginType = plugin_types_for_group
    elif arg.PluginType == 'quiet':
        arg.PluginType = ['passive', 'semi_passive']
        if plugin_group != 'web':
            usage("The quiet plugin type is only for the web plugin group")
    elif arg.PluginType not in plugin_types_for_group:
        usage(
            "Invalid Plugin Type '" + str(arg.PluginType) +
            "' for Plugin Group '" + str(plugin_group) +
            "'. Valid Types: " + ', '.join(plugin_types_for_group))

    scope = arg.Targets or []  # Arguments at the end are the URL target(s)
    num_targets = len(scope)
    if plugin_group != 'aux' and num_targets == 0 and not arg.ListPlugins:
        #usage("") OMG, #TODO: Fix this
        pass
    elif num_targets == 1:  # Check if this is a file
        if os.path.isfile(scope[0]):
            cprint("Scope file: trying to load targets from it ..")
            new_scope = []
            for target in open(scope[0]).read().split("\n"):
                CleanTarget = target.strip()
                if not CleanTarget:
                    continue  # Skip blank lines
                new_scope.append(CleanTarget)
            if len(new_scope) == 0:  # Bad file
                usage("Please provide a scope file (1 target x line)")
            scope = new_scope

    for target in scope:
        if target[0] == "-":
            usage("Invalid Target: " + target)

    args = ''
    if plugin_group == 'aux':
        # For Aux plugins, the Scope are the parameters
        args = scope
        # Aux plugins do not have targets, they have metasploit-like parameters
        scope = ['aux']
    return {'ListPlugins': arg.ListPlugins,
            'Force_Overwrite': arg.ForceOverwrite,
            'Interactive': arg.Interactive == 'yes',
            'Simulation': arg.Simulation,
            'Scope': scope,
            'argv': sys.argv,
            'PluginType': arg.PluginType,
            'OnlyPlugins': arg.OnlyPlugins,
            'ExceptPlugins': arg.ExceptPlugins,
            'InboundProxy': arg.InboundProxy,
            'OutboundProxy': arg.OutboundProxy,
            'OutboundProxyAuth': arg.OutboundProxyAuth,
            'Profiles': profiles,
            #'Algorithm': arg.Algorithm,
            'PluginGroup': plugin_group,
            'RPort': arg.RPort,
            'PortWaves' : arg.PortWaves,
            'ProxyMode': arg.ProxyMode,
            'TOR_mode' : arg.TOR_mode,
            'Args': args}


def run_owtf(core, args):
    try:
        if core.Start(args):
            # Only if Start is for real (i.e. not just listing plugins, etc)
            core.Finish("Complete")  # Not Interrupted or Crashed
    except KeyboardInterrupt:
        # NOTE: The user chose to interact: interactivity check redundant here:
        cprint("\nowtf was aborted by the user:")
        cprint("Please check report/plugin output files for partial results")
        # Interrupted. Must save the DB to disk, finish report, etc
        core.Finish("Aborted by user")
    except SystemExit:
        pass  # Report already saved, framework tries to exit
    finally: # Needed to rename the temp storage dirs to avoid confusion
        core.clean_temp_storage_dirs()

if __name__ == "__main__":
    banner()

    # Get tool path from script path:
    root_dir = os.path.dirname(os.path.abspath(sys.argv[0])) or '.'
    owtf_pid = os.getpid()
    if not "--update" in sys.argv[1:]:
        core = core.Init(root_dir, owtf_pid)  # Initialise Framework
        print(
            "OWTF Version: %s, Release: %s " % (
                core.Config.FrameworkConfigGet('VERSION'),
                core.Config.FrameworkConfigGet('RELEASE')),
            end='\n'*2
            )
        args = process_options(core, sys.argv[1:])
        run_owtf(core, args)
    else:
        # First confirming that --update flag is present in args and then
        # creating a different parser for parsing the args.
        try:
            arg = get_args_for_update(sys.argv[1:])
        except Exception as e:
            usage("Invalid OWTF option(s) " + e)
        # Updater class is imported
        updater = update.Updater(root_dir)
        # If outbound proxy is set, those values are added to Updater Object
        if arg.OutboundProxy:
            if arg.OutboundProxyAuth:
                updater.set_proxy(
                    arg.OutboundProxy,
                    proxy_auth=arg.OutboundProxyAuth)
            else:
                updater.set_proxy(arg.OutboundProxy)
        # Update method called to perform update
        updater.update()
