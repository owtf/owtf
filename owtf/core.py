"""
owtf.core
~~~~~~~~~

This is the command-line front-end in charge of processing arguments and call the framework.
"""
from __future__ import print_function

from copy import deepcopy
import logging
import os
import signal
import sys

from tornado.ioloop import IOLoop, PeriodicCallback

from owtf import __version__
from owtf.api.main import start_server
from owtf.config import config_handler
from owtf.files.main import start_file_server
from owtf.lib import exceptions
from owtf.lib.cli_options import parse_options, usage
from owtf.managers.config import load_framework_config, load_general_config
from owtf.managers.plugin import (
    get_types_for_plugin_group,
    load_plugins,
    load_test_groups,
)
from owtf.managers.resource import load_resources_from_file
from owtf.managers.session import _ensure_default_session
from owtf.managers.target import load_targets
from owtf.managers.worklist import load_works
from owtf.models.plugin import Plugin
from owtf.plugin.runner import show_plugin_list
from owtf.proxy.main import start_proxy
from owtf.settings import (
    AUX_TEST_GROUPS,
    DEFAULT_FRAMEWORK_CONFIG,
    DEFAULT_GENERAL_PROFILE,
    DEFAULT_RESOURCES_PROFILE,
    FALLBACK_AUX_TEST_GROUPS,
    FALLBACK_FRAMEWORK_CONFIG,
    FALLBACK_GENERAL_PROFILE,
    FALLBACK_NET_TEST_GROUPS,
    FALLBACK_RESOURCES_PROFILE,
    FALLBACK_WEB_TEST_GROUPS,
    NET_TEST_GROUPS,
    WEB_TEST_GROUPS,
)
from owtf.transactions.main import start_transaction_logger
from owtf.utils.file import clean_temp_storage_dirs, create_temp_storage_dirs
from owtf.utils.process import _signal_process
from owtf.utils.signals import workers_finish, owtf_start

__all__ = ["finish", "main"]

# Store parent PID for clean exit
owtf_pid = None

# Get a global DB connection instance
from owtf.db.session import get_scoped_session

db = get_scoped_session()


def print_banner():
    """
    Print the application banner.
    """
    print(
        """\033[92m
         _____ _ _ _ _____ _____
        |     | | | |_   _|   __|
        |  |  | | | | | | |   __|
        |_____|_____| |_| |__|

            @owtfp
        http://owtf.org
        Version: {0}
        \033[0m""".format(
            __version__
        )
    )


def get_plugins_from_arg(arg):
    """ Returns a list of requested plugins and plugin groups

    :param arg: Comma separated list of plugins
    :type arg: `str`
    :return: List of plugins and plugin groups
    :rtype: `list`
    """
    plugins = arg.split(",")
    plugin_groups = Plugin.get_groups_for_plugins(db, plugins)
    if len(plugin_groups) > 1:
        usage(
            "The plugins specified belong to several plugin groups: '%s'".format(
                str(plugin_groups)
            )
        )
    return [plugins, plugin_groups]


def process_options(user_args):
    """ The main argument processing function

    :param user_args: User supplied arguments
    :type user_args: `dict`
    :return: A dictionary of arguments
    :rtype: `dict`
    """
    arg = None
    try:
        valid_groups = Plugin.get_all_plugin_groups(db)
        valid_types = Plugin.get_all_plugin_types(db) + ["all", "quiet"]
        arg = parse_options(user_args, valid_groups, valid_types)
    except KeyboardInterrupt as e:
        usage("Invalid OWTF option(s) {}".format(e))
        sys.exit(0)
    except SystemExit:
        # --help triggers the SystemExit exception, catch it and exit
        finish()

    if arg:
        # Default settings:
        plugin_group = arg.plugin_group

        if arg.only_plugins:
            arg.only_plugins, plugin_groups = get_plugins_from_arg(arg.only_plugins)
            try:
                # Set Plugin Group according to plugin list specified
                plugin_group = plugin_groups[0]
            except IndexError:
                usage("Please use either OWASP/OWTF codes or Plugin names")
            logging.info(
                "Defaulting plugin group to '%s' based on list of plugins supplied",
                plugin_group,
            )

        if arg.except_plugins:
            arg.except_plugins, plugin_groups = get_plugins_from_arg(arg.except_plugins)

        if arg.tor_mode:
            arg.tor_mode = arg.tor_mode.split(":")
            if arg.tor_mode[0] == "help":
                from owtf.proxy.tor_manager import TOR_manager

                TOR_manager.msg_configure_tor()
                exit(0)
            if len(arg.tor_mode) == 1:
                if arg.tor_mode[0] != "help":
                    usage("Invalid argument for TOR-mode")
            elif len(arg.tor_mode) != 5:
                usage("Invalid argument for TOR-mode")
            else:
                # Enables outbound_proxy.
                if arg.tor_mode[0] == "":
                    outbound_proxy_ip = "127.0.0.1"
                else:
                    outbound_proxy_ip = arg.tor_mode[0]
                if arg.tor_mode[1] == "":
                    outbound_proxy_port = "9050"  # default TOR port
                else:
                    outbound_proxy_port = arg.tor_mode[1]
                arg.outbound_proxy = "socks://{0}:{1}".format(
                    outbound_proxy_ip, outbound_proxy_port
                )

        if arg.outbound_proxy:
            arg.outbound_proxy = arg.outbound_proxy.split("://")
            if len(arg.outbound_proxy) == 2:
                arg.outbound_proxy = arg.outbound_proxy + arg.outbound_proxy.pop().split(
                    ":"
                )
                if arg.outbound_proxy[0] not in ["socks", "http"]:
                    usage("Invalid argument for outbound proxy")
            else:
                arg.outbound_proxy = arg.outbound_proxy.pop().split(":")
            # outbound_proxy should be type://ip:port
            if len(arg.outbound_proxy) not in [2, 3]:
                usage("Invalid argument for outbound proxy")
            else:  # Check if the port is an int.
                try:
                    int(arg.outbound_proxy[-1])
                except ValueError:
                    usage("Invalid port provided for Outbound Proxy")

        if arg.inbound_proxy:
            arg.inbound_proxy = arg.inbound_proxy.split(":")
            # inbound_proxy should be (ip:)port:
            if len(arg.inbound_proxy) not in [1, 2]:
                usage("Invalid argument for Inbound Proxy")
            else:
                try:
                    int(arg.inbound_proxy[-1])
                except ValueError:
                    usage("Invalid port for Inbound Proxy")

        plugin_types_for_group = get_types_for_plugin_group(db, plugin_group)
        if arg.plugin_type == "all":
            arg.plugin_type = plugin_types_for_group
        elif arg.plugin_type == "quiet":
            arg.plugin_type = ["passive", "semi_passive"]

        scope = arg.targets or []  # Arguments at the end are the URL target(s)
        num_targets = len(scope)
        if plugin_group != "auxiliary" and num_targets == 0 and not arg.list_plugins:
            if arg.nowebui:
                finish()
        elif num_targets == 1:  # Check if this is a file
            if os.path.isfile(scope[0]):
                logging.info("Scope file: trying to load targets from it ..")
                new_scope = []
                for target in open(scope[0]).read().split("\n"):
                    clean_target = target.strip()
                    if not clean_target:
                        continue  # Skip blank lines
                    new_scope.append(clean_target)
                if len(new_scope) == 0:  # Bad file
                    usage("Please provide a scope file (1 target x line)")
                scope = new_scope

        for target in scope:
            if target[0] == "-":
                usage("Invalid Target: {}".format(target))

        args = ""
        if plugin_group == "auxiliary":
            # For auxiliary plugins, the scope are the parameters.
            args = scope
            # auxiliary plugins do not have targets, they have metasploit-like parameters.
            scope = ["auxiliary"]

        return {
            "list_plugins": arg.list_plugins,
            "force_overwrite": arg.force_overwrite,
            "interactive": arg.interactive == "yes",
            "scope": scope,
            "argv": sys.argv,
            "plugin_type": arg.plugin_type,
            "only_plugins": arg.only_plugins,
            "except_plugins": arg.except_plugins,
            "inbound_proxy": arg.inbound_proxy,
            "outbound_proxy": arg.outbound_proxy,
            "outbound_proxy_auth": arg.outbound_proxy_auth,
            "plugin_group": plugin_group,
            "rport": arg.rport,
            "port_waves": arg.port_waves,
            "proxy_mode": arg.proxy_mode,
            "tor_mode": arg.tor_mode,
            "nowebui": arg.nowebui,
            "args": args,
        }
    return {}


def initialise_framework(options):
    """This function initializes the entire framework

    :param options: Additional arguments for the component initializer
    :type options: `dict`
    :return: True if all commands do not fail
    :rtype: `bool`
    """
    logging.info("Loading framework please wait..")
    # No processing required, just list available modules.
    if options["list_plugins"]:
        show_plugin_list(db, options["list_plugins"])
        finish()
    target_urls = load_targets(session=db, options=options)
    load_works(session=db, target_urls=target_urls, options=options)
    start_proxy()
    start_transaction_logger()
    return True


def poll_workers():
    from owtf.managers.worker import worker_manager

    callback = PeriodicCallback(worker_manager.manage_workers, 2000)
    try:
        callback.start()
        IOLoop.instance().start()
    except SystemExit as e:
        callback.stop()


def init(args):
    """Start OWTF.
    :params dict args: Options from the CLI.
    """
    if initialise_framework(args):
        if not args["nowebui"]:
            start_server()
            start_file_server()

        poll_workers()


@workers_finish.connect
def finish(sender=None, **kwargs):
    if sender:
        logging.debug("[{}]: sent the signal".format(sender))
    global owtf_pid
    _signal_process(pid=owtf_pid, psignal=signal.SIGINT)


def main():
    """ The main wrapper which loads everything

    :return:
    :rtype: None
    """
    args = sys.argv
    print_banner()
    # Get tool path from script path:
    root_dir = os.path.dirname(os.path.abspath(args[0])) or "."
    global owtf_pid
    owtf_pid = os.getpid()

    # Bootstrap the DB
    create_temp_storage_dirs(owtf_pid)
    try:
        _ensure_default_session(db)
        load_framework_config(
            DEFAULT_FRAMEWORK_CONFIG, FALLBACK_FRAMEWORK_CONFIG, root_dir, owtf_pid
        )
        load_general_config(db, DEFAULT_GENERAL_PROFILE, FALLBACK_GENERAL_PROFILE)
        load_resources_from_file(
            db, DEFAULT_RESOURCES_PROFILE, FALLBACK_RESOURCES_PROFILE
        )
        load_test_groups(db, WEB_TEST_GROUPS, FALLBACK_WEB_TEST_GROUPS, "web")
        load_test_groups(db, NET_TEST_GROUPS, FALLBACK_NET_TEST_GROUPS, "net")
        load_test_groups(db, AUX_TEST_GROUPS, FALLBACK_AUX_TEST_GROUPS, "aux")
        # After loading the test groups then load the plugins, because of many-to-one relationship
        load_plugins(db)
    except exceptions.DatabaseNotRunningException:
        sys.exit(-1)

    args = process_options(args[1:])
    config_handler.cli_options = deepcopy(args)
    # Patch args by sending the OWTF start signal
    owtf_start.send(__name__, args=args)
    # Initialise Framework.
    try:
        if init(args):
            # Only if Start is for real (i.e. not just listing plugins, etc)
            finish()  # Not Interrupted or Crashed.
    except KeyboardInterrupt:
        # NOTE: The user chose to interact: interactivity check redundant here:
        logging.warning("OWTF was aborted by the user")
        logging.info("Please check report/plugin output files for partial results")
        # Interrupted. Must save the DB to disk, finish report, etc.
        finish()
    except SystemExit:
        pass  # Report already saved, framework tries to exit.
    finally:  # Needed to rename the temp storage dirs to avoid confusion.
        clean_temp_storage_dirs(owtf_pid)
