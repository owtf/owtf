"""
owtf.plugin.plugin_handler
~~~~~~~~~~~~~~~~~~~~~~~~~~

The PluginHandler is in charge of running all plugins taking into account the
chosen settings.
"""

import imp
import logging

from owtf.lib.exceptions import FrameworkAbortException, PluginAbortException, UnreachableTargetException
from owtf.lib.general import *
from ptp import PTP
from ptp.libptp.constants import UNKNOWN
from ptp.libptp.exceptions import PTPError
from sqlalchemy.exc import SQLAlchemyError

from owtf.dependency_management.dependency_resolver import BaseComponent
from owtf.dependency_management.interfaces import PluginHandlerInterface
from owtf.plugin.scanner import Scanner
from owtf.utils import FileOperations


INTRO_BANNER_GENERAL = """
Short Intro:
Current Plugin Groups:
- web: For web assessments or when network plugins find a port that "speaks HTTP"
- network: For network assessments, discovery and port probing
- auxiliary: Auxiliary plugins, to automate miscelaneous tasks
"""

INTRO_BANNER_WEB_PLUGIN_TYPE = """
WEB Plugin Types:
- Passive Plugins: NO requests sent to target
- Semi Passive Plugins: SOME "normal/legitimate" requests sent to target
- Active Plugins: A LOT OF "bad" requests sent to target (You better have permission!)
- Grep Plugins: NO requests sent to target. 100% based on transaction searches and plugin output parsing.
  Automatically run after semi_passive and active in default profile.
"""


class PluginHandler(BaseComponent, PluginHandlerInterface):

    COMPONENT_NAME = "plugin_handler"

    def __init__(self, options):
        self.register_in_service_locator()
        self.core = None
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
        self.plugin_count = 0
        self.simulation = options['Simulation']
        self.scope = options['Scope']
        self.plugin_group = options['PluginGroup']
        self.only_plugins_list = self.validate_format_plugin_list(options.get('OnlyPlugins'))
        self.except_plugins_list = self.validate_format_plugin_list(options.get('ExceptPlugins'))
        # For special plugin types like "quiet" -> "semi_passive" + "passive"
        if isinstance(options.get('PluginType'), str):
            options['PluginType'] = options['PluginType'].split(',')
        self.scanner = None
        self.init_exec_registry()

    def init(self, options):
        self.init_options(options)
        self.core = self.get_component("core")
        self.plugin_output = self.get_component("plugin_output")
        self.reporter = self.get_component("reporter")
        self.scanner = Scanner()

    def plugin_already_run(self, plugin_info):
        """Check if plugin has already run

        :param plugin_info: Plugin info
        :type plugin_info: `dict`
        :return: true/false
        :rtype: `bool`
        """
        return self.plugin_output.plugin_already_run(plugin_info)

    def validate_format_plugin_list(self, plugin_codes):
        """Validate the plugin codes by checking if they exist.

        :param list plugin_codes: OWTF plugin codes to be validated.

        :return: validated plugin codes.
        :rtype: list

        """
        # Ensure there is always a list to iterate from! :)
        if not plugin_codes:
            return []
        valid_plugin_codes = []
        plugins_by_group = self.db_plugin.get_plugins_by_group(self.plugin_group)
        for code in plugin_codes:
            found = False
            for plugin in plugins_by_group:  # Processing Loop
                if code in [plugin['code'], plugin['name']]:
                    valid_plugin_codes.append(plugin['code'])
                    found = True
                    break
            if not found:
                self.error_handler.abort_framework("The code '%s' is not a valid plugin, please use the -l option to see"
                                                  "available plugin names and codes" % code)
        return valid_plugin_codes  # Return list of Codes

    def init_exec_registry(self):
        """Initialises the Execution registry: As plugins execute they will be tracked here
        Useful to avoid calling plugins stupidly :)

        :return: None
        :rtype: None
        """
        self.exec_registry = defaultdict(list)
        for target in self.scope:
            self.exec_registry[target] = []

    def get_last_plugin_exec(self, plugin):
        """Get shortcut to relevant execution log for this target for readability below :)

        :param plugin: plugin dict
        :type plugin: `dict`
        :return: Index
        :rtype: `int`
        """
        exec_log = self.exec_registry[self.config.target]
        num_items = len(exec_log)
        if num_items == 0:
            return -1  # List is empty
        for index in range((num_items - 1), -1, -1):
            match = True
            # Compare all execution log values against the passed Plugin, if all match, return index to log record
            for k, v in list(exec_log[index].items()):
                if k not in plugin or plugin[k] != v:
                    match = False
            if match:
                return index
        return -1

    def get_log_since_last_exec(self, plugin):
        """Get all execution entries from log since last time the passed plugin executed

        :param plugin: Plugin dict
        :type plugin: `dict`
        :return: The logs from execution registry
        :rtype: `dict`
        """
        return self.exec_registry[self.config.target][self.get_last_plugin_exec(plugin):]

    def get_plugin_output_dir(self, plugin):
        """Get plugin directory by test type

        :param plugin: Plugin dict
        :type plugin: `dict`
        :return: Path to the plugin's output dir
        :rtype: `str`
        """
        # Organise results by OWASP Test type and then active, passive, semi_passive
        if ((plugin['group'] == 'web') or (plugin['group'] == 'network')):
            return os.path.join(self.target.get_path('partial_url_output_path'),
                                wipe_bad_chars(plugin['title']), plugin['type'])
        elif plugin['group'] == 'auxiliary':
            return os.path.join(self.config.get_val('AUX_OUTPUT_PATH'), wipe_bad_chars(plugin['title']),
                                plugin['type'])

    def requests_possible(self):
        """Check if requests are possible
        .note::
             Even passive plugins will make requests to external resources

        :return:
        :rtype: `bool`
        """
        return ['grep'] != self.db_plugin.get_types_for_plugin_group('web')

    def dump_output_file(self, filename, contents, plugin, relative_path=False):
        """Dumps output file to path

        :param filename: Name of the file
        :type filename: `str`
        :param contents: Contents of the file
        :type contents: `str`
        :param plugin: Plugin
        :type plugin: `dict`
        :param relative_path: use relative path
        :type relative_path: `bool`
        :return: Absolute path to the file
        :rtype: `str`
        """
        save_dir = self.get_plugin_output_dir(plugin)
        abs_path = FileOperations.dump_file(filename, contents, save_dir)
        if relative_path:
            return (os.path.relpath(abs_path, self.config.get_output_dir_target()))
        return abs_path

    def get_abs_path(self, relative_path):
        """Absolute path from relative path

        :param relative_path: Relative path
        :type relative_path: `str`
        :return: The absolute path
        :rtype: `str`
        """
        return (os.path.join(self.config.get_output_dir_target(), relative_path))

    def exists(self, directory):
        """Check if directory exists

        :param directory: directory to check
        :type directory: `str`
        :return: True if it exists, else False
        :rtype: `bool`
        """
        return os.path.exists(directory)

    def get_module(self, module_name, module_file, module_path):
        """Python fiddling to load a module from a file, there is probably a better way...

        .usage::
            ModulePath = os.path.abspath(ModuleFile)

        :param module_name: Name of the module
        :type module_name: `str`
        :param module_file:  Name of module file
        :type module_file: `str`
        :param module_path: path to the module
        :type module_path: `str`
        :return: None
        :rtype: None
        """
        f, filename, desc = imp.find_module(module_file.split('.')[0], [module_path])
        return imp.load_module(module_name, f, filename, desc)

    def chosen_plugin(self, plugin, show_reason=False):
        """Verify that the plugin has been chosen by the user.

        :param dict plugin: The plugin dictionary with all the information.
        :param bool show_reason: If the plugin cannot be run, print the reason.

        :return: True if the plugin has been chosen, False otherwise.
        :rtype: bool

        """
        chosen = True
        reason = 'not-specified'
        if plugin['group'] == self.plugin_group:
            # Skip plugins not present in the white-list defined by the user.
            if self.only_plugins_list and plugin['code'] not in self.only_plugins_list:
                chosen = False
                reason = 'not in white-list'
            # Skip plugins present in the black-list defined by the user.
            if self.except_plugins_list and plugin['code'] in self.except_plugins_list:
                chosen = False
                reason = 'in black-list'
        if plugin['type'] not in self.db_plugin.get_types_for_plugin_group(plugin['group']):
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
        """Force overwrite default config

        :return:
        :rtype:
        """
        return self.config.get('FORCE_OVERWRITE')

    def plugin_can_run(self, plugin, show_reason=False):
        """Verify that a plugin can be run by OWTF.

        :param dict plugin: The plugin dictionary with all the information.
        :param bool show_reason: If the plugin cannot be run, print the reason.

        :return: True if the plugin can be run, False otherwise.
        :rtype: bool

        """
        if not self.chosen_plugin(plugin, show_reason=show_reason):
            return False  # Skip not chosen plugins
        # Grep plugins to be always run and overwritten (they run once after semi_passive and then again after active)
        if self.plugin_already_run(plugin) and ((not self.force_overwrite() and not ('grep' == plugin['type'])) or
                                              plugin['type'] == 'external'):
            if show_reason:
                logging.warning(
                    "Plugin: %s (%s/%s) has already been run, skipping...",
                    plugin['title'],
                    plugin['group'],
                    plugin['type']
                )
            return False
        if 'grep' == plugin['type'] and self.plugin_already_run(plugin):
            # Grep plugins can only run if some active or semi_passive plugin was run since the last time
            return False
        return True

    def get_plugin_full_path(self, plugin_dir, plugin):
        """Get full path to the plugin

        :param plugin_dir: path to the plugin directory
        :type plugin_dir: `str`
        :param plugin: Plugin dict
        :type plugin: `dict`
        :return: Full path to the plugin
        :rtype: `str`
        """
        return "%s/%s/%s" % (plugin_dir, plugin['type'], plugin['file'])  # Path to run the plugin

    def run_plugin(self, plugin_dir, plugin, save_output=True):
        """Run a specific plugin

        :param plugin_dir: path of plugin directory
        :type plugin_dir: `str`
        :param plugin: Plugin dict
        :type plugin: `dict`
        :param save_output: Save output option
        :type save_output: `bool`
        :return: Plugin output
        :rtype: `dict`
        """
        plugin_path = self.get_plugin_full_path(plugin_dir, plugin)
        path, name = os.path.split(plugin_path)
        plugin_output = self.get_module("", name, path + "/").run(plugin)
        return plugin_output

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
                    os.path.basename(output['output'].get('RelativeFilePath', ''))
                )
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
                    # filename - Path to output file.
                    # plugin - Metasploit module name.
                    parser.parse(pathname=pathname, filename=module[1], plugin=module[0], light=True)
                    owtf_rank = max(owtf_rank, parser.highest_ranking)
            else:
                parser.parse(pathname=pathname, light=True)
                owtf_rank = parser.highest_ranking
        except PTPError:  # Not supported tool or report not found.
            pass
        except Exception as e:
            logging.error('Unexpected exception when running PTP: %s' % e)
        if owtf_rank == UNKNOWN:  # Ugly truth... PTP gives 0 for unranked but OWTF uses -1 instead...
            owtf_rank = -1
        return owtf_rank

    def process_plugin(self, plugin_dir, plugin, status=None):
        """Process a plugin from running to ranking.

        :param str plugin_dir: Path to the plugin directory.
        :param dict plugin: The plugin dictionary with all the information.
        :param dict status: Running status of the plugin.

        :return: The output generated by the plugin when run.
        :return: None if the plugin was not run.
        :rtype: list

        """
        if status is None:
            status = {}
        # Ensure that the plugin CAN be run before starting anything.
        if not self.plugin_can_run(plugin, show_reason=True):
            return None
        # Save how long it takes for the plugin to run.
        self.timer.start_timer('Plugin')
        plugin['start'] = self.timer.get_start_date_time('Plugin')
        # Use relative path from targets folders while saving
        plugin['output_path'] = os.path.relpath(self.get_plugin_output_dir(plugin), self.config.get_output_dir_target())
        status['AllSkipped'] = False  # A plugin is going to be run.
        plugin['status'] = 'Running'
        self.plugin_count += 1
        logging.info(
            '_' * 10 + ' %d - Target: %s -> Plugin: %s (%s/%s) ' + '_' * 10,
            self.plugin_count,
            self.target.get_target_url(),
            plugin['title'],
            plugin['group'],
            plugin['type'])
        # Skip processing in simulation mode, but show until line above
        # to illustrate what will run
        if self.simulation:
            return None
        # DB empty => grep plugins will fail, skip!!
        if ('grep' == plugin['type'] and self.transaction.num_transactions() == 0):
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
        # TODO: Handle this gracefully
        # Replace print by logging
        finally:
            plugin['status'] = status_msg
            plugin['end'] = self.timer.get_end_date_time('Plugin')
            plugin['owtf_rank'] = self.rank_plugin(output, self.get_plugin_output_dir(plugin))
            try:
                if status_msg == 'Successful':
                    self.plugin_output.save_plugin_output(plugin, output)
                else:
                    self.plugin_output.save_partial_output(plugin, partial_output, abort_reason)
            except SQLAlchemyError as e:
                logging.error("Exception occurred while during database transaction : \n%s", str(e))
                output += str(e)
            if status_msg == 'Aborted':
                self.error_handler.user_abort('Plugin')
            if abort_reason == 'Framework Aborted':
                self.core.finish()
        return output

    def process_plugins(self):
        """Process plugins

        :return:
        :rtype:
        """
        status = {'SomeAborted': False, 'SomeSuccessful': False, 'AllSkipped': True}
        if self.plugin_group in ['web', 'auxiliary', 'network']:
            self.process_plugins_for_target_list(self.plugin_group, status, self.target.get_all("ID"))
        return status

    def get_plugin_group_dir(self, plugin_group):
        """Get directory for plugin group

        :param plugin_group: Plugin group
        :type plugin_group: `str`
        :return: Path to the output dir for plugin group
        :rtype: `str`
        """
        plugin_dir = self.config.get_val('PLUGINS_DIR') + plugin_group
        return plugin_dir

    def switch_to_target(self, target):
        """Switch to target

        :param target: target id
        :type target: `int`
        :return: None
        :rtype: None
        """
        self.target.set_target(target)  # Tell Target DB that all Gets/Sets are now Target-specific

    def process_plugins_for_target_list(self, plugin_group, status, target_list):
        """Process plugins for all targets in the list

        :param plugin_group: Plugin group
        :type plugin_group: `str`
        :param status: Plugin exec status
        :type status: `dict`
        :param target_list: List of targets
        :type target_list: `list`
        :return: None
        :rtype: None
        """
        plugin_dir = self.get_plugin_group_dir(plugin_group)
        if plugin_group == 'network':
            portwaves = self.config.get('PORTWAVES')
            waves = portwaves.split(',')
            waves.append('-1')
            lastwave = 0
            for target in target_list:  # For each Target
                self.scanner.scan_network(target)
                # Scanning and processing the first part of the ports
                for i in range(1):
                    ports = self.config.get_tcp_ports(lastwave, waves[i])
                    print("Probing for ports %s" % str(ports))
                    http = self.scanner.probe_network(target, 'tcp', ports)
                    # Tell Config that all Gets/Sets are now
                    # Target-specific.
                    self.switch_to_target(target)
                    for plugin in plugin_group:
                        self.process_plugin(plugin_dir, plugin, status)
                    lastwave = waves[i]
                    for http_ports in http:
                        if http_ports == '443':
                            self.process_plugins_for_target_list(
                                'web',
                                {'SomeAborted': False, 'SomeSuccessful': False, 'AllSkipped': True},
                                {'https://%s' % target.split('//')[1]})
                        else:
                            self.process_plugins_for_target_list(
                                'web',
                                {'SomeAborted': False, 'SomeSuccessful': False, 'AllSkipped': True},
                                {target})
        else:
            pass

    def clean_up(self):
        """Cleanup workers

        :return: None
        :rtype: None
        """
        if getattr(self, "worker_manager", None) is not None:
            self.worker_manager.clean_up()

    def show_plugin_list(self, group, msg=INTRO_BANNER_GENERAL):
        """Show available plugins

        :param group: Plugin group
        :type group: `str`
        :param msg: Message to print
        :type msg: `str`
        :return: None
        :rtype: None
        """
        if group == 'web':
            logging.info("%s%s\nAvailable WEB plugins:", msg, INTRO_BANNER_WEB_PLUGIN_TYPE)
        elif group == 'auxiliary':
            logging.info("%s\nAvailable AUXILIARY plugins:", msg)
        elif group == 'network':
            logging.info("%s\nAvailable NETWORK plugins:", msg)
        for plugin_type in self.db_plugin.get_types_for_plugin_group(group):
            self.show_plugin_types(plugin_type, group)

    def show_plugin_types(self, plugin_type, group):
        """Show all plugin types

        :param plugin_type: Plugin type
        :type plugin_type: `str`
        :param group: Plugin group
        :type group: `str`
        :return: None
        :rtype: None
        """
        logging.info("\n%s %s plugins %s", '*' * 40, plugin_type.title().replace('_', '-'), '*' * 40)
        for plugin in self.db_plugin.get_plugins_by_group_type(group, plugin_type):
            line_start = " %s:%s" % (plugin['type'], plugin['name'])
            pad1 = "_" * (60 - len(line_start))
            pad2 = "_" * (20 - len(plugin['code']))
            logging.info("%s%s(%s)%s%s", line_start, pad1, plugin['code'], pad2, plugin['descrip'])
