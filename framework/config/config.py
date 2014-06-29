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

The Configuration object parses all configuration files, loads them into
memory, derives some settings and provides framework modules with a central
repository to get info.

"""

import os
import re
import socket

from urlparse import urlparse
from collections import defaultdict

from framework.lib.exceptions import PluginAbortException, \
                                     DBIntegrityException
from framework.config import plugin, health_check
from framework.lib.general import cprint
from framework.db import models, target_manager


REPLACEMENT_DELIMITER = "@@@"
REPLACEMENT_DELIMITER_LENGTH = len(REPLACEMENT_DELIMITER)
CONFIG_TYPES = [ 'string', 'other' ]


class Config(object):
    Target = None
    def __init__(self, RootDir, OwtfPid, CoreObj):
        self.RootDir = RootDir
        self.OwtfPid = OwtfPid
        self.Core = CoreObj
        self.initialize_attributes()
        self.SearchRegex = re.compile(REPLACEMENT_DELIMITER + '([A-Z0-9-_]*?)' + REPLACEMENT_DELIMITER)  # key can consist alphabets, numbers, hyphen & underscore
        # Available profiles = g -> General configuration, n -> Network plugin order, w -> Web plugin order, r -> Resources file
        self.LoadFrameworkConfigFromFile( self.RootDir+'/framework/config/framework_config.cfg' )

    def initialize_attributes(self):
        self.Config = defaultdict(list) # General configuration information
        for Type in CONFIG_TYPES:
            self.Config[Type] = {}

    def Init(self):
        self.HealthCheck = health_check.HealthCheck(self.Core)

    def LoadFrameworkConfigFromFile(self, ConfigPath): # Load the configuration frominto a global dictionary
        if 'framework_config' not in ConfigPath:
            cprint("Loading Config from: "+ConfigPath+" ..")
        ConfigFile = self.Core.open(ConfigPath, 'r')
        self.Set('FRAMEWORK_DIR', self.RootDir) # Needed Later
        for line in ConfigFile:
            try:
                Key = line.split(':')[0]
                if Key[0] == '#': # Ignore comment lines
                    continue
                #Value = ''.join(line.split(':')[1:]).strip() <- Removes ":"!!!
                Value = line.replace(Key+": ", "").strip()
                self.Set(Key, self.MultipleReplace(Value, { 'FRAMEWORK_DIR' : self.RootDir, 'OWTF_PID' : str(self.OwtfPid) } ))
            except ValueError:
                self.Core.Error.FrameworkAbort("Problem in config file: '"+ConfigPath+"' -> Cannot parse line: "+line)

    def ConvertStrToBool(self, string):
        return(not(string in ['False', 'false', 0, '0']))

    def ProcessOptions(self, Options):
        self.LoadProfiles(Options['Profiles'])
        self.LoadTargets(Options)
        # After all initialisations, run health-check:
        # self.HealthCheck.run() Please fix it. Health check should check db health etc..

    def LoadProfiles(self, Profiles):
        self.Profiles = defaultdict(list) # This prevents python from blowing up when the Key does not exist :)
        for Type, File in Profiles: # Now override with User-provided profiles, if present
            self.Profiles[Type] = File

    def LoadTargets(self, Options):
        # print(Options)
        Scope = self.PrepareURLScope(Options['Scope'], Options['PluginGroup'])
        for Target in Scope:
            try:
                self.Core.DB.Target.AddTarget(Target)
            except DBIntegrityException:
                cprint(Target + " already exists in DB")

    def PrepareURLScope(self, Scope,Group): # Convert all targets to URLs
        NewScope = []
        for TargetURL in Scope:
            if TargetURL[-1] == "/":
                TargetURL = TargetURL[0:-1]
            if TargetURL[0:4] != 'http':
                # Add both "http" and "https" if not present:
                # the connection check will then remove from the report if one does not exist
                if Group == "net":
                                    NewScope.append('http://' + TargetURL)
                else:
                    for Prefix in [ 'http', 'https' ]:
                        NewScope.append( Prefix+'://'+TargetURL )
            else:
                NewScope.append(TargetURL) # Append "as-is"
        return NewScope

    def MultipleReplace(self, Text, ReplaceDict):
        NewText = Text
        for key in self.SearchRegex.findall(NewText):
            if ReplaceDict.get(key, None):  # Check if key exists in the replace dict ;)
                # A recursive call to remove all level occurences of place holders
                NewText = NewText.replace(REPLACEMENT_DELIMITER + key + REPLACEMENT_DELIMITER, self.MultipleReplace(ReplaceDict[key], ReplaceDict))
        return NewText

    def LoadProxyConfigurations(self, Options):
        if Options['InboundProxy']:
            if len(Options['InboundProxy']) == 1:
                Options['InboundProxy'] = [self.Get('INBOUND_PROXY_IP'), Options['InboundProxy'][0]]
        else:
            Options['InboundProxy'] = [self.Get('INBOUND_PROXY_IP'), self.Get('INBOUND_PROXY_PORT')]
        self.Set('INBOUND_PROXY_IP', Options['InboundProxy'][0])
        self.Set('INBOUND_PROXY_PORT', Options['InboundProxy'][1])
        self.Set('INBOUND_PROXY', ':'.join(Options['InboundProxy']))
        self.Set('PROXY', ':'.join(Options['InboundProxy']))

    def DeepCopy(self, Config): # function to perform a "deep" copy of the config Obj passed
        Copy = defaultdict(list)
        for Key, Value in Config.items():
            Copy[Key] = Value.copy()
        return Copy

    def GetResources(self, ResourceType, Target=None): # Transparently replaces the Resources placeholders with the relevant config information
        return self.Core.DB.Resource.GetResources(ResourceType)

    def GetResourceList(self, ResourceTypeList):
        return self.Core.DB.Resource.GetResourceList(ResourceTypeList)

    def GetRawResources(self, ResourceType):
        return self.Resources[ResourceType]

    def DeriveConfigFromURL(self, TargetURL): #,Options):
        target_config = dict(target_manager.TARGET_CONFIG)
        target_config['TARGET_URL'] = TargetURL # Set the target in the config
        # TODO: Use urlparse here
        ParsedURL = urlparse(TargetURL)
        URLScheme = Protocol = ParsedURL.scheme
        if ParsedURL.port == None: # Port is blank: Derive from scheme
            """
            if Options['PluginGroup'] == 'net':
                if Options['RPort'] != None:
                    Port = Options['RPort']
                    if Options['OnlyPlugins']!= None:
                        for only_plugin in Options['OnlyPlugins']:
                            service = only_plugin
                            if service =='httprpc':
                                                service = 'http_rpc'
                            self.Set(service.upper()+"_PORT_NUMBER",Port)
            """
            Port = '80'
            if 'https' == URLScheme:
                Port = '443'
        else: # Port found by urlparse:
            Port = str(ParsedURL.port)
        #\print "Port=" + Port
        Host = ParsedURL.hostname
        HostPath = ParsedURL.hostname + ParsedURL.path
        #protocol, crap, host = TargetURL.split('/')[0:3]
        #DotChunks = TargetURL.split(':')
        #URLScheme = DotChunks[0]
        #Port = '80'
        #if len(DotChunks) == 2: # Case: http://myhost.com -> Derive port from http / https
        #   if 'https' == URLScheme:
        #       Port = '443'
        #else: # Derive port from ":xyz" URL part
        #   Port = DotChunks[2].split('/')[0]
        target_config['HOST_PATH'] = HostPath # Needed for google resource search
        target_config['URL_SCHEME'] = URLScheme # Some tools need this!
        target_config['PORT_NUMBER'] = Port # Some tools need this!
        target_config['HOST_NAME'] = Host # Set the top URL

        HostIP = self.GetIPFromHostname(Host)
        HostIPs = self.GetIPsFromHostname(Host)
        target_config['HOST_IP'] = HostIP
        target_config['ALTERNATIVE_IPS'] = HostIPs

        IPURL = target_config['TARGET_URL'].replace(Host, HostIP) 
        target_config['IP_URL'] = IPURL
        target_config['TOP_DOMAIN'] = target_config['HOST_NAME']

        HostnameChunks = target_config['HOST_NAME'].split('.')
        if self.IsHostNameNOTIP(Host, HostIP) and len(HostnameChunks) > 2:
            target_config['TOP_DOMAIN'] = '.'.join(HostnameChunks[1:]) #Get "example.com" from "www.example.com"
        target_config['TOP_URL'] = Protocol+"://" + Host + ":" + Port # Set the top URL
        return target_config

    def DeriveOutputSettingsFromURL(self, TargetURL):
        self.Set('HOST_OUTPUT', self.Get('OUTPUT_PATH')+"/"+self.Get('HOST_IP')) # Set the output directory
        self.Set('PORT_OUTPUT', self.Get('HOST_OUTPUT')+"/"+self.Get('PORT_NUMBER')) # Set the output directory
        URLInfoID = TargetURL.replace('/','_').replace(':','')
        self.Set('URL_OUTPUT', self.Get('PORT_OUTPUT')+"/"+URLInfoID+"/") # Set the URL output directory (plugins will save their data here)
        self.Set('PARTIAL_URL_OUTPUT_PATH', self.Get('URL_OUTPUT')+'partial') # Set the partial results path
        self.Set('PARTIAL_REPORT_REGISTER', self.Get('PARTIAL_URL_OUTPUT_PATH')+"/partial_report_register.txt")

        # Tested in FF 8: Different directory = Different localStorage!! -> All localStorage-dependent reports must be on the same directory
        self.Set('HTML_DETAILED_REPORT_PATH', self.Get('OUTPUT_PATH')+"/"+URLInfoID+".html") # IMPORTANT: For localStorage to work Url reports must be on the same directory
        self.Set('URL_REPORT_LINK_PATH', self.Get('OUTPUT_PATH')+"/index.html") # IMPORTANT: For localStorage to work Url reports must be on the same directory

        if not self.Get('SIMULATION'):
            self.Core.CreateMissingDirs(self.Get('HOST_OUTPUT'))

        # URL Analysis DBs
        # URL DBs: Distintion between vetted, confirmed-to-exist, in transaction DB URLs and potential URLs
        self.InitHTTPDBs(self.Get('URL_OUTPUT'))

    def DeriveDBPathsFromURL(self, TargetURL):
        targets_folder = os.path.expanduser(self.Get('TARGETS_DB_FOLDER'))
        url_info_id = TargetURL.replace('/','_').replace(':','')
        transaction_db_path = os.path.join(targets_folder, url_info_id, "transactions.db")
        url_db_path = os.path.join(targets_folder, url_info_id, "urls.db")
        plugins_db_path = os.path.join(targets_folder, url_info_id, "plugins.db")
        return [transaction_db_path, url_db_path, plugins_db_path]

    #def DeriveConfigFromURL(self, TargetURL,Options): # Basic configuration tweaks to make things simpler for the plugins
    #    self.DeriveURLSettings(TargetURL,Options)
    #    self.DeriveOutputSettingsFromURL(TargetURL)

    def GetFileName(self, Setting, Partial = False):
        Path = self.Get(Setting)
        if Partial:
            return Path.split("/")[-1]
        return Path

    def GetHTMLTransaclog(self, Partial = False):
        return self.GetFileName('TRANSACTION_LOG_HTML', Partial)

    def GetTXTTransaclog(self, Partial = False):
        return self.GetFileName('TRANSACTION_LOG_TXT', Partial)

    def IsHostNameNOTIP(self, host_name, host_ip):
        return host_name != host_ip # Host

    def GetIPFromHostname(self, Hostname):
        IP = ''
        for Socket in [ socket.AF_INET, socket.AF_INET6 ]: # IP validation based on @marcwickenden's pull request, thanks!
            try:
                socket.inet_pton(Socket, Hostname)
                IP = Hostname
                break
            except socket.error:
                continue
        if not IP:
            try:
                IP = socket.gethostbyname(Hostname)
            except socket.gaierror:
                self.Core.Error.FrameworkAbort("Cannot resolve Hostname: "+Hostname)

        ipchunks = IP.strip().split("\n")
        AlternativeIPs = []
        if len(ipchunks) > 1:
            IP = ipchunks[0]
            cprint(Hostname+" has several IP addresses: ("+", ".join(ipchunks)[0:-3]+"). Choosing first: "+IP+"")
            AlternativeIPs = ipchunks[1:]
        self.Set('ALTERNATIVE_IPS', AlternativeIPs)
        IP = IP.strip()
        self.Set('INTERNAL_IP', self.Core.IsIPInternal(IP))
        cprint("The IP address for "+Hostname+" is: '"+IP+"'")
        return IP

    def GetIPsFromHostname(self, Hostname):
        IP = ''
        for Socket in [ socket.AF_INET, socket.AF_INET6 ]: # IP validation based on @marcwickenden's pull request, thanks!
            try:
                socket.inet_pton(Socket, Hostname)
                IP = Hostname
                break
            except socket.error:
                continue
        if not IP:
            try:
                IP = socket.gethostbyname(Hostname)
            except socket.gaierror:
                self.Core.Error.FrameworkAbort("Cannot resolve Hostname: "+Hostname)

        ipchunks = IP.strip().split("\n")
        #AlternativeIPs = []
        #if len(ipchunks) > 1:
        #    IP = ipchunks[0]
        #    cprint(Hostname+" has several IP addresses: ("+", ".join(ipchunks)[0:-3]+"). Choosing first: "+IP+"")
        #    AlternativeIPs = ipchunks[1:]
        #self.Set('ALTERNATIVE_IPS', AlternativeIPs)
        #IP = IP.strip()
        #self.Set('INTERNAL_IP', self.Core.IsIPInternal(IP))
        #cprint("The IP address for "+Hostname+" is: '"+IP+"'")
        return ipchunks

    def IsSet(self, Key):
        Key = self.PadKey(Key)
        Config = self.GetConfig()
        for Type in CONFIG_TYPES:
            if Key in Config[Type]:
                return True
        return False

    def GetKeyValue(self, Key):
        Config = self.GetConfig() # Gets the right config for target / general
        for Type in CONFIG_TYPES:
            if Key in Config[Type]:
                return Config[Type][Key]

    def PadKey(self, Key):
        return REPLACEMENT_DELIMITER+Key+REPLACEMENT_DELIMITER # Add delimiters

    def StripKey(self, Key):
        return Key.replace(REPLACEMENT_DELIMITER, '')

    def FrameworkConfigGet(self, Key): # Transparently gets config info from Target or General
        try:
            Key = self.PadKey(Key)
            return self.GetKeyValue(Key)
        except KeyError:
            Message = "The configuration item: '"+Key+"' does not exist!"
            self.Core.Error.Add(Message)
            raise PluginAbortException(Message) # Raise plugin-level exception to move on to next plugin

    def FrameworkConfigGetDBPath(self, Key):
        # Only for main/common dbs, for target specific dbs, there are other methods
        relative_path = self.FrameworkConfigGet(Key)
        return os.path.join(self.FrameworkConfigGet("OUTPUT_PATH"), self.FrameworkConfigGet("DB_DIR"), relative_path)

    def GetAsPartialPath(self, Key): # Convenience wrapper
        return self.Core.GetPartialPath(self.Get(Key))

    def GetAsList(self, KeyList):
        ValueList = []
        for Key in KeyList:
            ValueList.append(self.FrameworkConfigGet(Key))
        return ValueList

    def GetHeaderList(self, Key):
        return self.FrameworkConfigGet(Key).split(',')

    def SetGeneral(self, Type, Key, Value):
        #print str(self.Config)
        self.Config[Type][Key] = Value

    def Set(self, Key, Value): # Transparently set config items in Target-specific or General config
        Key = REPLACEMENT_DELIMITER+Key+REPLACEMENT_DELIMITER # Store config in "replacement mode", that way we can multiple-replace the config on resources, etc
        Type = 'other'
        if isinstance(Value, str): # Only when value is a string, store in replacements config
            Type = 'string'
        return self.SetGeneral(Type, Key, Value)

    def GetFrameworkConfigDict(self):
        return self.GetConfig()['string']

    def GetReplacementDict(self):
        return({"FRAMEWORK_DIR":self.RootDir})

    def __getitem__(self, Key):
        return self.Get(Key)

    def __setitem__(self, Key, Value):
        return self.Set(Key, Value)

    def GetConfig(self):
        return self.Config

    def Show(self):
        cprint("Configuration settings")
        for k, v in self.GetConfig().items():
            cprint(str(k)+" => "+str(v))

    def GetOutputDirForTargets(self):
        return os.path.join(self.FrameworkConfigGet("OUTPUT_PATH"), self.FrameworkConfigGet("TARGETS_DIR"))

    def CleanUpForTarget(self, TargetURL):
        return self.Core.rmtree(self.GetOutputDirForTarget(TargetURL))

    def GetOutputDirForTarget(self, TargetURL):
        return os.path.join(self.GetOutputDirForTargets(), TargetURL.replace("/","_").replace(":",""))

    def CreateOutputDirForTarget(self, TargetURL):
        self.Core.CreateMissingDirs(self.GetOutputDirForTarget(TargetURL))

    def GetTransactionDBPathForTarget(self, TargetURL):
        return os.path.join(self.GetOutputDirForTarget(TargetURL), self.FrameworkConfigGet("TRANSACTION_DB_NAME"))

    def GetUrlDBPathForTarget(self, TargetURL):
        return os.path.join(self.GetOutputDirForTarget(TargetURL), self.FrameworkConfigGet("URL_DB_NAME"))

    def GetOutputDBPathForTarget(self, TargetURL):
        return os.path.join(self.GetOutputDirForTarget(TargetURL), self.FrameworkConfigGet("OUTPUT_DB_NAME"))
