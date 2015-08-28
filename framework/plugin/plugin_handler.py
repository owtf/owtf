#!/usr/bin/env python
"""
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
from ptp.libptp.constants import UNKNOWN
from ptp.libptp.exceptions import PTPError
from framework.dependency_management.dependency_resolver import BaseComponent
from framework.dependency_management.interfaces import PluginHandlerInterface

from framework.lib.exceptions import FrameworkAbortException, \
                                     PluginAbortException, \
                                     UnreachableTargetException
from framework.lib.general import *
from framework.plugin.scanner import Scanner
from framework.utils import FileOperations


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


class PluginHandler(BaseComponent, PluginHandlerInterface):

    COMPONENT_NAME = "plugin_handler"

    def __init__(self, options):
        self.register_in_service_locator()
        self.Core = None
        self.db = self.get_component("db")
        self.config = self.get_component("config")
        self.plugin_output = None
        self.db_plugin = self.get_component("db_plugin")
        self.target = self.get_component("target")
        self.transaction = self.get_component("transaction")
        self.error_handler = self.get_component("error_handler")
        self.reporter = None
        self.timer = self.get_component("timer")
        self.init_options(options)

    def init_options(self, options):
        """Initialize CLI options for each instance of PluginHandler."""
        self.PluginCount = 0
        self.Simulation = options['Simulation']
        self.Scope = options['Scope']
        self.PluginGroup = options['PluginGroup']
        self.OnlyPluginsList = self.ValidateAndFormatPluginList(options.get('OnlyPlugins'))
        self.ExceptPluginsList = self.ValidateAndFormatPluginList(options.get('ExceptPlugins'))
        if isinstance(options.get('PluginType'), str):  # For special plugin types like "quiet" -> "semi_passive" + "passive"
            options['PluginType'] = options['PluginType'].split(',')
        self.scanner = None
        self.InitExecutionRegistry()

    def init(self, options):
        self.init_options(options)
        self.Core = self.get_component("core")
        self.plugin_output = self.get_component("plugin_output")
        self.reporter = self.get_component("reporter")
        self.scanner = Scanner()

    def PluginAlreadyRun(self, PluginInfo):
        return self.plugin_output.PluginAlreadyRun(PluginInfo)

    def ValidateAndFormatPluginList(self, plugin_codes):
        """Validate the plugin codes by checking if they exist.

        :param list plugin_codes: OWTF plugin codes to be validated.

        :return: validated plugin codes.
        :rtype: list

        """
        # Ensure there is always a list to iterate from! :)
        if not plugin_codes:
            return []
        valid_plugin_codes = []
        plugins_by_group = self.db_plugin.GetPluginsByGroup(self.PluginGroup)
        for code in plugin_codes:
            found = False
            for plugin in plugins_by_group:  # Processing Loop
                if code in [plugin['code'], plugin['name']]:
                    valid_plugin_codes.append(plugin['code'])
                    found = True
                    break
            if not found:
                self.error_handler.FrameworkAbort(
                    "The code '%s' is not a valid plugin, please use the -l option to see available plugin names and codes" % code),
        return valid_plugin_codes  # Return list of Codes

    def InitExecutionRegistry(self):  # Initialises the Execution registry: As plugins execute they will be tracked here, useful to avoid calling plugins stupidly :)
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
            for Key, Value in ExecLog[Index].items():  # Compare all execution log values against the passed Plugin, if all match, return index to log record
                if not Key in Plugin or Plugin[Key] != Value:
                    Match = False
            if Match:
                #print str(PluginIprint "you have etered " + cnfo)+" was found!"
                return Index
        return -1

    def PluginAlreadyRun(self, PluginInfo):
        return self.plugin_output.PluginAlreadyRun(PluginInfo)

    def GetExecLogSinceLastExecution(self, Plugin):  # Get all execution entries from log since last time the passed plugin executed
        return self.ExecutionRegistry[self.config.GetTarget()][self.GetLastPluginExecution(Plugin):]

    def GetPluginOutputDir(self, Plugin): # Organise results by OWASP Test type and then active, passive, semi_passive
        #print "Plugin="+str(Plugin)+", Partial url ..="+str(self.Core.Config.Get('partial_url_output_path'))+", TARGET="+self.Core.Config.Get('TARGET')
        if ((Plugin['group'] == 'web') or (Plugin['group'] == 'net')):
            return os.path.join(self.target.GetPath('partial_url_output_path'), WipeBadCharsForFilename(Plugin['title']), Plugin['type'])
        elif Plugin['group'] == 'aux':
            return os.path.join(self.config.Get('AUX_OUTPUT_PATH'), WipeBadCharsForFilename(Plugin['title']), Plugin['type'])

    def RequestsPossible(self):
        # Even passive plugins will make requests to external resources
        # return [ 'grep' ] != self.config.GetAllowedPluginTypes('web')
        return ['grep'] != self.db_plugin.GetTypesForGroup('web')

    def DumpOutputFile(self, Filename, Contents, Plugin, RelativePath=False):
        SaveDir = self.GetPluginOutputDir(Plugin)
        abs_path = FileOperations.dump_file(Filename, Contents, SaveDir)
        if RelativePath:
            return (os.path.relpath(abs_path, self.config.GetOutputDirForTargets()))
        return (abs_path)

    def RetrieveAbsPath(self, RelativePath):
        return (os.path.join(self.config.GetOutputDirForTargets(), RelativePath))

    def GetPluginOutputDir(self, Plugin):  # Organise results by OWASP Test type and then active, passive, semi_passive
        # print "Plugin="+str(Plugin)+", Partial url ..="+str(self.config.Get('PARTIAL_URL_OUTPUT_PATH'))+", TARGET="+self.config.Get('TARGET')
        if ((Plugin['group'] == 'web') or (Plugin['group'] == 'net')):
            return os.path.join(self.target.GetPath('partial_url_output_path'), WipeBadCharsForFilename(Plugin['title']), Plugin['type'])
        elif Plugin['group'] == 'aux':
            return os.path.join(self.config.Get('AUX_OUTPUT_PATH'), WipeBadCharsForFilename(Plugin['title']), Plugin['type'])

    def exists(self, directory):
        return os.path.exists(directory)

    def GetModule(self, ModuleName, ModuleFile, ModulePath):  # Python fiddling to load a module from a file, there is probably a better way...
        f, Filename, desc = imp.find_module(ModuleFile.split('.')[0], [ModulePath])  # ModulePath = os.path.abspath(ModuleFile)
        return imp.load_module(ModuleName, f, Filename, desc)

    def chosen_plugin(self, plugin, show_reason=False):
        """Verify that the plugin has been chosen by the user.

        :param dict plugin: The plugin dictionary with all the information.
        :param bool show_reason: If the plugin cannot be run, print the reason.

        :return: True if the plugin has been chosen, False otherwise.
        :rtype: bool

        """
        chosen = True
        reason = 'not-specified'
        if plugin['group'] == self.PluginGroup:
            # Skip plugins not present in the white-list defined by the user.
            if self.OnlyPluginsList and plugin['code'] not in self.OnlyPluginsList:
                chosen = False
                reason = 'not in white-list'
            # Skip plugins present in the black-list defined by the user.
            if self.ExceptPluginsList and plugin['code'] in self.ExceptPluginsList:
                chosen = False
                reason = 'in black-list'
        if plugin['type'] not in self.db_plugin.GetTypesForGroup(plugin['group']):
            chosen = False  # Skip plugin: Not matching selected type
            reason = 'not matching selected type'
        if not chosen and show_reason:
            logging.warning(
                'Plugin: %s (%s/%s) has not been chosen by the user (%s), skipping...',
                plugin['title'],
                plugin['group'],
                plugin['type'],
                reason)
        return chosen

    def force_overwrite(self):
        # return self.config.Get('FORCE_OVERWRITE')
        return False

    def plugin_can_run(self, plugin, show_reason=False):
        """Verify that a plugin can be run by OWTF.

        :param dict plugin: The plugin dictionary with all the information.
        :param bool show_reason: If the plugin cannot be run, print the reason.

        :return: True if the plugin can be run, False otherwise.
        :rtype: bool

        """
        if not self.chosen_plugin(plugin, show_reason=show_reason):
            return False  # Skip not chosen plugins
        # Grep plugins to be always run and overwritten (they run once after
        # semi_passive and then again after active):
        if self.PluginAlreadyRun(plugin) and ((not self.force_overwrite() and not ('grep' == plugin['type'])) or plugin['type'] == 'external'):
            if show_reason:
                logging.warning(
                    "Plugin: %s (%s/%s) has already been run, skipping...",
                    plugin['title'],
                    plugin['group'],
                    plugin['type'])
            return False
        if 'grep' == plugin['type'] and self.PluginAlreadyRun(plugin):
            # Grep plugins can only run if some active or semi_passive plugin
            # was run since the last time
            return False
        return True

    def GetPluginFullPath(self, PluginDir, Plugin):
        return PluginDir + "/" + Plugin['type'] + "/" + Plugin['file']  # Path to run the plugin

    def RunPlugin(self, PluginDir, Plugin, save_output=True):
        PluginPath = self.GetPluginFullPath(PluginDir, Plugin)
        (Path, Name) = os.path.split(PluginPath)
        PluginOutput = self.GetModule("", Name, Path + "/").run(Plugin)
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
        msf_modules = None
        if output:
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
                    owtf_rank = max(owtf_rank, parser.get_highest_ranking())
            else:
                parser.parse(pathname=pathname)
                owtf_rank = parser.get_highest_ranking()
        except PTPError:  # Not supported tool or report not found.
            pass
        if owtf_rank == UNKNOWN:  # Ugly truth... PTP gives 0 for unranked but OWTF uses -1 instead...
            owtf_rank = -1
        return owtf_rank

    def ProcessPlugin(self, plugin_dir, plugin, status={}):
        """Process a plugin from running to ranking.

        :param str plugin_dir: Path to the plugin directory.
        :param dict plugin: The plugin dictionary with all the information.
        :param dict status: Running status of the plugin.

        :return: The output generated by the plugin when run.
        :return: None if the plugin was not run.
        :rtype: list

        """
        # Ensure that the plugin CAN be run before starting anything.
        if not self.plugin_can_run(plugin, show_reason=True):
            return None
        # Save how long it takes for the plugin to run.
        self.timer.start_timer('Plugin')
        plugin['start'] = self.timer.get_start_date_time('Plugin')
        # Use relative path from targets folders while saving
        plugin['output_path'] = os.path.relpath(
            self.GetPluginOutputDir(plugin),
            self.config.GetOutputDirForTargets())
        status['AllSkipped'] = False  # A plugin is going to be run.
        plugin['status'] = 'Running'
        self.PluginCount += 1
        logging.info(
            '_' * 10 + ' %d - Target: %s -> Plugin: %s (%s/%s) ' + '_' * 10,
            self.PluginCount,
            self.target.GetTargetURL(),
            plugin['title'],
            plugin['group'],
            plugin['type'])
        # Skip processing in simulation mode, but show until line above
        # to illustrate what will run
        if self.Simulation:
            return None
        # DB empty => grep plugins will fail, skip!!
        if ('grep' == plugin['type'] and self.transaction.NumTransactions() == 0):
            logging.info(
                'Skipped - Cannot run grep plugins: '
                'The Transaction DB is empty')
            return None
        output = None
        status_msg = ''
        partial_output = []
        abort_reason = ''
        try:
            output = self.RunPlugin(plugin_dir, plugin)
            status_msg = 'Successful'
            status['SomeSuccessful'] = True
        except KeyboardInterrupt:
            # Just explain why crashed.
            status_msg = 'Aborted'
            abort_reason = 'Aborted by User'
            status['SomeAborted (Keyboard Interrupt)'] = True
        except SystemExit:
            # Abort plugin processing and get out to external exception
            # handling, information saved elsewhere.
            raise SystemExit
        except PluginAbortException as PartialOutput:
            status_msg = 'Aborted (by user)'
            partial_output = PartialOutput.parameter
            abort_reason = 'Aborted by User'
            status['SomeAborted'] = True
        except UnreachableTargetException as PartialOutput:
            status_msg = 'Unreachable Target'
            partial_output = PartialOutput.parameter
            abort_reason = 'Unreachable Target'
            status['SomeAborted'] = True
        except FrameworkAbortException as PartialOutput:
            status_msg = 'Aborted (Framework Exit)'
            partial_output = PartialOutput.parameter
            abort_reason = 'Framework Aborted'
        # TODO: Handle this gracefully
        # except:
        # Plugin["status"] = "Crashed"
        #     cprint("Crashed")
        #     self.SavePluginInfo(self.Core.Error.Add("Plugin "+Plugin['Type']+"/"+Plugin['File']+" failed for target "+self.Core.Config.Get('TARGET')), Plugin) # Try to save something
        #     TODO: http://blog.tplus1.com/index.php/2007/09/28/the-python-logging-module-is-much-better-than-print-statements/
        finally:
            plugin['status'] = status_msg
            plugin['end'] = self.timer.get_end_date_time('Plugin')
            plugin['owtf_rank'] = self.rank_plugin(output, self.GetPluginOutputDir(plugin))
            if status_msg == 'Successful':
                self.plugin_output.SavePluginOutput(plugin, output)
            else:
                self.plugin_output.SavePartialPluginOutput(
                    plugin,
                    partial_output,
                    abort_reason)
            if status_msg == 'Aborted':
                self.error_handler.UserAbort('Plugin')
            if abort_reason == 'Framework Aborted':
                self.Core.finish()
        return output

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
        return self.db_plugin.GetOrder(PluginGroup)

    def get_plugins_in_order(self, PluginGroup):
        return self.db_plugin.GetOrder(PluginGroup)

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
            #       for Plugin in self.db_plugin.GetOrder(PluginGroup):# For each Plugin
            #               #print "Processing Plugin="+str(Plugin)
            #               for Target in TargetList: # For each Target
            #                       #print "Processing Target="+str(Target)
            #                       self.SwitchToTarget(Target) # Tell Config that all Gets/Sets are now Target-specific
            #                       self.ProcessPlugin( PluginDir, Plugin, Status )
            #elif 'depth' == self.Algorithm: # Loop Targets, then plugins
            #       for Target in TargetList: # For each Target
            #               self.SwitchToTarget(Target) # Tell Config that all Gets/Sets are now Target-specific
            #               for Plugin in self.db_plugin.GetOrder(PluginGroup):# For each Plugin
            #                       self.ProcessPlugin( PluginDir, Plugin, Status )

    def clean_up(self):
        if getattr(self, "WorkerManager", None) is not None:
            self.WorkerManager.clean_up()

    def SavePluginInfo(self, PluginOutput, Plugin):
        self.db.SaveDBs()  # Save new URLs to DB after each request
        self.reporter.SavePluginReport(PluginOutput, Plugin)  # Timer retrieved by Reporter

    def show_plugin_list(self, group, msg=INTRO_BANNER_GENERAL):
        if group == 'web':
            logging.info(msg + INTRO_BANNER_WEB_PLUGIN_TYPE + "\nAvailable WEB plugins:")
        elif group == 'aux':
            logging.info(msg + "\nAvailable AUXILIARY plugins:")
        elif group == 'net':
            logging.info(msg + "\nAvailable NET plugins:")
        for plugin_type in self.db_plugin.GetTypesForGroup(group):
            self.show_plugin_types(plugin_type, group)

    def show_plugin_types(self, plugin_type, group):
        logging.info("\n" + '*' * 40 + " " + plugin_type.title().replace('_', '-') + " plugins " + '*' * 40)
        for Plugin in self.db_plugin.GetPluginsByGroupType(group, plugin_type):
            # 'Name' : PluginName, 'Code': PluginCode, 'File' : PluginFile, 'Descrip' : PluginDescrip } )
            LineStart = " " + Plugin['type'] + ": " + Plugin['name']
            Pad1 = "_" * (60 - len(LineStart))
            Pad2 = "_" * (20 - len(Plugin['code']))
            logging.info(LineStart + Pad1 + "(" + Plugin['code'] + ")" + Pad2 + Plugin['descrip'])

