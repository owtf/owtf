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

The Configuration object parses all configuration files, loads them into memory, derives some settings and provides framework modules with a central repository to get info
'''
import sys, os, re, socket
from urlparse import urlparse
from collections import defaultdict
from framework.config import plugin, health_check
from framework.lib.general import *

# Plugin config offsets for info:
PTYPE = 0
PFILE = 1
PTITLE = 2
PCODE = 3
PURL = 4
DEFAULT_PROFILES = { 'g' : 'DEFAULT_GENERAL_PROFILE', 'net' : 'DEFAULT_NET_PLUGIN_ORDER_PROFILE', 'web' : 'DEFAULT_WEB_PLUGIN_ORDER_PROFILE', 'r' : 'DEFAULT_RESOURCES_PROFILE' } 
REPLACEMENT_DELIMITER = "@@@"
REPLACEMENT_DELIMITER_LENGTH = len(REPLACEMENT_DELIMITER)
CONFIG_TYPES = [ 'string', 'other' ]

class Config:
    Target = None
    def __init__(self, RootDir, OwtfPid, CoreObj):
        self.RootDir = RootDir
        self.OwtfPid = OwtfPid
        self.Core = CoreObj
        self.initialize_attributes()
        # Available profiles = g -> General configuration, n -> Network plugin order, w -> Web plugin order, r -> Resources file
        self.LoadConfigFromFile( self.RootDir+'/framework/config/framework_config.cfg' )

    def initialize_attributes(self):
        self.Config = defaultdict(list) # General configuration information
        for Type in CONFIG_TYPES:
            self.Config[Type] = {} # Distinguish strings from everything else in the config = easier + more efficient to replace resources later
        #print str(self.Config)
        self.TargetConfig = {} # General + Target-specific configuration
        self.Targets = [] # List of targets

    def Init(self):
        self.Plugin = plugin.PluginConfig(self.Core)
        self.HealthCheck = health_check.HealthCheck(self.Core)

    def GetTarget(self):
        return self.Target

    def GetTargets(self):
        return self.Targets

    def LoadConfigFromFile(self, ConfigPath): # Load the configuration frominto a global dictionary
        if 'framework_config' not in ConfigPath:
            cprint("Loading Config from: "+ConfigPath+" ..")
        ConfigFile = open(ConfigPath, 'r')
        for line in ConfigFile:
            try:
                Key = line.split(':')[0]
                if Key[0] == '#': # Ignore comment lines
                    continue
                #Value = ''.join(line.split(':')[1:]).strip() <- Removes ":"!!!
                Value = line.replace(Key+": ", "").strip()
                self.Set(Key, MultipleReplace(Value, { '@@@FRAMEWORK_DIR@@@' : self.RootDir, '@@@OWTF_PID@@@' : str(self.OwtfPid) } ))
            except ValueError:
                self.Core.Error.FrameworkAbort("Problem in config file: '"+ConfigPath+"' -> Cannot parse line: "+line)

    def ProcessOptions(self, Options):
        self.Set('FORCE_OVERWRITE', Options['Force_Overwrite']) # True/False
        self.Set('INTERACTIVE', Options['Interactive']) # True/False
        self.Set('SIMULATION', Options['Simulation']) # True/False

        self.Set('PORTWAVES' ,Options['PortWaves'])
        self.LoadPluginTestGroups(Options['PluginGroup'])
        self.LoadProfilesAndSettings(Options)
        # After all initialisations, run health-check:
        self.HealthCheck.run()

    def LoadPluginTestGroups(self, PluginGroup):
        if(PluginGroup == 'web'):
            self.Plugin.LoadWebTestGroupsFromFile()
        elif(PluginGroup == 'net'):
            self.Plugin.LoadNetTestGroupsFromFile()

    def LoadProfilesAndSettings(self, Options):
        self.LoadProfiles(Options['Profiles'])
        self.LoadProxyConfigurations(Options)
        self.DeriveGlobalSettings()
        self.DeriveFromTarget(Options)

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

    def SetTarget(self, Target): # Sets the Target Offset in the configuration, until changed Config.Get will retrieve Target-specific info
        self.Target = Target
        if self.Target not in self.TargetConfig: # Target config not initialised yet
            self.TargetConfig[self.Target] = self.DeepCopy(self.Config) # Clone general info into target-specific config
            self.Targets.append(self.Target)
            #self.TargetConfig[self.Target] = self.Config.deepcopy() # Clone general info into target-specific config
        self.Set('TARGET', Target)
        #print str(self.TargetConfig)

    def DeriveFromTarget(self, Options):
        self.TargetConfig = defaultdict(list) # General + Target-specific configuration
        if Options['PluginGroup'] not in [ 'web', 'aux' ,'net']:
            self.Core.Error.FrameworkAbort("Sorry, not implemented yet!")
        if Options['PluginGroup'] == 'web' or Options['PluginGroup']== 'net': # Target to be interpreted as a URL
            for TargetURL in self.PrepareURLScope(Options['Scope'],Options['PluginGroup']):
                self.SetTarget(TargetURL) # Set the Target URL as the configuration offset, changes will be performed here
                self.DeriveConfigFromURL(TargetURL,Options) # Derive some settings from Target URL and initialise everything
                self.Set('REVIEW_OFFSET', TargetURL)
                # All virtual host URLs to be displayed under ip/port in summary:
                self.Set('SUMMARY_HOST_IP', self.Get('HOST_IP')) 
                self.Set('SUMMARY_PORT_NUMBER', self.Get('PORT_NUMBER')) 
                if Options['PluginGroup'] == 'web':
                    self.Set('REPORT_TYPE', 'URL')
                else:
                    self.Set('REPORT_TYPE', 'NET')
        elif Options['PluginGroup'] == 'aux': # Target to NOT be interpreted as anything
            self.Set('AUX_OUTPUT_PATH', self.Get('OUTPUT_PATH')+"/aux")
            self.Set('HTML_DETAILED_REPORT_PATH', self.Get('OUTPUT_PATH')+"/aux.html") # IMPORTANT: For localStorage to work Url reports must be on the same directory
            self.InitHTTPDBs(self.Get('AUX_OUTPUT_PATH')+"/db/") # Aux modules can make HTTP requests, but these are saved on aux DB
            self.Set('REVIEW_OFFSET', 'AUX')
            self.Set('SUMMARY_HOST_IP', '')
            self.Set('SUMMARY_PORT_NUMBER', '')
            self.Set('REPORT_TYPE', 'AUX')
            self.SetTarget('aux') # No Target for Aux plugins -> They work in a different way. But need target here for conf. to work properly

    def LoadProfiles(self, Profiles):
        self.Profiles = defaultdict(list) # This prevents python from blowing up when the Key does not exist :)
        for Type, Setting in DEFAULT_PROFILES.items():
            self.Profiles[Type] = self.Get(Setting) # First set default files for each profile type
        for Type, File in Profiles: # Now override with User-provided profiles, if present
            self.Profiles[Type] = File
        # Now the self.Profiles contains the right mix of default + user-supplied profiles, parse the profiles
        self.LoadConfigFromFile(self.Profiles['g']) # General config loaded on top of normal config
        self.LoadResourcesFromFile(self.Profiles['r'])
        for PluginGroup in self.Plugin.GetAllGroups():
            if PluginGroup in self.Profiles:
                self.Plugin.LoadPluginOrderFromFile(PluginGroup, self.Profiles[PluginGroup])
            else:
                self.Plugin.LoadPluginOrderFromFileSystem(PluginGroup)

    def LoadResourcesFromFile(self, File): # This needs to be a list instead of a dictionary to preserve order in python < 2.7
        cprint("Loading Resources from: "+File+" ..")
        self.ResourcePath = File
        ConfigFile = open(File, 'r')
        self.Resources = defaultdict(list) # This prevents python from blowing up when the Key does not exist :)
        for line in ConfigFile:
            if '#' == line[0]:
                continue # Skip comment lines
            try:
                Type, Name, Resource = line.split('_____')
            except:
                cprint(self.ResourcePath+" ERROR: The delimiter is incorrect in this line: "+str(line.split('_____')))
                sys.exit(-1)
            self.Resources[Type.upper()].append([ Name, Resource ])

    def IsResourceType(self, ResourceType):
        return ResourceType in self.Resources

    def GetTcpPorts(self,startport,endport):
        PortFile = open(self.Get('TCP_PORT_FILE'), 'r')
        for line in PortFile:
            PortList = line.split(',')
            response = ','.join(PortList[int(startport):int(endport)])
        return response

    def GetUdpPorts(self,startport,endport):
        PortFile = open(self.Get('UDP_PORT_FILE'), 'r')
        for line in PortFile:
            PortList = line.split(',')
            response = ','.join(PortList[int(startport):int(endport)])
        return response

    def GetResources(self, ResourceType): # Transparently replaces the Resources placeholders with the relevant config information
        ReplacedResources = []
        if self.Core.ProxyMode:
            ResourceType += ""#"Proxified"
        ResourceType = ResourceType.upper() # Force upper case to make Resource search not case sensitive
        if self.IsResourceType(ResourceType):
            for Name, Resource in self.Resources[ResourceType]:
                ReplacedResources.append( [ Name, MultipleReplace( Resource, self.GetReplacementDict() ) ] )
        else:
            cprint("The resource type: '"+str(ResourceType)+"' is not defined on '"+self.ResourcePath+"'")
        return ReplacedResources

    def GetResourceList(self, ResourceTypeList):
        ResourceList = []
        for ResourceType in ResourceTypeList:
            #print "ResourceTye="+str(self.GetResources(ResourceType))
            ResourceList = ResourceList + self.GetResources(ResourceType)
        return ResourceList

    def GetRawResources(self, ResourceType):
        return self.Resources[ResourceType]

    def DeriveGlobalSettings(self):
        self.Set('FRAMEWORK_DIR', self.RootDir)
        DBPath = self.Get('OUTPUT_PATH')+"/db/" # Global DB
        self.Set('UNREACHABLE_DB', DBPath+'unreachable.txt') # Stores when and how owtf was run
        self.Set('RUN_DB', DBPath+'runs.txt') # Stores when and how owtf was run
        self.Set('ERROR_DB', DBPath+'errors.txt') # Stores error traces for debugging
        self.Set('SEED_DB', DBPath+'seed.txt') # Stores random seed for testing
        self.Set('SUMMARY_HTMLID_DB', DBPath+'htmlid.txt') # Stores the max html element id to ensure unique ids in forms, etc
        self.Set('DEBUG_DB', DBPath+'debug.txt')
        self.Set('PLUGIN_REPORT_REGISTER', DBPath+"plugin_report_register.txt")
        self.Set('DETAILED_REPORT_REGISTER', DBPath+"detailed_report_register.txt")
        self.Set('COMMAND_REGISTER', DBPath+"command_register.txt")

        self.Set('USER_AGENT_#', self.Get('USER_AGENT').replace(' ', '#')) # User-Agent as shell script-friendly argument! :)
        self.Set('SHORT_USER_AGENT', self.Get('USER_AGENT').split(' ')[0]) # For tools that choke with blank spaces in UA!?
        self.Set('HTML_REPORT_PATH', self.Get('OUTPUT_PATH')+"/"+self.Get('HTML_REPORT'))

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

    def DeriveURLSettings(self, TargetURL,Options):
        #print "self.Target="+self.Target
        self.Set('TARGET_URL', TargetURL) # Set the target in the config
        # TODO: Use urlparse here
        ParsedURL = urlparse(TargetURL)
        URLScheme = Protocol = ParsedURL.scheme
        if ParsedURL.port == None: # Port is blank: Derive from scheme
            if Options['PluginGroup'] == 'net':
                if Options['RPort'] != None:
                    Port = Options['RPort']
                    if Options['OnlyPlugins']!= None:
                        for only_plugin in Options['OnlyPlugins']:
                            service = only_plugin
                            if service =='httprpc':
                                                service = 'http_rpc'
                            self.Set(service.upper()+"_PORT_NUMBER",Port)

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
        self.Set('HOST_PATH',HostPath) # Needed for google resource search
        self.Set('URL_SCHEME', URLScheme) # Some tools need this!
        self.Set('PORT_NUMBER', Port) # Some tools need this!
        self.Set('HOST_NAME', Host) # Set the top URL
        self.Set('HOST_IP', self.GetIPFromHostname(self.Get('HOST_NAME')))
        self.Set('IP_URL', self.Get('TARGET_URL').replace(self.Get('HOST_NAME'), self.Get('HOST_IP')))
        self.Set('TOP_DOMAIN', self.Get('HOST_NAME'))
        HostnameChunks = self.Get('HOST_NAME').split('.')
        if self.IsHostNameNOTIP() and len(HostnameChunks) > 2:
            self.Set('TOP_DOMAIN', '.'.join(HostnameChunks[1:])) #Get "example.com" from "www.example.com"
        self.Set('TOP_URL', Protocol+"://" + Host + ":" + Port) # Set the top URL

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

    def InitHTTPDBs(self, DBPath):
        self.Set('TRANSACTION_LOG_TXT', DBPath+'transaction_log.txt') # Set the Transaction database
        self.Set('TRANSACTION_LOG_HTML', DBPath+'transaction_log.html') 
        self.Set('TRANSACTION_LOG_TRANSACTIONS', DBPath+'transactions/') # directory to store full requests
        self.Set('TRANSACTION_LOG_REQUESTS', DBPath+'transactions/requests/') # directory to store full requests
        self.Set('TRANSACTION_LOG_RESPONSE_HEADERS', DBPath+'transactions/response_headers/') # directory to store full requests
        self.Set('TRANSACTION_LOG_RESPONSE_BODIES', DBPath+'transactions/response_bodies/') # directory to store full requests
        self.Set('TRANSACTION_LOG_FILES', DBPath+'files/') # directory to store downloaded files

        DBPath = DBPath+"db/"
        self.Set('HTMLID_DB', DBPath+'htmlid.txt') # Stores the max html element id to ensure unique ids in forms, etc
        self.Set('ALL_URLS_DB', DBPath+'all_urls.txt') # All URLs in scope without errors
        self.Set('ERROR_URLS_DB', DBPath+'error_urls.txt') # URLs that produce errors (404, etc)
        self.Set('FILE_URLS_DB', DBPath+'file_urls.txt') # URL for files
        self.Set('IMAGE_URLS_DB', DBPath+'image_urls.txt') # URLs for images
        self.Set('FUZZABLE_URLS_DB', DBPath+'fuzzable_urls.txt') # Potentially fuzzable URLs
        self.Set('EXTERNAL_URLS_DB', DBPath+'external_urls.txt') # Out of scope URLs
        self.Set('SSI_URLS_DB', DBPath+'ssi_urls.txt') # SSI  URLs

        self.Set('POTENTIAL_ALL_URLS_DB', DBPath+'potential_urls.txt') # All seen URLs
        # POTENTIAL_ERROR_URLS is never used in the DB but helps simplify the code (vetted urls more similar to potential urls)
        self.Set('POTENTIAL_ERROR_URLS_DB', DBPath+'potential_error_urls.txt') # URLs that produce errors (404, etc) - NOT USED
        self.Set('POTENTIAL_FILE_URLS_DB', DBPath+'potential_file_urls.txt') # URL for files
        self.Set('POTENTIAL_IMAGE_URLS_DB', DBPath+'potential_image_urls.txt') # URLs for images 
        self.Set('POTENTIAL_FUZZABLE_URLS_DB', DBPath+'potential_fuzzable_urls.txt') # Potentially fuzzable URLs
        self.Set('POTENTIAL_EXTERNAL_URLS_DB', DBPath+'potential_external_urls.txt') # Out of scope URLs
        self.Set('POTENTIAL_SSI_URLS_DB', DBPath+'potential_ssi_urls.txt') # SSI URLs

    def DeriveConfigFromURL(self, TargetURL,Options): # Basic configuration tweaks to make things simpler for the plugins
        self.DeriveURLSettings(TargetURL,Options)
        self.DeriveOutputSettingsFromURL(TargetURL)

    def GetFileName(self, Setting, Partial = False):
        Path = self.Get(Setting)
        if Partial:
            return Path.split("/")[-1]
        return Path

    def GetHTMLTransaclog(self, Partial = False):
        return self.GetFileName('TRANSACTION_LOG_HTML', Partial)

    def GetTXTTransaclog(self, Partial = False):
        return self.GetFileName('TRANSACTION_LOG_TXT', Partial)

    def IsHostNameNOTIP(self):
        return self.Get('HOST_NAME') != self.Get('HOST_IP') # Host

    def GetIPFromHostname(self, Hostname):
        IP = ''
        for Socket in [ socket.AF_INET, socket.AF_INET6 ]: # IP validation based on @marcwickenden's pull request, thanks!
            try:
                socket.inet_pton(Socket, Hostname)
                IP = Hostname
                break
            except socket.error: continue
        if not IP:
            try: IP = socket.gethostbyname(Hostname)
            except socket.gaierror: self.Core.Error.FrameworkAbort("Cannot resolve Hostname: "+Hostname)

        ipchunks = IP.strip().split("\n")
        AlternativeIPs = []
        if len(ipchunks) > 1:
            IP = ipchunks[0]
            cprint(Hostname+" has several IP addresses: ("+", ".join(ipchunks)[0:-3]+"). Choosing first: "+IP+"")
            AlternativeIPs = ipchunks[1:]
        self.Set('ALTERNATIVE_IPS', AlternativeIPs)
        IP = IP.strip()
        self.Set('INTERNAL_IP', self.Core.is_ip_internal(IP))
        cprint("The IP address for "+Hostname+" is: '"+IP+"'")
        return IP

    def GetAll(self, Key): # Retrieves a config setting value on all target configurations
        Matches = []
        PreviousTarget = self.Target
        for Target, Config in self.TargetConfig.items():
            self.SetTarget(Target)
            Value = self.Get(Key)
            if Value not in Matches: # Avoid duplicates
                Matches.append(Value)
        self.Target = PreviousTarget
        return Matches

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

    def Get(self, Key): # Transparently gets config info from Target or General
        try:
            Key = self.PadKey(Key)
            return self.GetKeyValue(Key)
        except KeyError:
            Message = "The configuration item: '"+Key+"' does not exist!"
            self.Core.Error.Add(Message)
            raise PluginAbortException(Message) # Raise plugin-level exception to move on to next plugin

    def GetAsPartialPath(self, Key): # Convenience wrapper
        return self.Core.GetPartialPath(self.Get(Key))

    def GetAsList(self, KeyList):
        ValueList = []
        for Key in KeyList:
            ValueList.append(self.Get(Key))
        return ValueList

    def GetHeaderList(self, Key):
        return self.Get(Key).split(',')

    def SetForTarget(self, Type, Key, Value, Target):
        #print str(self.TargetConfig)
        #print "Trying .. self.TargetConfig["+Target+"]["+Key+"] = "+Value+" .."
        self.TargetConfig[Target][Type][Key] = Value

    def SetGeneral(self, Type, Key, Value):
        #print str(self.Config)
        self.Config[Type][Key] = Value

    def Set(self, Key, Value): # Transparently set config items in Target-specific or General config
        Key = REPLACEMENT_DELIMITER+Key+REPLACEMENT_DELIMITER # Store config in "replacement mode", that way we can multiple-replace the config on resources, etc
        Type = 'other'
        if isinstance(Value, str): # Only when value is a string, store in replacements config
            Type = 'string'
        if self.Target == None:
            return self.SetGeneral(Type, Key, Value)
        return self.SetForTarget(Type, Key, Value, self.Target)

    def GetReplacementDict(self):
        return self.GetConfig()['string']

    def __getitem__(self, Key):
        return self.Get(Key)

    def __setitem__(self, Key, Value):
        return self.Set(Key, Value)

    def GetConfig(self):
        if self.Target == None:
            return self.Config
        return self.TargetConfig[self.Target]

    def Show(self):
        cprint("Configuration settings")
        for k, v in self.GetConfig().items():
            cprint(str(k)+" => "+str(v))
