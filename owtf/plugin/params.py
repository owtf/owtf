"""
owtf.plugin.params
~~~~~~~~~~~~~~~~~~

Manage parameters to the plugins
"""
import logging
from collections import defaultdict
import copy

from owtf.config import config_handler
from owtf.db.session import get_scoped_session
from owtf.models.error import Error
from owtf.utils.error import abort_framework
from owtf.utils.signals import owtf_start
from owtf.utils.strings import merge_dicts

__all__ = ["plugin_params"]


class PluginParams(object):

    def __init__(self):
        # Complicated stuff to keep everything Pythonic and from blowing up
        def handle_signal(sender, **kwargs):
            self.on_start(sender, **kwargs)

        self.handle_signal = handle_signal
        owtf_start.connect(handle_signal)

        self.raw_args = None
        self.init = False
        self.no_args = []
        self.session = get_scoped_session()

    def on_start(self, sender, **kwargs):
        self.raw_args = copy.deepcopy(kwargs["args"]["args"])

    def process_args(self):
        """Process args

        :return: True if run is successful
        :rtype: `bool`
        """
        self.args = defaultdict(list)
        for arg in self.raw_args:
            if "O" == arg:
                continue
            chunks = arg.split("=")
            if len(chunks) < 2:
                Error.add_error(
                    self.session,
                    "USER ERROR: {!s} arguments should be in NAME=VALUE format".format(str(chunks)),
                    "user",
                )
                return False
            arg_name = chunks[0]
            try:
                arg_val = arg.replace(arg_name, "")[1:]
            except ValueError:
                Error.add_error(
                    self.session, "USER ERROR: {!s} arguments should be in NAME=VALUE format".format(arg_name), "user"
                )
                return False
            self.args[arg_name] = arg_val
        return True

    def list_args(self, args, mandatory=True):
        """List of available arguments

        :param args: args
        :type args: `dict`
        :param mandatory: True/false if mandatory to set
        :type mandatory: `bool`
        :return: None
        :rtype: None
        """
        logging.info("")  # Newline
        if mandatory:
            logging.info("mandatory parameters:")
        else:
            logging.info("Optional parameters:")
        for arg_name, arg_description in list(args.items()):
            if arg_description is None:
                arg_description = ""
            logging.info("- %s%s%s", arg_name, (30 - len(arg_name)) * "_", arg_description.replace("\n", "\n"))

    def get_args_example(self, full_args_list):
        """Arguments for an example plugin

        :param full_args_list: Full list of args
        :type full_args_list: `dict`
        :return: Padded example
        :rtype: `str`
        """
        args_str = []
        for key, value in list(merge_dicts(full_args_list["mandatory"], full_args_list["Optional"]).items()):
            args_str.append(key)
        pad = "=? "
        return pad.join(args_str) + pad

    def show_param_info(self, full_args_list, plugin):
        """Show parameter info for a plugin

        :param full_args_list: Full args list
        :type full_args_list: `dict`
        :param plugin: Plugin
        :type plugin: `dict`
        :return: None
        :rtype: None
        """
        logging.info("\nInformation for %s", self.show_plugin(plugin))
        logging.info("\nDescription: %s", str(full_args_list["Description"]))
        self.list_args(full_args_list["mandatory"], True)
        if len(full_args_list["Optional"]) > 0:
            self.list_args(full_args_list["Optional"], False)
        logging.info("\nUsage: %s\n", self.get_args_example(full_args_list))
        abort_framework("User is only viewing options, exiting")

    def show_plugin(self, plugin):
        """Show plugin info

        :param plugin: Plugin dict
        :type plugin: `dict`
        :return: Formatted plugin string
        :rtype: `str`
        """
        return "plugin: {0}/{1}".format(plugin["type"], plugin["file"])

    def default_arg_from_config(self, args, arg_name, settings_list):
        """Get default args from config

        :param args: args list
        :type args: `dict`
        :param arg_name: Name of arg to fetch
        :type arg_name: `str`
        :param settings_list: List of settings
        :type settings_list: `list`
        :return: True if run is successful
        :rtype: `bool`
        """
        default_order_str = " (Default order is: {!s})".format(settings_list)
        for setting in settings_list:
            if config_handler.is_set(setting):  # argument is set in config
                args[arg_name] = config_handler.get_val(setting)
                logging.info("default not passed '%s' to '%s'%s", arg_name, str(args[arg_name]), default_order_str)
                return True
        logging.info("Could not default not passed: '%s'%s", arg_name, default_order_str)
        return False

    def get_arg_list(self, session, arg_list, plugin, mandatory=True):
        """Get args list

        :param arg_list: available args
        :type arg_list: `dict`
        :param plugin: Plugin info
        :type plugin: `dict`
        :param mandatory: Mandatory to list?
        :type mandatory: `bool`
        :return: available args for plugins
        :rtype: `dict`
        """
        if not self.init:
            self.init = True
            if not self.process_args():  # Process Passed arguments the first time only
                return self.ret_arg_error({}, plugin)  # Abort processing (invalid data)
        args = {}
        for arg_name in arg_list:
            if arg_name not in self.args:
                config_default_order = [
                    "{0}_{1}_{2}".format(plugin["code"], plugin["type"], arg_name),
                    "{0}_{1}".format(plugin["code"], arg_name),
                    arg_name,
                ]
                default = self.default_arg_from_config(args, arg_name, config_default_order)
                if default or mandatory is False:
                    # The Parameter has been defaulted, must skip loop to avoid assignment at the bottom or
                    # argument is optional = ok to skip
                    continue
                Error.add_error(
                    session,
                    "USER ERROR: {!s} requires argument: '{!s}'".format(self.show_plugin(plugin), arg_name),
                    "user",
                )
                return self.ret_arg_error({}, plugin)  # Abort processing (invalid data)
            args[arg_name] = self.args[arg_name]
        return args

    def get_arg_error(self, plugin):
        """Set arg error

        :param plugin: Plugin dict
        :type plugin: `dict`
        :return: Argument error for a plugin
        :rtype: `bool`
        """
        return plugin["argError"]

    def set_arg_error(self, plugin, error=True):
        """Set arg error for a plugin

        :param plugin: Plugin dict
        :type plugin: `dict`
        :param error: Error or not
        :type error: `bool`
        :return: None
        :rtype: None
        """
        plugin["argError"] = error

    def ret_arg_error(self, return_val, plugin):
        """Returns the arg error for a plugin

        :param return_val: The return value
        :type return_val: `bools`
        :param plugin: Plugin dict
        :type plugin: `dict`
        :return: return val
        :rtype: `str`
        """
        self.set_arg_error(plugin, True)
        return return_val

    def check_arg_list(self, full_args_list, plugin):
        """Check args list for a plugin

        :param full_args_list: Full args list
        :type full_args_list: `dict`
        :param plugin: Plugin dict
        :type plugin: `dict`
        :return: True if run successful
        :rtype: `bool`
        """
        if "Mandatory" not in full_args_list or "Optional" not in full_args_list:
            Error.add_error(
                self.session,
                "OWTF PLUGIN BUG: {!s} requires declared Mandatory and Optional arguments".format(
                    self.show_plugin(plugin)
                ),
                trace="",
            )
            return self.ret_arg_error(True, plugin)
        if "Description" not in full_args_list:
            Error.add_error(
                self.session, "OWTF PLUGIN BUG: {!s}  requires a Description".format(self.show_plugin(plugin)), trace=""
            )
            return self.ret_arg_error(False, plugin)
        return True

    def set_args_basic(self, all_args, plugin):
        """Set basic required args

        :param all_args: All available args
        :type all_args: `dict`
        :param plugin: Plugin dict
        :type plugin: `dict`
        :return: Replaced args list
        :rtype: `list`
        """
        if not all_args:
            return self.no_args
        args_str = []
        for arg_name, arg_val in list(all_args.items()):
            args_str.append(arg_name + "=" + str(self.args[arg_name]))
            all_args[arg_name] = arg_val
        plugin["args"] = " ".join(args_str)  # Record arguments in plugin dictionary
        return [all_args]

    def set_config(self, args):
        """Set config for args

        :param args: args to override
        :type args: `dict`
        :return: None
        :rtype: None
        """
        for arg_name, arg_val in list(args.items()):
            logging.info("Overriding configuration setting '_%s' with value %s..", arg_name, str(arg_val))
            config_handler.set_general_val(
                "string", "_{!s}".format(arg_name), arg_val
            )  # Pre-pend "_" to avoid naming collisions

    def get_permutations(self, args):
        """Get permutations from args

        :param args: Available args
        :type args: `dict`
        :return: List of permutations
        :rtype: `defaultdict`
        """
        permutations = defaultdict(list)
        if "REPEAT_DELIM" not in args:
            return permutations  # No permutations
        separator = args["REPEAT_DELIM"]
        for arg_name, arg_val in list(args.items()):
            if arg_name == "REPEAT_DELIM":
                continue  # The repeat delimiter is not considered a permutation: It's the permutation delimiter :)
            chunks = arg_val.split(separator)
            if len(chunks) > 1:
                permutations[arg_name] = chunks
        return permutations

    def set_permutation(self, arg_name, permutations, permutation_list):
        """Add a particular permutation for an arg

        :param arg_name: Arg to replace
        :type arg_name: `str`
        :param permutations: List of permutations
        :type permutations: `list`
        :param permutation_list: Permutation list
        :type permutation_list: `list`
        :return: None
        :rtype: None
        """
        for index, permutation in enumerate(permutation_list):
            count = 0
            for perm in permutations:
                perm_args = permutation_list[index].copy()  # 1st copy by value original arguments
                perm_args[arg_name] = perm  # 2nd override argument with permutation
                if count == 0:  # Modify 1st existing record with permutation
                    permutation_list[index] = perm_args
                else:
                    # 3rd store each subsequent permutation as a different set of args
                    permutation_list.append(perm_args)
                count += 1

    def set_args(self, all_args, plugin):
        """Set args from all args for a plugin

        :param all_args: All available args
        :type all_args: `dict`
        :param plugin: Plugin
        :type plugin: `dict`
        :return: List of permutations
        :rtype: `list`
        """
        arg_list = self.set_args_basic(all_args, plugin)
        if not arg_list:
            return arg_list  # Nothing to do
        args = arg_list[0]
        permutation_list = [args]
        for arg_name, permutations in list(self.get_permutations(args).items()):
            self.set_permutation(arg_name, permutations, permutation_list)
        if not permutation_list:
            return arg_list  # No permutations, return original arguments
        return permutation_list

    def get_args(self, session, full_args_list, plugin):
        """Get args from a full list for a plugin

        :param full_args_list: available args
        :type full_args_list: `dict`
        :param plugin: Plugin
        :type plugin: `dict`
        :return: None
        :rtype: None
        """
        self.set_arg_error(plugin, False)
        if not self.check_arg_list(full_args_list, plugin):
            return self.no_args
        if "O" in self.raw_args:  # To view available options
            self.show_param_info(full_args_list, plugin)
            return self.no_args  # Abort processing, just showing options
        mandatory = self.get_arg_list(session, full_args_list["Mandatory"], plugin, True)
        optional = self.get_arg_list(session, full_args_list["Optional"], plugin, False)
        if self.get_arg_error(plugin):
            logging.info("")
            logging.warn("ERROR: Aborting argument processing, please correct the errors above and try again")
            logging.info("")
            return self.no_args  # Error processing arguments, must abort processing
        all_args = merge_dicts(mandatory, optional)
        return self.set_args(all_args, plugin)


plugin_params = PluginParams()
