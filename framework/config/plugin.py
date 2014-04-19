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

The random module allows the rest of the framework to have access to random functionality
'''


import os
import base64
from distutils.util import strtobool
from collections import defaultdict

from framework.lib.general import *


PLUGIN_GROUP_FOR_REPORT_TYPE = {'URL': 'web', 'AUX': 'aux', 'NET': 'net'}


class PluginConfig:
    def __init__(self, Core):
        self.Core = Core
        self.AllowedPluginTypes = defaultdict(list)
        self.PluginOrder = defaultdict(list)
        self.LoadFromFileSystem()
        self.LoadWebTestGroupsFromFile() # here???
        self.LoadNetTestGroupsFromFile() # here???

    def GetTypesForGroup(self, PluginGroup):
        PluginTypes = []
        if (self.AllPlugins.has_key(PluginGroup)):
            for PluginType, Plugins in self.AllPlugins[PluginGroup].items():
                PluginTypes.append(PluginType)
            return sorted(PluginTypes) # Return list in alphabetical order
        else:
            cprint("Plugins not found for group: " + PluginGroup)
            return []

    def GetAllTypes(self):
        AllPluginTypes = []
        for PluginGroup, GroupInfo in self.AllPlugins.items():
            AllPluginTypes = AllPluginTypes + self.GetTypesForGroup(PluginGroup)
        return sorted(list(set(AllPluginTypes)))

    def GetGroupsForPlugins(self, PluginList):
        PluginGroups = []
        for PluginGroup, GroupInfo in self.AllPlugins.items():
            for PluginType, Plugins in self.AllPlugins[PluginGroup].items():
                for Plugin in Plugins:
                    if (Plugin['Code'] in PluginList or Plugin['Name'] in PluginList) and PluginGroup not in PluginGroups:
                        PluginGroups.append(PluginGroup)
        return PluginGroups

    def GetAllGroups(self):
        PluginGroups = []
        for PluginGroup, GroupInfo in self.AllPlugins.items():
            PluginGroups.append(PluginGroup)
        return PluginGroups

    def LoadFromFileSystem(self):
        self.AllPlugins = defaultdict(list)
        # This commands finds all the plugins and gets their descriptions in
        # one go.
        PluginFinderCommand = "for i in $(find "+self.Core.Config.Get('PLUGINS_DIR')+" -name '*.py'); do echo \"$i#$(grep ^DESCRIPTION $i|sed 's/ = /=/'|cut -f2 -d=)#$(grep ^USE_INTERNET_RESOURCES $i|sed 's/ = /=/'|cut -f2 -d=)\"; done | sort"
        for line in self.Core.Shell.shell_exec(PluginFinderCommand).split("\n"):
            if not line:
                continue  # Skip blank lines.
            # Remove plugin directory part of the path.
            Plugin = line.strip().replace(self.Core.Config.Get('PLUGINS_DIR'), '')
            PluginFile, PluginDescrip, plugin_internet_res = Plugin.split('#')
            # Use strtobool to convert the switch to a boolean
            try:
                plugin_internet_res = strtobool(plugin_internet_res)
            except ValueError:
                # Whether the string is malformed, whether it is empty.
                # In both cases, the default value is set to False
                plugin_internet_res = False
            PluginDescrip = PluginDescrip[1:-1] # Get rid of surrounding quotes
            PluginChunks = PluginFile.split('/')
            # i.e. all modules have a group. i.e. for web plugins: types are ->
            # passive, semi_passive, active, grep
            if (len(PluginChunks) == 3):
                PluginGroup, PluginType, PluginFile = PluginChunks
            if PluginGroup not in self.AllPlugins:
                self.AllPlugins[PluginGroup] = defaultdict(list)

            PluginName, PluginCode = PluginFile.split('@')
            PluginCode = PluginCode.split('.')[0]  # Get rid of the ".py"
            self.AllPlugins[PluginGroup][PluginType].append({
                'Group': PluginGroup,
                'Type': PluginType,
                'Title': PluginName.title().replace('_', ' '),
                'Name': PluginName,
                'Code': PluginCode,
                'File': PluginFile,
                'Descrip': PluginDescrip,
                'InternetRes': plugin_internet_res,
                # Args to be set on-the-fly by auxiliary plugins.
                'Args': '' })

    def GetPlugins(self, Criteria): # Builds a Plugin list containing all plugins that match the passed criteria
        PluginList = []
        for PluginGroup, GroupInfo in self.AllPlugins.items():
            for PluginType, Plugins in self.AllPlugins[PluginGroup].items():
                for Plugin in Plugins:
                    Match = True
                    for Name, Value in Criteria.items():
                        if Plugin[Name] != Value:
                            Match = False
                    if Match:
                        PluginList.append(Plugin)
        return PluginList

    def GetPlugin(self, Criteria, ShowWarnings = True): # Returns the first Plugin that matches the passed criteria
        Plugins = self.GetPlugins(Criteria)
        if Plugins:
            #print "Plugin found for: "+str(Criteria)
            return Plugins[0]
        if ShowWarnings:
            cprint("WARNING!: No Plugin found for: "+str(Criteria))
        return None

    def GetAll(self, Group, Type = None):
        if Type == None:
            return self.AllPlugins[Group]
        return self.AllPlugins[Group][Type]

    def GetNetTestGroups(self):
        return self.NetTestGroups + self.WebTestGroups

    def LoadNetTestGroupsFromFile(self): # This needs to be a list instead of a dictionary to preserve order in python < 2.7
        self.NetTestGroups = []
        ConfigFile = open(self.Core.Config.Get('NET_TEST_GROUPS'), 'r')
        for line in ConfigFile:
            if '#' == line[0]:
                continue # Skip comments
            try:
                Code, Descrip, Hint, URL = line.strip().split(' | ')
            except ValueError:
                self.Core.Error.FrameworkAbort("Problem in Net Test Groups file: '"+self.Get('NET_TEST_GROUPS')+"' -> Cannot parse line: "+line)
            if len(Descrip) < 2:
                Descrip = Hint
            if len(Hint) < 2:
                Hint = ""
            self.NetTestGroups.append( { 'Code' : Code, 'Descrip' : Descrip, 'Hint' : Hint, 'URL' : URL } )

    def GetWebTestGroups(self):
        return self.WebTestGroups

    def LoadWebTestGroupsFromFile(self): # This needs to be a list instead of a dictionary to preserve order in python < 2.7
        self.WebTestGroups = []
        ConfigFile = open(self.Core.Config.Get('WEB_TEST_GROUPS'), 'r')
        for line in ConfigFile:
            if '#' == line[0]:
                continue # Skip comments
            try:
                Code, Descrip, Hint, URL = line.strip().split(' | ')
            except ValueError:
                self.Core.Error.FrameworkAbort("Problem in Web Test Groups file: '"+self.Get('WEB_TEST_GROUPS')+"' -> Cannot parse line: "+line)
            if len(Descrip) < 2:
                Descrip = Hint
            if len(Hint) < 2:
                Hint = ""
            self.WebTestGroups.append( { 'Code' : Code, 'Descrip' : Descrip, 'Hint' : Hint, 'URL' : URL } )

    def GetWebTestGroupInfoForCode(self, CodeToMatch):
        for Code, Descrip, Hint, URL in self.WebTestGroups:
            if Code == CodeToMatch:
                return [ Descrip, Hint, URL ]
        return None # Not found (should not happen)
        #TODO: Netsec equivalent -> self.NetTestGroups = []
        # MUST LOAD PLUGINS FROM FILE SYSTEM

    def LoadPluginOrderFromFile(self, PluginGroup, File): # This needs to be a list instead of a dictionary to preserve order in python < 2.7
        self.PluginOrder[PluginGroup] = []
        ConfigFile = open(File, 'r')
        cprint("Loading "+PluginGroup+" Plugin Order from: "+File+" ..") # Indicate file being processed so that the user can fix typos, etc
        PluginType = ''
        PreviousStrippedPath = ""
        for line in ConfigFile:
            try:
                line = line.split('#')[0].strip() # Take out comments at the end
                if not line:
                    continue # Skip comment lines
                Path = line.split('___')[0]
                # Plugin group specified, add all of them to order IF previous plugin was not from the same category
                StrippedPath = Path[1:-1] # Take out the "[" and "]"
                PathList = []
                PluginType = ""
                if Path[0] == '[' and StrippedPath in self.AllPlugins[PluginGroup]:
                    if StrippedPath in [ PluginType, PreviousStrippedPath ]: # Plugin Category matches previous category --> Must skip to avoid twice
                        continue # Avoid calling i.e. grep plugins twice or more in a row
                    PathList = []
                    for Plugin in self.GetAll(PluginGroup, StrippedPath):
                        PathList.append( StrippedPath+"/"+Plugin['File'] ) # Category plugins to order (i.e. grep plugins)
                    PreviousStrippedPath = StrippedPath
                else:
                    PathList = [ Path ]
                    PreviousStrippedPath = ""
                for Path in PathList:
                    PluginType, PluginFile = Path.split('/')
                    Plugin = self.GetPlugin( { 'Group' : PluginGroup, 'Type' : PluginType, 'File' : PluginFile } ) # Find this plugin
                    if Plugin: # If Plugin found, append to Plugin order list:
                        self.PluginOrder[PluginGroup].append(Plugin)
            except ValueError as Error:
                print "Error="+str(Error)
                self.Core.Error.FrameworkAbort("Cannot parse file: '"+File+"' -> line -> "+line)

    def LoadPluginOrderFromFileSystem(self, PluginGroup):
        self.PluginOrder[PluginGroup] = self.GetPlugins( { 'Group' : PluginGroup } )
        #print "self.PluginOrder["+PluginGroup+"]="+str(self.PluginOrder[PluginGroup])

    def GetOrder(self, PluginGroup):
        return self.PluginOrder[PluginGroup]

    def GetAllowedTypes(self, PluginGroup):
        return self.AllowedPluginTypes[PluginGroup]

    def DeriveAllowedTypes(self, PluginGroup, PluginTypeFilter):
        if PluginGroup == 'web':
            self.AllowedPluginTypes[PluginGroup] = self.DeriveWebAllowedTypes(PluginGroup, PluginTypeFilter)
        elif PluginGroup == 'net':
            self.AllowedPluginTypes[PluginGroup] = self.DeriveNetAllowedTypes(PluginGroup, PluginTypeFilter)   
            self.AllowedPluginTypes['web'] = self.DeriveWebAllowedTypes('web', {"active"})
        else:
            self.AllowedPluginTypes[PluginGroup] = self.GetTypesForGroup(PluginGroup)

    def DeriveWebAllowedTypes(self, PluginGroup, PluginTypeFilter):
        #print "Deriving Web Allowed Types from PluginGroup="+PluginGroup+", PluginTypeFilter="+str(PluginTypeFilter)
        AllowedPluginTypes = self.GetTypesForGroup(PluginGroup) # Default: All plugins enabled
        PluginTypes = []
        for PluginType in PluginTypeFilter:
            if PluginType == 'quiet':
                #AllowedPluginTypes = [ 'passive', 'semi_passive' ] # Remove active category
                PluginTypes = sorted(PluginTypes + ['passive', 'semi_passive', 'grep'])
            elif PluginType != 'all':
                PluginTypes.append(PluginType)
                if PluginType in [ 'semi_passive', 'active' ]:
                    PluginTypes.append('grep') # grep plugins will be run after semi_passive and active plugins
                #AllowedPluginTypes = [ PluginTypeFilter ]
            elif PluginType == 'all':
                PluginTypes = AllowedPluginTypes
        #print "Derived PluginTypes="+str(PluginTypes)
        if PluginTypes:
            AllowedPluginTypes = sorted(PluginTypes + [ 'external' ])
        return AllowedPluginTypes

    def DeriveNetAllowedTypes(self, PluginGroup, PluginTypeFilter):
        #print "Deriving Net Allowed Types from PluginGroup="+PluginGroup+", PluginTypeFilter="+str(PluginTypeFilter)
        AllowedPluginTypes = self.GetTypesForGroup(PluginGroup) # Default: All plugins enabled
        PluginTypes = []
        for PluginType in PluginTypeFilter:
            if PluginType != 'all':
                PluginTypes.append(PluginType)
            elif PluginType == 'all':
                PluginTypes = AllowedPluginTypes
        #print "Derived AllowedPluginTypes="+str(PluginTypes)
        return PluginTypes
