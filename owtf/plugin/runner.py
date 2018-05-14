"""
owtf.plugin.runner
~~~~~~~~~~~~~~~~~~

The module is in charge of running all plugins taking into account the
chosen settings.
"""
import copy
from collections import defaultdict
import imp
import logging
import os

from ptp import PTP
from ptp.libptp.constants import UNKNOWN
from ptp.libptp.exceptions import PTPError
from sqlalchemy.exc import SQLAlchemyError

from owtf.config import config_handler
from owtf.db.session import get_scoped_session
from owtf.lib.exceptions import FrameworkAbortException, PluginAbortException, UnreachableTargetException
from owtf.managers.plugin import get_plugins_by_group, get_plugins_by_group_type, get_types_for_plugin_group
from owtf.managers.poutput import save_partial_output, save_plugin_output
from owtf.managers.target import target_manager
from owtf.managers.transaction import num_transactions
from owtf.net.scanner import Scanner
from owtf.settings import AUX_OUTPUT_PATH, PLUGINS_DIR
from owtf.utils.error import abort_framework, user_abort
from owtf.utils.file import FileOperations, get_output_dir_target
from owtf.utils.signals import owtf_start
from owtf.utils.strings import wipe_bad_chars
from owtf.utils.timer import timer

__all__ = ["runner", "show_plugin_list", "show_plugin_types"]

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


class PluginRunner(object):

    def __init__(self):
        # Complicated stuff to keep everything Pythonic and from blowing up
        def handle_signal(sender, **kwargs):
            self.on_start(sender, **kwargs)

        self.handle_signal = handle_signal
        owtf_start.connect(handle_signal)

        self.plugin_group = None
        self.simulation = None
        self.scope = None
        self.only_plugins = None
        self.except_plugins = None
        self.only_plugins_list = None
        self.except_plugins_list = None
        self.options = {}
        self.timer = timer
        self.plugin_count = 0
        self.session = get_scoped_session()

    def on_start(self, sender, **kwargs):
        self.options = copy.deepcopy(kwargs["args"])
        self.force_overwrite = self.options["force_overwrite"]
        self.plugin_group = self.options["plugin_group"]
        self.portwaves = self.options["port_waves"]
        self.simulation = self.options.get("Simulation", None)
        self.scope = self.options["scope"]
        self.only_plugins = self.options["only_plugins"]
        self.except_plugins = self.options["except_plugins"]
        self.except_plugins_list = self.validate_format_plugin_list(
            session=self.session, plugin_codes=self.only_plugins
        )
        # For special plugin types like "quiet" -> "semi_passive" + "passive"
        if isinstance(self.options.get("plugin_type"), str):
            self.options["plugin_type"] = self.options["plugin_type"].split(",")
        self.scanner = Scanner()
        self.init_exec_registry()

    def validate_format_plugin_list(self, session, plugin_codes):
        """Validate the plugin codes by checking if they exist.

        :param list plugin_codes: OWTF plugin codes to be validated.

        :return: validated plugin codes.
        :rtype: list

        """
        # Ensure there is always a list to iterate from! :)
        if not plugin_codes:
            return []
        valid_plugin_codes = []
        plugins_by_group = get_plugins_by_group(session=session, plugin_group=self.plugin_group)
        for code in plugin_codes:
            found = False
            for plugin in plugins_by_group:  # Processing Loop
                if code in [plugin["code"], plugin["name"]]:
                    valid_plugin_codes.append(plugin["code"])
                    found = True
                    break
            if not found:
                abort_framework(
                    "The code '{!s}' is not a valid plugin, please use the -l option to see"
                    "available plugin names and codes".format(code)
                )
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
        exec_log = self.exec_registry[config_handler.target]
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
        return self.exec_registry[config_handler.target][self.get_last_plugin_exec(plugin):]

    def get_plugin_output_dir(self, plugin):
        """Get plugin directory by test type

        :param plugin: Plugin
        :type plugin: `dict`
        :return: Path to the plugin's output dir
        :rtype: `str`
        """
        # Organise results by OWASP Test type and then active, passive, semi_passive
        if plugin["group"] in ["web", "network"]:
            return os.path.join(
                target_manager.get_path("partial_url_output_path"), wipe_bad_chars(plugin["title"]), plugin["type"]
            )
        elif plugin["group"] == "auxiliary":
            return os.path.join(AUX_OUTPUT_PATH, wipe_bad_chars(plugin["title"]), plugin["type"])

    def requests_possible(self):
        """Check if requests are possible
        .. note::

             Even passive plugins will make requests to external resources

        :return:
        :rtype: `bool`
        """
        return ["grep"] != get_types_for_plugin_group(self.session, "web")

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
            return os.path.relpath(abs_path, get_output_dir_target())
        return abs_path

    def get_abs_path(self, relative_path):
        """Absolute path from relative path

        :param relative_path: Relative path
        :type relative_path: `str`
        :return: The absolute path
        :rtype: `str`
        """
        return os.path.join(get_output_dir_target(), relative_path)

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
        f, filename, desc = imp.find_module(module_file.split(".")[0], [module_path])
        return imp.load_module(module_name, f, filename, desc)

    def chosen_plugin(self, session, plugin, show_reason=False):
        """Verify that the plugin has been chosen by the user.

        :param dict plugin: The plugin dictionary with all the information.
        :param bool show_reason: If the plugin cannot be run, print the reason.

        :return: True if the plugin has been chosen, False otherwise.
        :rtype: bool

        """
        chosen = True
        reason = "not-specified"
        if plugin["group"] == self.plugin_group:
            # Skip plugins not present in the white-list defined by the user.
            if self.only_plugins_list and plugin["code"] not in self.only_plugins_list:
                chosen = False
                reason = "not in white-list"
            # Skip plugins present in the black-list defined by the user.
            if self.except_plugins_list and plugin["code"] in self.except_plugins_list:
                chosen = False
                reason = "in black-list"
        if plugin["type"] not in get_types_for_plugin_group(session=session, plugin_group=plugin["group"]):
            chosen = False  # Skip plugin: Not matching selected type
            reason = "not matching selected type"
        if not chosen and show_reason:
            logging.warning(
                "Plugin: %s (%s/%s) has not been chosen by the user (%s), skipping...",
                plugin["title"],
                plugin["group"],
                plugin["type"],
                reason,
            )
        return chosen

    def can_plugin_run(self, session, plugin, show_reason=False):
        """Verify that a plugin can be run by OWTF.

        :param dict plugin: The plugin dictionary with all the information.
        :param bool show_reason: If the plugin cannot be run, print the reason.

        :return: True if the plugin can be run, False otherwise.
        :rtype: bool

        """
        from owtf.managers.poutput import plugin_already_run

        if not self.chosen_plugin(session=session, plugin=plugin, show_reason=show_reason):
            return False  # Skip not chosen plugins
        # Grep plugins to be always run and overwritten (they run once after semi_passive and then again after active)
        if (
            plugin_already_run(session=session, plugin_info=plugin)
            and ((not self.force_overwrite and not ("grep" == plugin["type"])) or plugin["type"] == "external")
        ):
            if show_reason:
                logging.warning(
                    "Plugin: %s (%s/%s) has already been run, skipping...",
                    plugin["title"],
                    plugin["group"],
                    plugin["type"],
                )
            return False
        if "grep" == plugin["type"] and plugin_already_run(session=session, plugin_info=plugin):
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
        return "{0}/{1}/{2}".format(plugin_dir, plugin["type"], plugin["file"])  # Path to run the plugin

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
                    output["output"].get("ModifiedCommand", "").split(" ")[3],
                    os.path.basename(output["output"].get("RelativeFilePath", "")),
                )
                for output in cmd
                if ("output" in output and "metasploit" in output["output"].get("ModifiedCommand", ""))
            ]

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
            logging.error("Unexpected exception when running PTP: %s", str(e))
        if owtf_rank == UNKNOWN:  # Ugly truth... PTP gives 0 for unranked but OWTF uses -1 instead...
            owtf_rank = -1
        return owtf_rank

    def process_plugin(self, session, plugin_dir, plugin, status=None):
        """Process a plugin from running to ranking.

        :param `Session` session: SQLAlchemy session
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
        if not self.can_plugin_run(session=session, plugin=plugin, show_reason=True):
            return None
        # Save how long it takes for the plugin to run.
        self.timer.start_timer("Plugin")
        plugin["start"] = self.timer.get_start_date_time("Plugin")
        # Use relative path from targets folders while saving
        plugin["output_path"] = os.path.relpath(self.get_plugin_output_dir(plugin), get_output_dir_target())
        status["AllSkipped"] = False  # A plugin is going to be run.
        plugin["status"] = "Running"
        self.plugin_count += 1
        logging.info(
            "_" * 10 + " %d - Target: %s -> Plugin: %s (%s/%s) " + "_" * 10,
            self.plugin_count,
            target_manager.get_target_url(),
            plugin["title"],
            plugin["group"],
            plugin["type"],
        )
        # Skip processing in simulation mode, but show until line above
        # to illustrate what will run
        if self.simulation:
            return None
        # DB empty => grep plugins will fail, skip!!
        if "grep" == plugin["type"] and num_transactions(session) == 0:
            logging.info("Skipped - Cannot run grep plugins: The Transaction DB is empty")
            return None
        output = None
        status_msg = ""
        partial_output = []
        abort_reason = ""
        try:
            output = self.run_plugin(plugin_dir, plugin)
            status_msg = "Successful"
            status["SomeSuccessful"] = True
        except KeyboardInterrupt:
            # Just explain why crashed.
            status_msg = "Aborted"
            abort_reason = "Aborted by User"
            status["SomeAborted (Keyboard Interrupt)"] = True
        except SystemExit:
            # Abort plugin processing and get out to external exception
            # handling, information saved elsewhere.
            raise SystemExit
        except PluginAbortException as PartialOutput:
            status_msg = "Aborted (by user)"
            partial_output = PartialOutput.parameter
            abort_reason = "Aborted by User"
            status["SomeAborted"] = True
        except UnreachableTargetException as PartialOutput:
            status_msg = "Unreachable Target"
            partial_output = PartialOutput.parameter
            abort_reason = "Unreachable Target"
            status["SomeAborted"] = True
        except FrameworkAbortException as PartialOutput:
            status_msg = "Aborted (Framework Exit)"
            partial_output = PartialOutput.parameter
            abort_reason = "Framework Aborted"
        # TODO: Handle this gracefully
        # Replace print by logging
        finally:
            plugin["status"] = status_msg
            plugin["end"] = self.timer.get_end_date_time("Plugin")
            plugin["owtf_rank"] = self.rank_plugin(output, self.get_plugin_output_dir(plugin))
            try:
                if status_msg == "Successful":
                    save_plugin_output(session=session, plugin=plugin, output=output)
                else:
                    save_partial_output(session=session, plugin=plugin, output=partial_output, message=abort_reason)
            except SQLAlchemyError as e:
                logging.error("Exception occurred while during database transaction : \n%s", str(e))
                output += str(e)
            if status_msg == "Aborted":
                user_abort("Plugin")
            if abort_reason == "Framework Aborted":
                abort_framework("Framework abort")
        return output

    def process_plugin_list(self):
        """Process plugins

        :return:
        :rtype:
        """
        status = {"SomeAborted": False, "SomeSuccessful": False, "AllSkipped": True}
        if self.plugin_group in ["web", "auxiliary", "network"]:
            self.process_plugins_for_target_list(self.session, self.plugin_group, status, target_manager.get_all("ID"))
        return status

    def get_plugin_group_dir(self, plugin_group):
        """Get directory for plugin group

        :param plugin_group: Plugin group
        :type plugin_group: `str`
        :return: Path to the output dir for plugin group
        :rtype: `str`
        """
        return "{}/{}".format(PLUGINS_DIR, plugin_group)

    # TODO(viyatb): Make this run for normal plugin runs
    # This is not called anywhere - why? Seems it was always broken.
    def process_plugins_for_target_list(self, session, plugin_group, status, target_list):
        """Process plugins for all targets in the list
        :param plugin_group: Plugin group
        :type plugin_group: `str`
        :param status: Plugin exec status
        :type status: `dict`
        :param target_list: List of targets
        :type target_list: `set`
        :return: None
        :rtype: None
        """
        plugin_dir = self.get_plugin_group_dir(plugin_group)
        if plugin_group == "network":
            waves = self.portwaves.split(",")
            waves.append("-1")
            lastwave = 0
            for target in target_list:  # For each Target
                self.scanner.scan_network(target)
                # Scanning and processing the first part of the ports
                for i in range(1):
                    ports = config_handler.get_tcp_ports(lastwave, waves[i])
                    logging.info("Probing for ports %s", str(ports))
                    http = self.scanner.probe_network(target, "tcp", ports)
                    # Tell Config that all Gets/Sets are now target-specific.
                    target_manager.set_target(target)
                    for plugin in plugin_group:
                        self.process_plugin(session=session, plugin_dir=plugin_dir, plugin=plugin, status=status)
                    lastwave = waves[i]
                    for http_ports in http:
                        if http_ports == "443":
                            self.process_plugins_for_target_list(
                                session,
                                "web",
                                {"SomeAborted": False, "SomeSuccessful": False, "AllSkipped": True},
                                {"https://{}".format(target.split("//")[1])},
                            )
                        else:
                            self.process_plugins_for_target_list(
                                session,
                                "web",
                                {"SomeAborted": False, "SomeSuccessful": False, "AllSkipped": True},
                                {target},
                            )
        else:
            pass


def show_plugin_list(session, group, msg=INTRO_BANNER_GENERAL):
    """Show available plugins

    :param group: Plugin group
    :type group: `str`
    :param msg: Message to print
    :type msg: `str`
    :return: None
    :rtype: None
    """
    if group == "web":
        logging.info("%s%s\nAvailable WEB plugins:", msg, INTRO_BANNER_WEB_PLUGIN_TYPE)
    elif group == "auxiliary":
        logging.info("%s\nAvailable AUXILIARY plugins:", msg)
    elif group == "network":
        logging.info("%s\nAvailable NETWORK plugins:", msg)
    for plugin_type in get_types_for_plugin_group(session, group):
        show_plugin_types(session, plugin_type, group)


def show_plugin_types(session, plugin_type, group):
    """Show all plugin types

    :param plugin_type: Plugin type
    :type plugin_type: `str`
    :param group: Plugin group
    :type group: `str`
    :return: None
    :rtype: None
    """
    logging.info("\n%s %s plugins %s", "*" * 40, plugin_type.title().replace("_", "-"), "*" * 40)
    for plugin in get_plugins_by_group_type(session, group, plugin_type):
        line_start = " {!s}:{!s}".format(plugin["type"], plugin["name"])
        pad1 = "_" * (60 - len(line_start))
        pad2 = "_" * (20 - len(plugin["code"]))
        logging.info("%s%s(%s)%s%s", line_start, pad1, plugin["code"], pad2, plugin["descrip"])


runner = PluginRunner()
