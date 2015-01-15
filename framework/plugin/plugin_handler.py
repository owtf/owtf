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

    def __init__(self, Options):
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
        self.init_options(Options)

    def init_options(self, options):
        """Initialize CLI options for each instance of PluginHandler."""
        self.PluginCount = 0
        self.Simulation = options['Simulation']
        self.Scope = options['Scope']
        self.PluginGroup = options['PluginGroup']
        self.OnlyPluginsList = self.format_plugin_codes(options.get('OnlyPlugins'))
        self.ExceptPluginsList = self.format_plugin_codes(options.get('ExceptPlugins'))
        if isinstance(options.get('PluginType'), str):  # For special plugin types like "quiet" -> "semi_passive" + "passive"
            options['PluginType'] = options['PluginType'].split(',')
        self.scanner = None
        self.init_execution_registry()

    def init(self, options):
        self.init_options(options)
        self.Core = self.get_component("core")
        self.plugin_output = self.get_component("plugin_output")
        self.reporter = self.get_component("reporter")
        self.scanner = Scanner()

    def format_plugin_codes(self, codes):
        """Validate the plugin codes by checking if they exist.

        :param list codes: OWTF plugin codes to be validated.

        :return: validated plugin codes.
        :rtype: list

        """
        # Ensure there is always a list to iterate from! :)
        codes = codes or []
        valid_plugin_codes = []
        plugins_by_group = self.db_plugin.GetPluginsByGroup(self.PluginGroup)
        for code in codes:
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

    def init_execution_registry(self):  # Initialises the Execution registry: As plugins execute they will be tracked here, useful to avoid calling plugins stupidly :)
        self.ExecutionRegistry = defaultdict(list)
        for target in self.Scope:
            self.ExecutionRegistry[target] = []

    def requests_possible(self):
        # Even passive plugins will make requests to external resources
        # return [ 'grep' ] != self.config.GetAllowedPluginTypes('web')
        return ['grep'] != self.db_plugin.GetTypesForGroup('web')

    def get_plugin_output_dir(self, Plugin):  # Organise results by OWASP Test type and then active, passive, semi_passive
        # print "Plugin="+str(Plugin)+", Partial url ..="+str(self.config.Get('PARTIAL_URL_OUTPUT_PATH'))+", TARGET="+self.config.Get('TARGET')
        if ((Plugin['group'] == 'web') or (Plugin['group'] == 'net')):
            return os.path.join(self.target.GetPath('partial_url_output_path'), WipeBadCharsForFilename(Plugin['title']), Plugin['type'])
        elif Plugin['group'] == 'aux':
            return os.path.join(self.config.Get('AUX_OUTPUT_PATH'), WipeBadCharsForFilename(Plugin['title']), Plugin['type'])

    def dump_output_file(self, Filename, Contents, Plugin, RelativePath=False):
        SaveDir = self.get_plugin_output_dir(Plugin)
        abs_path = FileOperations.dump_file(Filename, Contents, SaveDir)
        if RelativePath:
            return (os.path.relpath(abs_path, self.config.GetOutputDirForTargets()))
        return (abs_path)

    def load_plugin(self, ModuleName, ModuleFile, ModulePath):  # Python fiddling to load a module from a file, there is probably a better way...
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
        if self.plugin_output.PluginAlreadyRun(plugin) and ((not ('grep' == plugin['type'])) or plugin['type'] == 'external'):
            if show_reason:
                logging.warning(
                    "Plugin: %s (%s/%s) has already been run, skipping...",
                    plugin['title'],
                    plugin['group'],
                    plugin['type'])
            return False
        if 'grep' == plugin['type'] and self.plugin_output.PluginAlreadyRun(plugin):
            # Grep plugins can only run if some active or semi_passive plugin
            # was run since the last time
            return False
        return True

    def plugin_full_path(self, path, plugin):
        return os.path.join(path, plugin['type'], plugin['file'])

    def run_plugin(self, path, plugin, save_output=True):
        plugin_path = self.plugin_full_path(path, plugin)
        (path, name) = os.path.split(plugin_path)
        return self.load_plugin("", name, path + "/").run(plugin)

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
            return [(
                output['output'].get('ModifiedCommand', '').split(' ')[3],
                os.path.basename(output['output'].get('RelativeFilePath', '')))
                for output in cmd
                if ('output' in output and 'metasploit' in output['output'].get('ModifiedCommand', ''))]

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
                    owtf_rank = max(
                        owtf_rank,
                        parser.get_highest_ranking())
            else:
                parser.parse(pathname=pathname)
                owtf_rank = parser.get_highest_ranking()
        except PTPError:  # Not supported tool or report not found.
            pass
        return owtf_rank

    def process_plugin(self, plugin_dir, plugin, status={}):
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
            self.get_plugin_output_dir(plugin),
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
            logging.info('Skipped - Cannot run grep plugins: The Transaction DB is empty')
            return None
        output = None
        status_msg = ''
        partial_output = []
        abort_reason = ''
        try:
            output = self.run_plugin(plugin_dir, plugin)
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
        finally:
            plugin['status'] = status_msg
            plugin['end'] = self.timer.get_end_date_time('Plugin')
            plugin['owtf_rank'] = self.rank_plugin(
                output,
                self.get_plugin_output_dir(plugin))
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

    def get_plugin_group_dir(self, PluginGroup):
        PluginDir = self.config.FrameworkConfigGet('PLUGINS_DIR') + PluginGroup
        return PluginDir

    def switch_to_target(self, target):
        # Tell Target DB that all Gets/Sets are now Target-specific
        self.target.SetTarget(target)

    def process_plugins_for_target_list(self, group, status, targets):
        path = self.get_plugin_group_dir(group)
        if group == 'net':
            portwaves = self.config.Get('PORTWAVES')
            waves = portwaves.split(',')
            waves.append('-1')
            lastwave = 0
            for target in targets:  # For each Target
                self.scanner.scan_network(target)
                # Scanning and processing the first part of the ports
                ports = self.config.GetTcpPorts(lastwave, waves[0])
                logging.info("Probing for ports:", str(ports))
                http = self.scanner.probe_network(target, 'tcp', ports)
                # Tell Config that all Gets/Sets are now
                # Target-specific.
                self.SwitchToTarget(target)
                for Plugin in self.db_plugin.GetOrder(group):
                    self.process_plugin(path, Plugin, status)
                lastwave = waves[0]
                for http_ports in http:
                    if http_ports == '443':
                        self.process_plugins_for_target_list(
                            'web', {
                                'SomeAborted': False,
                                'SomeSuccessful': False,
                                'AllSkipped': True},
                            {'https://' + Target.split('//')[1]})
                    else:
                        self.process_plugins_for_target_list(
                            'web', {
                                'SomeAborted': False,
                                'SomeSuccessful': False,
                                'AllSkipped': True},
                            {Target})

    def clean_up(self):
        if getattr(self, "WorkerManager", None) is not None:
            self.WorkerManager.clean_up()

    def show_plugin_list(self, group):
        if group == 'web':
            self.show_web_plugins_banner()
        elif group == 'aux':
            self.show_aux_plugins_banner()
        elif group == 'net':
            self.show_net_plugins_banner()
        self.show_plugin_group(group)

    def show_net_plugins_banner(self):
        logging.info(INTRO_BANNER_GENERAL + "\nAvailable NET plugins")

    def show_aux_plugins_banner(self):
        logging.info(INTRO_BANNER_GENERAL + "\n Available AUXILIARY plugins:")

    def show_web_plugins_banner(self):
        logging.info(INTRO_BANNER_GENERAL + INTRO_BANNER_WEB_PLUGIN_TYPE + "\n Available WEB plugins:")

    def show_plugin_group(self, group):
        for plugin_type in self.db_plugin.GetTypesForGroup(group):
            self.show_plugin_type(plugin_type, group)

    def show_plugin_type(self, plugin_type, PluginGroup):
        logging.info("\n" + '*' * 40 + " " + plugin_type.title().replace('_', '-') + " plugins " + '*' * 40)
        for Plugin in self.db_plugin.GetPluginsByGroupType(PluginGroup, plugin_type):
            # 'Name' : PluginName, 'Code': PluginCode, 'File' : PluginFile, 'Descrip' : PluginDescrip } )
            LineStart = " " + Plugin['type'] + ": " + Plugin['name']
            Pad1 = "_" * (60 - len(LineStart))
            Pad2 = "_" * (20 - len(Plugin['code']))
            logging.info(LineStart + Pad1 + "(" + Plugin['code'] + ")" + Pad2 + Plugin['descrip'])
