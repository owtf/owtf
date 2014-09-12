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

The PluginHandler is in charge of running all plugins taking into account the
chosen settings.
"""

import os
import sys
import imp
import time
import json
import fcntl
import curses
import select
import signal
import logging
import termios
import multiprocessing

from threading import Thread
from collections import defaultdict
from ptp import PTP
from ptp.libptp.exceptions import PTPError
from framework.dependency_management.dependency_resolver import BaseComponent

from framework.lib.exceptions import FrameworkAbortException, \
    PluginAbortException, \
    UnreachableTargetException
from framework.lib.general import *
from framework.plugin.scanner import Scanner


INTRO_BANNER_GENERAL = """
Short Intro:
Current Plugin Groups:
- web: For web assessments or when net plugins find a port that "speaks HTTP"
- net: For network assessments, discovery and port probing
- aux: Auxiliary plugins, to automate miscelaneous tasks
"""

INTRO_BANNER_WEB_PLUGIN_TYPE = """
WEB Plugin Types:
- Passive Plugins: NO requests sent to target
- Semi Passive Plugins: SOME "normal/legitimate" requests sent to target
- Active Plugins: A LOT OF "bad" requests sent to target (You better have permission!)
- Grep Plugins: NO requests sent to target. 100% based on transaction searches and plugin output parsing. Automatically run after semi_passive and active in default profile.
"""


class PluginHandler(BaseComponent):
    PluginCount = 0

    COMPONENT_NAME = "plugin_handler"

    def __init__(self, CoreObj, Options):
        self.register_in_service_locator()
        self.Core = CoreObj
        self.config = self.Core.Config
        self.plugin_output = self.Core.DB.POutput
        self.db_plugin = self.Core.DB.Plugin
        self.target = self.Core.DB.Target
        self.transaction = self.Core.DB.Transaction
        self.error_handler = self.Core.Error
        self.reporter = self.Core.Reporter
        self.timer = self.Core.Timer
        # This should be dynamic from filesystem:
        #self.PluginGroups = [ 'web', 'net', 'aux' ]
        #self.PluginTypes = [ 'passive', 'semi_passive', 'active', 'grep' ]
        #self.AllowedPluginTypes = self.GetAllowedPluginTypes(Options['PluginType'].split(','))
        #self.Simulation, self.Scope, self.PluginGroup, self.Algorithm, self.ListPlugins = [ Options['Simulation'], Options['Scope'], Options['PluginGroup'], Options['Algorithm'], Options['ListPlugins'] ]
        self.Simulation, self.Scope, self.PluginGroup, self.ListPlugins = [Options['Simulation'], Options['Scope'],
                                                                           Options['PluginGroup'],
                                                                           Options['ListPlugins']]
        self.OnlyPluginsList = self.ValidateAndFormatPluginList(Options['OnlyPlugins'])
        self.ExceptPluginsList = self.ValidateAndFormatPluginList(Options['ExceptPlugins'])
        #print "OnlyPlugins="+str(self.OnlyPluginsList)
        #print "ExceptPlugins="+str(self.ExceptPluginsList)
        #print "Options['PluginType']="+str(Options['PluginType'])
        if isinstance(Options['PluginType'],
                      str):  # For special plugin types like "quiet" -> "semi_passive" + "passive"
            Options['PluginType'] = Options['PluginType'].split(',')
        self.AllowedPlugins = self.db_plugin.GetPluginsByGroupType(self.PluginGroup, Options['PluginType'])
        self.OnlyPluginsSet = len(self.OnlyPluginsList) > 0
        self.ExceptPluginsSet = len(self.ExceptPluginsList) > 0
        self.scanner = Scanner(self.Core)
        self.InitExecutionRegistry()
        self.showOutput = True

    def ValidateAndFormatPluginList(self, PluginList):
        List = []  # Ensure there is always a list to iterate from! :)
        if PluginList != None:
            List = PluginList

        ValidatedList = []
        # print "List to validate="+str(List)
        for Item in List:
            Found = False
            for Plugin in self.db_plugin.GetPluginsByGroup(self.PluginGroup):  # Processing Loop
                if Item in [Plugin['code'], Plugin['name']]:
                    ValidatedList.append(Plugin['code'])
                    Found = True
                    break
            if not Found:
                cprint(
                    "ERROR: The code '" + Item + "' is not a valid plugin, please use the -l option to see available plugin names and codes")
                exit()
        return ValidatedList  # Return list of Codes

    def InitExecutionRegistry(
            self):  # Initialises the Execution registry: As plugins execute they will be tracked here, useful to avoid calling plugins stupidly :)
        self.ExecutionRegistry = defaultdict(list)
        for Target in self.Scope:
            self.ExecutionRegistry[Target] = []

    def GetLastPluginExecution(self, Plugin):
        ExecLog = self.ExecutionRegistry[
            self.config.GetTarget()]  # Get shorcut to relevant execution log for this target for readability below :)
        NumItems = len(ExecLog)
        # print "NumItems="+str(NumItems)
        if NumItems == 0:
            return -1  # List is empty
        #print "NumItems="+str(NumItems)
        #print str(ExecLog)
        #print str(range((NumItems -1), 0))
        for Index in range((NumItems - 1), -1, -1):
            #print "Index="+str(Index)
            #print str(ExecLog[Index])
            Match = True
            for Key, Value in ExecLog[
                Index].items():  # Compare all execution log values against the passed Plugin, if all match, return index to log record
                if not Key in Plugin or Plugin[Key] != Value:
                    Match = False
            if Match:
                #print str(PluginIprint "you have etered " + cnfo)+" was found!"
                return Index
        return -1

    def PluginAlreadyRun(self, PluginInfo):
        # if self.Simulation:
        #        return self.HasPluginExecuted(PluginInfo)
        #SaveDir = self.GetPluginOutputDir(PluginInfo)
        #if not self.exists(SaveDir): # At least one directory is missing
        #        return False # This is the first time the plugin is going to run (i.e. some directory was missing)
        #return True # The path already exists, therefore the plugin has been run before
        if self.plugin_output.PluginAlreadyRun(PluginInfo):
            return (True)
        return (False)

    def GetExecLogSinceLastExecution(self,
                                     Plugin):  # Get all execution entries from log since last time the passed plugin executed
        return self.ExecutionRegistry[self.config.GetTarget()][self.GetLastPluginExecution(Plugin):]

    def NormalRequestsAllowed(self):
        # AllowedPluginTypes = self.config.GetAllowedPluginTypes('web')
        #GetAllowedPluginTypes('web')
        AllowedPluginTypes = self.config.Plugin.GetAllowedTypes('web')
        return 'semi_passive' in AllowedPluginTypes or 'active' in AllowedPluginTypes

    def RequestsPossible(self):
        # Even passive plugins will make requests to external resources
        # return [ 'grep' ] != self.config.GetAllowedPluginTypes('web')
        return ['grep'] != self.db_plugin.GetTypesForGroup('web')

    def DumpOutputFile(self, Filename, Contents, Plugin, RelativePath=False):
        SaveDir = self.GetPluginOutputDir(Plugin)
        abs_path = self.Core.DumpFile(Filename, Contents, SaveDir)
        if RelativePath:
            return (os.path.relpath(abs_path, self.config.GetOutputDirForTargets()))
        return (abs_path)

    def RetrieveAbsPath(self, RelativePath):
        return (os.path.join(self.config.GetOutputDirForTargets(), RelativePath))

    def GetPluginOutputDir(self, Plugin):  # Organise results by OWASP Test type and then active, passive, semi_passive
        # print "Plugin="+str(Plugin)+", Partial url ..="+str(self.config.Get('PARTIAL_URL_OUTPUT_PATH'))+", TARGET="+self.config.Get('TARGET')
        if ((Plugin['group'] == 'web') or (Plugin['group'] == 'net')):
            return os.path.join(self.target.GetPath('PARTIAL_URL_OUTPUT_PATH'),
                                WipeBadCharsForFilename(Plugin['title']), Plugin['type'])
        elif Plugin['group'] == 'aux':
            return os.path.join(self.config.Get('AUX_OUTPUT_PATH'), WipeBadCharsForFilename(Plugin['title']),
                                Plugin['type'])

    def exists(self, directory):
        return os.path.exists(directory)

    def GetModule(self, ModuleName, ModuleFile,
                  ModulePath):  # Python fiddling to load a module from a file, there is probably a better way...
        f, Filename, desc = imp.find_module(ModuleFile.split('.')[0],
                                            [ModulePath])  # ModulePath = os.path.abspath(ModuleFile)
        return imp.load_module(ModuleName, f, Filename, desc)

    def IsChosenPlugin(self, Plugin):
        Chosen = True
        if Plugin['group'] == self.PluginGroup:
            if self.OnlyPluginsSet and Plugin['code'] not in self.OnlyPluginsList:
                Chosen = False  # Skip plugins not present in the white-list defined by the user
            if self.ExceptPluginsSet and Plugin['code'] in self.ExceptPluginsList:
                Chosen = False  # Skip plugins present in the black-list defined by the user
        if Plugin['type'] not in self.db_plugin.GetTypesForGroup(Plugin['group']):
            Chosen = False  # Skip plugin: Not matching selected type
        return Chosen

    def IsActiveTestingPossible(self):  # Checks if 1 active plugin is enabled = active testing possible:
        Possible = False
        # for PluginType, PluginFile, Title, Code, ReferenceURL in self.config.GetPlugins(): # Processing Loop
        #for PluginType, PluginFile, Title, Code in self.config.Plugin.GetOrder(self.PluginGroup):
        for Plugin in self.config.Plugin.GetOrder(self.PluginGroup):
            if self.IsChosenPlugin(Plugin) and Plugin['type'] == 'active':
                Possible = True
                break
        return Possible

    def force_overwrite(self):
        # return self.config.Get('FORCE_OVERWRITE')
        return False

    def CanPluginRun(self, Plugin, ShowMessages=False):
        # if self.Core.IsTargetUnreachable():
        #        return False # Cannot run plugin if target is unreachable
        if not self.IsChosenPlugin(Plugin):
            return False  # Skip not chosen plugins
        # Grep plugins to be always run and overwritten (they run once after semi_passive and then again after active):
        #if self.PluginAlreadyRun(Plugin) and not self.config.Get('FORCE_OVERWRITE'): #not Code == 'OWASP-WU-SPID': # For external plugin forced re-run (development)
        if self.PluginAlreadyRun(Plugin) and ((not self.force_overwrite() and not ('grep' == Plugin['type'])) or Plugin[
            'type'] == 'external'):  #not Code == 'OWASP-WU-SPID':
            if ShowMessages:
                logging.info(
                    "Plugin: " + Plugin['title'] + " (" + Plugin['type'] + ") has already been run, skipping ..")
            #if Plugin['Type'] == 'external':
            # External plugins are run only once per each run, so they are registered for all targets
            # that are targets in that run. This is an alternative to chaning the js filters etc..
            #        self.register_plugin_for_all_targets(Plugin)
            return False
        if 'grep' == Plugin['type'] and self.PluginAlreadyRun(Plugin):
            return False  # Grep plugins can only run if some active or semi_passive plugin was run since the last time
        return True

    def GetPluginFullPath(self, PluginDir, Plugin):
        return PluginDir + "/" + Plugin['type'] + "/" + Plugin['file']  # Path to run the plugin

    def RunPlugin(self, PluginDir, Plugin, save_output=True):
        PluginPath = self.GetPluginFullPath(PluginDir, Plugin)
        (Path, Name) = os.path.split(PluginPath)
        # (Name, Ext) = os.path.splitext(Name)
        #self.Core.DB.Debug.Add("Running Plugin -> Plugin="+str(Plugin)+", PluginDir="+str(PluginDir))
        PluginOutput = self.GetModule("", Name, Path + "/").run(self.Core, Plugin)
        #if save_output:
        #print(PluginOutput)
        #self.SavePluginInfo(PluginOutput, Plugin) # Timer retrieved here
        return PluginOutput


    @staticmethod
    def rank_plugin(output, pathname):
        """Rank the current plugin results using PTP.

        Returns the ranking value.

        """

        def extract_metasploit_modules(cmd):
            """Extract the metasploit modules contained in the plugin output.

            Returns the list of (module name, output file) found, an empty list
            otherwise.

            """
            return [
                (
                    output['output'].get('ModifiedCommand', '').split(' ')[3],
                    os.path.basename(
                        output['output'].get('RelativeFilePath', ''))
                )
                for output in cmd
                if ('output' in output and
                    'metasploit' in output['output'].get('ModifiedCommand', ''))]

        msf_modules = extract_metasploit_modules(output)
        owtf_rank = -1  # Default ranking value set to Unknown.
        try:
            parser = PTP()
            if msf_modules:
                for module in msf_modules:
                    parser.parse(
                        pathname=pathname,
                        filename=module[1],  # Path to output file.
                        plugin=module[0])  # Metasploit module name.
                    owtf_rank = max(
                        owtf_rank,
                        parser.get_highest_ranking())
            else:
                parser.parse(pathname=pathname)
                owtf_rank = parser.get_highest_ranking()
        except PTPError:  # Not supported tool or report not found.
            pass
        return owtf_rank


    def ProcessPlugin(self, plugin_dir, plugin, status={}):
        # Save how long it takes for the plugin to run.
        self.timer.StartTimer('Plugin')
        plugin['start'] = self.timer.GetStartDateTimeAsStr(
            'Plugin')
        # Use relative path from targets folders while saving
        plugin['output_path'] = os.path.relpath(self.GetPluginOutputDir(plugin),
                                                self.config.GetOutputDirForTargets())
        if not self.CanPluginRun(plugin, True):
            return None  # Skip.
        status['AllSkipped'] = False  # A plugin is going to be run.
        plugin['status'] = 'Running'
        self.PluginCount += 1
        logging.info(
            '_' * 10 + ' ' + str(self.PluginCount) +
            ' - Target: ' + self.target.GetTargetURL() +
            ' -> Plugin: ' + plugin['title'] + ' (' +
            plugin['type'] + ') ' + '_' * 10)
        # self.LogPluginExecution(Plugin)
        # Skip processing in simulation mode, but show until line above
        # to illustrate what will run
        if self.Simulation:
            return None
        # DB empty => grep plugins will fail, skip!!
        if ('grep' == plugin['type'] and
                    self.transaction.NumTransactions() == 0):
            logging.info(
                'Skipped - Cannot run grep plugins: '
                'The Transaction DB is empty')
            return None
        try:
            output = self.RunPlugin(plugin_dir, plugin)
            plugin['status'] = 'Successful'
            plugin['end'] = self.timer.GetEndDateTimeAsStr(
                'Plugin')
            owtf_rank = self.rank_plugin(
                output,
                self.GetPluginOutputDir(plugin))
            status['SomeSuccessful'] = True
            self.plugin_output.SavePluginOutput(
                plugin,
                output,
                self.timer.GetElapsedTimeAsStr('Plugin'),
                owtf_rank=owtf_rank)
            return output
        except KeyboardInterrupt:
            # Just explain why crashed.
            plugin['status'] = 'Aborted'
            plugin['end'] = self.timer.GetEndDateTimeAsStr(
                'Plugin')
            self.plugin_output.SavePartialPluginOutput(
                plugin,
                [],
                'Aborted by User',
                self.timer.GetElapsedTimeAsStr('Plugin'))
            self.error_handler.UserAbort('Plugin')
            status['SomeAborted (Keyboard Interrupt)'] = True
        except SystemExit:
            # Abort plugin processing and get out to external exception
            # handling, information saved elsewhere.
            raise SystemExit
        except PluginAbortException, PartialOutput:
            plugin['status'] = 'Aborted (by user)'
            plugin['end'] = self.timer.GetEndDateTimeAsStr(
                'Plugin')
            self.plugin_output.SavePartialPluginOutput(
                plugin,
                PartialOutput.parameter,
                'Aborted by User',
                self.timer.GetElapsedTimeAsStr('Plugin'))
            status['SomeAborted'] = True
        except UnreachableTargetException, PartialOutput:
            plugin['status'] = 'Unreachable Target'
            plugin['end'] = self.timer.GetEndDateTimeAsStr(
                'Plugin')
            self.plugin_output.SavePartialPluginOutput(
                plugin,
                PartialOutput.parameter,
                'Unreachable Target',
                self.timer.GetElapsedTimeAsStr('Plugin'))
            status['SomeAborted'] = True
        except FrameworkAbortException, PartialOutput:
            plugin['status'] = 'Aborted (Framework Exit)'
            plugin['end'] = self.timer.GetEndDateTimeAsStr(
                'Plugin')
            self.plugin_output.SavePartialPluginOutput(
                plugin,
                PartialOutput.parameter,
                'Framework Aborted',
                self.timer.GetElapsedTimeAsStr('Plugin'))
            self.Core.Finish("Aborted")
            #TODO: Handle this gracefully
            #except: # BUG
            #        Plugin["status"] = "Crashed"
            #        cprint("Crashed")
            #self.SavePluginInfo(self.error_handler.Add("Plugin "+Plugin['Type']+"/"+Plugin['File']+" failed for target "+self.config.Get('TARGET')), Plugin) # Try to save something
            #TODO: http://blog.tplus1.com/index.php/2007/09/28/the-python-logging-module-is-much-better-than-print-statements/

    def ProcessPlugins(self):
        status = {
            'SomeAborted': False,
            'SomeSuccessful': False,
            'AllSkipped': True}
        if self.PluginGroup in ['web', 'aux', 'net']:
            self.ProcessPluginsForTargetList(
                self.PluginGroup,
                status,
                self.target.GetAll("ID"))
        return status

    def GetPluginGroupDir(self, PluginGroup):
        PluginDir = self.config.FrameworkConfigGet('PLUGINS_DIR') + PluginGroup
        return PluginDir

    def SwitchToTarget(self, Target):
        self.target.SetTarget(Target)  # Tell Target DB that all Gets/Sets are now Target-specific

    def get_plugins_in_order_for_PluginGroup(self, PluginGroup):
        return self.config.Plugin.GetOrder(PluginGroup)

    def get_plugins_in_order(self, PluginGroup):
        return self.config.Plugin.GetOrder(PluginGroup)

    def ProcessPluginsForTargetList(self, PluginGroup, Status,
                                    TargetList):  # TargetList param will be useful for netsec stuff to call this
        PluginDir = self.GetPluginGroupDir(PluginGroup)
        if PluginGroup == 'net':
            portwaves = self.config.Get('PORTWAVES')
            waves = portwaves.split(',')
            waves.append('-1')
            lastwave = 0
            for Target in TargetList:  # For each Target
                self.scanner.scan_network(Target)
                # Scanning and processing the first part of the ports
                for i in range(1):
                    ports = self.config.GetTcpPorts(lastwave, waves[i])
                    print "probing for ports" + str(ports)
                    http = self.scanner.probe_network(Target, 'tcp', ports)
                    # Tell Config that all Gets/Sets are now
                    # Target-specific.
                    self.SwitchToTarget(Target)
                    for Plugin in self.get_plugins_in_order_for_PluginGroup(PluginGroup):
                        self.ProcessPlugin(PluginDir, Plugin, Status)
                    lastwave = waves[i]
                    for http_ports in http:
                        if http_ports == '443':
                            self.ProcessPluginsForTargetList(
                                'web', {
                                    'SomeAborted': False,
                                    'SomeSuccessful': False,
                                    'AllSkipped': True},
                                {'https://' + Target.split('//')[1]}
                            )
                        else:
                            self.ProcessPluginsForTargetList(
                                'web', {
                                    'SomeAborted': False,
                                    'SomeSuccessful': False,
                                    'AllSkipped': True},
                                {Target}
                            )
        else:
            pass
            # self.WorkerManager.startinput()
            #self.WorkerManager.fillWorkList(PluginGroup,TargetList)
            #self.WorkerManager.spawn_workers()
            #self.WorkerManager.manage_workers()
            #self.WorkerManager.poisonPillToWorkers()
            #Status = self.WorkerManager.joinWorker()
            #if 'breadth' == self.Algorithm: # Loop plugins, then targets
            #       for Plugin in self.config.Plugin.GetOrder(PluginGroup):# For each Plugin
            #               #print "Processing Plugin="+str(Plugin)
            #               for Target in TargetList: # For each Target
            #                       #print "Processing Target="+str(Target)
            #                       self.SwitchToTarget(Target) # Tell Config that all Gets/Sets are now Target-specific
            #                       self.ProcessPlugin( PluginDir, Plugin, Status )
            #elif 'depth' == self.Algorithm: # Loop Targets, then plugins
            #       for Target in TargetList: # For each Target
            #               self.SwitchToTarget(Target) # Tell Config that all Gets/Sets are now Target-specific
            #               for Plugin in self.config.Plugin.GetOrder(PluginGroup):# For each Plugin
            #                       self.ProcessPlugin( PluginDir, Plugin, Status )

    def CleanUp(self):
        self.WorkerManager.clean_up()

    def SavePluginInfo(self, PluginOutput, Plugin):
        self.Core.DB.SaveDBs()  # Save new URLs to DB after each request
        self.reporter.SavePluginReport(PluginOutput, Plugin)  # Timer retrieved by Reporter

    def ShowPluginList(self):
        if self.ListPlugins == 'web':
            self.ShowWebPluginsBanner()
        elif self.ListPlugins == 'aux':
            self.ShowAuxPluginsBanner()
        self.ShowPluginGroupPlugins(self.ListPlugins)

    def ShowAuxPluginsBanner(self):
        print(INTRO_BANNER_GENERAL + "\n Available AUXILIARY plugins:""")

    def ShowWebPluginsBanner(self):
        print(INTRO_BANNER_GENERAL + INTRO_BANNER_WEB_PLUGIN_TYPE + "\n Available WEB plugins:""")

    def ShowPluginGroupPlugins(self, PluginGroup):
        for PluginType in self.config.Plugin.GetTypesForGroup(PluginGroup):
            self.ShowPluginTypePlugins(PluginType, PluginGroup)

    def ShowPluginTypePlugins(self, PluginType, PluginGroup):
        cprint("\n" + '*' * 40 + " " + PluginType.title().replace('_', '-') + " plugins " + '*' * 40)
        for Plugin in self.config.Plugin.GetAll(PluginGroup, PluginType):
            # 'Name' : PluginName, 'Code': PluginCode, 'File' : PluginFile, 'Descrip' : PluginDescrip } )
            LineStart = " " + Plugin['type'] + ": " + Plugin['name']
            Pad1 = "_" * (60 - len(LineStart))
            Pad2 = "_" * (20 - len(Plugin['code']))
            cprint(LineStart + Pad1 + "(" + Plugin['code'] + ")" + Pad2 + Plugin['descrip'])

