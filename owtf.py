#!/usr/bin/env python
'''
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
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

This is the command-line front-end:
In charge of processing arguments and call the framework
'''
from __future__ import print_function

import argparse
import sys
import os

# Get tool path from script path:
RootDir = os.path.dirname(os.path.abspath(sys.argv[0])) or '.'
OwtfPid = os.getpid()

from framework import core
from framework.lib.general import *
from framework import update

def RootUser():
    currentUser = os.getuid() # Obtain user uid
    # On *nix OS uid/gid of root are 0/0
    if currentUser != 0:
        print("You need to be root!")
        sys.exit(1)
        
def Banner():
    print("""
                  __       ___  
                 /\ \__  /'___\ 
  ___   __  __  _\ \ ,_\/\ \__/ 
 / __`\/\ \/\ \/\ \\ \ \/\ \ ,__\ 
/\ \_\ \ \ \_/ \_/ \\ \ \_\ \ \_/
\ \____/\ \___x___/'\ \__\\\ \_\ 
 \/___/  \/__//__/   \/__/ \/_/ 

""")


def GetArgs(Core, args):
    ValidPluginGroups = Core.DB.Plugin.GetAllGroups()
    ValidPluginTypes = Core.DB.Plugin.GetAllTypes() + ['all', 'quiet']

    Parser = argparse.ArgumentParser(description="OWASP OWTF, the Offensive (Web) Testing Framework, is an OWASP+PTES-focused try to unite great tools and make pentesting more efficient @owtfp http://owtf.org\nAuthor: Abraham Aranguren <name.surname@owasp.org> - http://7-a.org - Twitter: @7a_")
    Parser.add_argument("-l", "--list_plugins",
                         dest="ListPlugins",
                         default=None,
                         choices=ValidPluginGroups,
                         help="List available plugins in the plugin group (web, net or aux)")
    Parser.add_argument("-f", "--force",
                        dest="ForceOverwrite",
                        action='store_true',
                        help="Force plugin result overwrite (default is avoid overwrite)")
    Parser.add_argument("-i", "--interactive",
                        dest="Interactive",
                        default="yes",
                        help="Interactive: yes (default, more control) / no (script-friendly)")
    Parser.add_argument("-e", "--except",
                        dest="ExceptPlugins",
                        default=None,
                        help="Comma separated list of plugins to be ignored in the test")
    Parser.add_argument("-o", "--only",
                        dest="OnlyPlugins",
                        default=None,
                        help="Comma separated list of the only plugins to be used in the test")
    Parser.add_argument("-p", "--inbound_proxy",
                        dest="InboundProxy",
                        default=None,
                        help="(ip:)port - Setup an inbound proxy for manual site analysis")
    Parser.add_argument("-x", "--outbound_proxy",
                        dest="OutboundProxy",
                        default=None,
                        help="type://ip:port - Send all OWTF requests using the proxy for the given ip and port. The 'type' can be 'http'(default) or 'socks'")
    Parser.add_argument("-xa", "--outbound_proxy_auth",
                        dest="OutboundProxyAuth",
                        default=None,
                        help="username:password - Credentials if any for outbound proxy")
    Parser.add_argument("-T", "--tor",
                        dest="TOR_mode",
                        default=None,
                        help="ip:port:tor_control_port:password:IP_renew_time - Sends all OWTF requests through the TOR network. For configuration help run -T help.")
    Parser.add_argument("-s", "--simulation",
                        dest="Simulation",
                        action='store_true',
                        help="Do not do anything, simply simulate how plugins would run")
    Parser.add_argument("-m", "--custom_profile",
                        dest="CustomProfile",
                        default=None,
                        help="<g:f,w:f,n:f,r:f> - Use my profile: 'f' = valid config file. g: general config, w: web plugin order, n: net plugin order, r: resources file")
    """
    Parser.add_argument("-a", "--algorithm",
                        dest="Algorithm",
                        default="breadth", choices=Core.Config.Get('ALGORITHMS'),
                        help="<depth/breadth> - Multi-target algorithm: breadth (default)=each plugin runs for all targets first | depth=all plugins run for each target first")
    """
    Parser.add_argument("-g", "--plugin_group",
                        dest="PluginGroup",
                        default="web",
                        choices=ValidPluginGroups,
                        help="<web/net/aux> - Initial plugin group: web (default) = targets are interpreted as URLs = web assessment only\nnet = targets are interpreted as hosts/network ranges = traditional network discovery and probing\naux = targets are NOT interpreted, it is up to the plugin/resource definition to decide what to do with the target")
    Parser.add_argument("-t", "--plugin_type",
                        dest="PluginType",
                        default="all",
                        choices=ValidPluginTypes,
                        help="<plugin type> - For web plugins: passive, semi_passive, quiet (passive + semi_passive), grep, active, all (default)\nNOTE: grep plugins run automatically after semi_passive and active in the default profile")
    Parser.add_argument("-port", "--port",
                        dest="RPort",
                        default=None,
                        help="<port> - Port to run probes")
    Parser.add_argument("-portwaves", "--portwaves",
                        dest="PortWaves",
                        default="10,100,1000",
                        help="<wave1,wave2,wave3> - Waves to run network scanning")
    Parser.add_argument("-proxy", "--proxy",
                        dest="ProxyMode",
                        default=True,
                        action="store_true",
                        help="Use this flag to run OWTF Inbound Proxy")
    Parser.add_argument("--update", "--update",
                        dest="Update",
                        action="store_true",
                        help="Use this flag to update OWTF to stable version (not bleeding edge)")
    Parser.add_argument('Targets', nargs='*', help='List of Targets')

    return Parser.parse_args(args)

def GetArgsForUpdate(args):
    Parser = argparse.ArgumentParser(description="OWASP OWTF, the Offensive (Web) Testing Framework, is an OWASP+PTES-focused try to unite great tools and make pentesting more efficient @owtfp http://owtf.org\nAuthor: Abraham Aranguren <name.surname@owasp.org> - http://7-a.org - Twitter: @7a_")
    Parser.add_argument("-x", "--outbound_proxy",
                        dest="OutboundProxy",
                        default=None,
                        help="type://ip:port - Send all OWTF requests using the proxy for the given ip and port. The 'type' can be 'http'(default) or 'socks'")
    Parser.add_argument("-xa", "--outbound_proxy_auth",
                        dest="OutboundProxyAuth",
                        default=None,
                        help="username:password - Credentials if any for outbound proxy")
    Parser.add_argument("--update", "--update",
                        dest="Update",
                        action="store_true",
                        help="Use this flag to update OWTF")
    return Parser.parse_args(args)

def Usage(error_message):
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


def ValidateOnePluginGroup(PluginGroups):
    if len(PluginGroups) > 1:
        Usage("The plugins specified belong to several Plugin Groups: '" +
              str(PluginGroups) + "'")


def GetPluginsFromArg(Core, Arg):
    Plugins = Arg.split(',')
    PluginGroups = Core.DB.Plugin.GetGroupsForPlugins(Plugins)
    ValidateOnePluginGroup(PluginGroups)
    return [Plugins, PluginGroups]


def ProcessOptions(Core, user_args):
    try:
        Arg = GetArgs(Core, user_args)
    except KeyboardInterrupt: #Exception as e:
        Usage("Invalid OWTF option(s) " + e)

    # Default settings:
    Profiles = []
    PluginGroup = Arg.PluginGroup
    if Arg.CustomProfile:  # Custom profiles specified
        # Quick pseudo-validation check
        for Profile in Arg.CustomProfile.split(','):
            Chunks = Profile.split(':')
            if len(Chunks) != 2 or not os.path.exists(Chunks[1]):
                Usage("Invalid Profile")
            else:  # Profile "ok" :)
                Profiles.append(Chunks)

    if Arg.OnlyPlugins:
        Arg.OnlyPlugins, PluginGroups = GetPluginsFromArg(Core, Arg.OnlyPlugins)
        try:
            # Set Plugin Group according to plugin list specified
            PluginGroup = PluginGroups[0]
        except IndexError:
            Usage("Please use either OWASP/OWTF codes or Plugin names")
        cprint("Defaulting Plugin Group to '" +
                   PluginGroup +
                   "' based on list of plugins supplied")

    if Arg.ExceptPlugins:
        Arg.ExceptPlugins, PluginGroups = GetPluginsFromArg(Core, Arg.ExceptPlugins)
        print("ExceptPlugins=" + str(Arg.ExceptPlugins))

    if Arg.TOR_mode:
        Arg.TOR_mode = Arg.TOR_mode.split(":")
        print(Arg.TOR_mode[0])
        if len(Arg.TOR_mode) == 1:
            if Arg.TOR_mode[0] != "help":
                Usage("Invalid argument for TOR-mode")
        elif len(Arg.TOR_mode) != 5:
            Usage("Invalid argument for TOR-mode")
        else:
            #Enables OutboundProxy
            if Arg.TOR_mode[0] == '':
                outbound_proxy_ip = "127.0.0.1"
            else:
                outbound_proxy_ip = Arg.TOR_mode[0]
            if Arg.TOR_mode[1] == '':
                outbound_proxy_port = "9050" #default TOR port
            else:
                outbound_proxy_port = Arg.TOR_mode[1]
            Arg.OutboundProxy = "socks://" + outbound_proxy_ip + ":" + outbound_proxy_port
    

    if Arg.OutboundProxy:
        Arg.OutboundProxy = Arg.OutboundProxy.split('://')
        if len(Arg.OutboundProxy) == 2:
            Arg.OutboundProxy = Arg.OutboundProxy + Arg.OutboundProxy.pop().split(':')
            if Arg.OutboundProxy[0] not in ["socks", "http"]:
                Usage("Invalid argument for Outbound Proxy")
        else:
            Arg.OutboundProxy = Arg.OutboundProxy.pop().split(':') 
        if (len(Arg.OutboundProxy) not in [2, 3]):  # OutboundProxy should be type://ip:port
            Usage("Invalid argument for Outbound Proxy")
        else: # Check if the port is an int
            try:
                int(Arg.OutboundProxy[-1])
            except ValueError:
                Usage("Invalid port provided for Outbound Proxy")

    if Arg.InboundProxy:
        Arg.InboundProxy = Arg.InboundProxy.split(':')

        # InboundProxy should be (ip:)port:
        if len(Arg.InboundProxy) not in [1, 2]:
            Usage("Invalid argument for Inbound Proxy")
        else:
            try:
                int(Arg.InboundProxy[-1])
            except ValueError:
                Usage("Invalid port for Inbound Proxy")


    PluginTypesForGroup = Core.DB.Plugin.GetTypesForGroup(PluginGroup)
    if Arg.PluginType == 'all':
        Arg.PluginType = PluginTypesForGroup
    elif Arg.PluginType == 'quiet':
        Arg.PluginType = ['passive', 'semi_passive']
        if PluginGroup != 'web':
            Usage("The quiet plugin type is only for the web plugin group")
    elif Arg.PluginType not in PluginTypesForGroup:
        Usage("Invalid Plugin Type '" + str(Arg.PluginType) +
                  "' for Plugin Group '" + str(PluginGroup) +
                  "'. Valid Types: " + ', '.join(PluginTypesForGroup))

    Scope = Arg.Targets or []  # Arguments at the end are the URL target(s)
    NumTargets = len(Scope)
    if PluginGroup != 'aux' and NumTargets == 0 and not Arg.ListPlugins:
        #Usage("") OMG, #TODO: Fix this
        pass
    elif NumTargets == 1:  # Check if this is a file
        if os.path.isfile(Scope[0]):
            cprint("Scope file: trying to load targets from it ..")
            NewScope = []
            for Target in open(Scope[0]).read().split("\n"):
                CleanTarget = Target.strip()
                if not CleanTarget:
                    continue  # Skip blank lines
                NewScope.append(CleanTarget)
            if len(NewScope) == 0:  # Bad file
                Usage("Please provide a scope file (1 target x line)")
            Scope = NewScope

    for Target in Scope:
        if Target[0] == "-":
            Usage("Invalid Target: " + Target)

    Args = ''
    if PluginGroup == 'aux':
        # For Aux plugins, the Scope are the parameters
        Args = Scope
        # Aux plugins do not have targets, they have metasploit-like parameters
        Scope = ['aux']
    return {'ListPlugins': Arg.ListPlugins,
            'Force_Overwrite': Arg.ForceOverwrite,
            'Interactive': Arg.Interactive == 'yes',
            'Simulation': Arg.Simulation,
            'Scope': Scope,
            'argv': sys.argv,
            'PluginType': Arg.PluginType,
            'OnlyPlugins': Arg.OnlyPlugins,
            'ExceptPlugins': Arg.ExceptPlugins,
            'InboundProxy': Arg.InboundProxy,
            'OutboundProxy': Arg.OutboundProxy,
            'OutboundProxyAuth': Arg.OutboundProxyAuth,
            'Profiles': Profiles,
            #'Algorithm': Arg.Algorithm,
            'PluginGroup': PluginGroup,
            'RPort': Arg.RPort,
            'PortWaves' : Arg.PortWaves,
            'ProxyMode': Arg.ProxyMode,
            'TOR_mode' : Arg.TOR_mode,
            'Args': Args}


def run_owtf(Core, args):
    try:
        if Core.Start(args):
            # Only if Start is for real (i.e. not just listing plugins, etc)
            Core.Finish("Complete")  # Not Interrupted or Crashed
    except KeyboardInterrupt:
        # NOTE: The user chose to interact: interactivity check redundant here:
        cprint("\nowtf was aborted by the user:")
        cprint("Please check report/plugin output files for partial results")
        # Interrupted. Must save the DB to disk, finish report, etc
        Core.Finish("Aborted by user")
    except SystemExit:
        pass  # Report already saved, framework tries to exit
    #except:
    #    Core.Error.Add("Unknown owtf error")
        # Interrupted. Must save the DB to disk, finish report, etc
    #    Core.Finish("Crashed")
    finally: # Needed to rename the temp storage dirs to avoid confusion
        Core.CleanTempStorageDirs(Core.Config.OwtfPid)

if __name__ == "__main__":
    RootUser()
    Banner()
    if not "--update" in sys.argv[1:]:
        Core = core.Init(RootDir, OwtfPid)  # Initialise Framework
        print(
            "OWTF Version: %s, Release: %s " %
            (Core.Config.FrameworkConfigGet('VERSION'), Core.Config.FrameworkConfigGet('RELEASE')),
            end='\n'*2
            )
        args = ProcessOptions(Core, sys.argv[1:])
        run_owtf(Core, args)
    else:
        # First confirming that --update flag is present in args and then
        # creating a different parser for parsing the args.
        try:
            Arg = GetArgsForUpdate(sys.argv[1:])
        except Exception as e:
            Usage("Invalid OWTF option(s) " + e)
        # Updater class is imported
        UpdaterObj = update.Updater(RootDir)
        # If outbound proxy is set, those values are added to Updater Object
        if Arg.OutboundProxy:
            if Arg.OutboundProxyAuth:
                UpdaterObj.set_proxy(Arg.OutboundProxy, proxy_auth=Arg.OutboundProxyAuth)
            else:
                UpdaterObj.set_proxy(Arg.OutboundProxy)
        # Update method called to perform update
        UpdaterObj.update()
