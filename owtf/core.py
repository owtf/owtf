"""
owtf.cli

This is the command-line front-end in charge of processing arguments and call the framework.
"""

from __future__ import print_function

import os
import sys
import logging
from copy import deepcopy

from owtf.api.main import start_api_server
from owtf.cli.main import start_cli
from owtf.config import config_handler
from owtf.filesrv.main import start_file_server
from owtf.lib import exceptions
from owtf.lib.cli_options import usage, parse_options
from owtf import db
from owtf.managers.config import load_config_db_file, load_framework_config_file
from owtf.managers.resource import load_resources_from_file
from owtf.managers.mapping import load_mappings_from_file
from owtf.managers.plugin import get_groups_for_plugins, get_all_plugin_types, get_all_plugin_groups, \
    get_types_for_plugin_group, load_test_groups, load_plugins
from owtf.managers.session import _ensure_default_session
from owtf.managers.target import load_targets
from owtf.managers.worklist import load_works
from owtf.plugin.plugin_handler import show_plugin_list, plugin_handler
from owtf.proxy.main import start_proxy
from owtf.settings import WEB_TEST_GROUPS, AUX_TEST_GROUPS, NET_TEST_GROUPS, DEFAULT_RESOURCES_PROFILE, \
    FALLBACK_RESOURCES_PROFILE, FALLBACK_AUX_TEST_GROUPS, FALLBACK_NET_TEST_GROUPS, FALLBACK_WEB_TEST_GROUPS, \
    FALLBACK_MAPPING_PROFILE, DEFAULT_MAPPING_PROFILE, DEFAULT_FRAMEWORK_CONFIG, FALLBACK_FRAMEWORK_CONFIG, \
    DEFAULT_GENERAL_PROFILE, FALLBACK_GENERAL_PROFILE, SERVER_ADDR, UI_SERVER_PORT, CLI
from owtf.utils.file import clean_temp_storage_dirs, create_temp_storage_dirs
from owtf.utils.process import kill_children


owtf_pid = None


def banner():
    """Prints a figlet type banner"""



def get_plugins_from_arg(arg):
    """ Returns a list of requested plugins and plugin groups

    :param arg: Comma separated list of plugins
    :type arg: `str`
    :return: List of plugins and plugin groups
    :rtype: `list`
    """
    plugins = arg.split(',')
    plugin_groups = get_groups_for_plugins(db, plugins)
    if len(plugin_groups) > 1:
        usage("The plugins specified belong to several plugin groups: '%s'".format(str(plugin_groups)))
    return [plugins, plugin_groups]


def process_options(user_args):
    """ The main argument processing function

    :param user_args: User supplied arguments
    :type user_args: `dict`
    :return: A dictionary of arguments
    :rtype: `dict`
    """
    try:
        valid_groups = get_all_plugin_groups(db)
        valid_types = get_all_plugin_types(db) + ['all', 'quiet']
        arg = parse_options(user_args, valid_groups, valid_types)
    except KeyboardInterrupt as e:
        usage("Invalid OWTF option(s) %s" % e)
        sys.exit(0)

    # Default settings:
    plugin_group = arg.PluginGroup

    if arg.OnlyPlugins:
        arg.OnlyPlugins, plugin_groups = get_plugins_from_arg(arg.OnlyPlugins)
        try:
            # Set Plugin Group according to plugin list specified
            plugin_group = plugin_groups[0]
        except IndexError:
            usage("Please use either OWASP/OWTF codes or Plugin names")
        logging.info("Defaulting Plugin Group to '%s' based on list of plugins supplied" % plugin_group)

    if arg.ExceptPlugins:
        arg.ExceptPlugins, plugin_groups = get_plugins_from_arg(arg.ExceptPlugins)

    if arg.TOR_mode:
        arg.TOR_mode = arg.TOR_mode.split(":")
        if(arg.TOR_mode[0] == "help"):
            from owtf.proxy.tor_manager import TOR_manager
            TOR_manager.msg_configure_tor()
            exit(0)
        if len(arg.TOR_mode) == 1:
            if arg.TOR_mode[0] != "help":
                usage("Invalid argument for TOR-mode")
        elif len(arg.TOR_mode) != 5:
            usage("Invalid argument for TOR-mode")
        else:
            # Enables OutboundProxy.
            if arg.TOR_mode[0] == '':
                outbound_proxy_ip = "127.0.0.1"
            else:
                outbound_proxy_ip = arg.TOR_mode[0]
            if arg.TOR_mode[1] == '':
                outbound_proxy_port = "9050"  # default TOR port
            else:
                outbound_proxy_port = arg.TOR_mode[1]
            arg.OutboundProxy = "socks://{0}:{1}".format(outbound_proxy_ip, outbound_proxy_port)

    if arg.OutboundProxy:
        arg.OutboundProxy = arg.OutboundProxy.split('://')
        if len(arg.OutboundProxy) == 2:
            arg.OutboundProxy = arg.OutboundProxy + arg.OutboundProxy.pop().split(':')
            if arg.OutboundProxy[0] not in ["socks", "http"]:
                usage("Invalid argument for Outbound Proxy")
        else:
            arg.OutboundProxy = arg.OutboundProxy.pop().split(':')
        # OutboundProxy should be type://ip:port
        if (len(arg.OutboundProxy) not in [2, 3]):
            usage("Invalid argument for Outbound Proxy")
        else:  # Check if the port is an int.
            try:
                int(arg.OutboundProxy[-1])
            except ValueError:
                usage("Invalid port provided for Outbound Proxy")

    if arg.InboundProxy:
        arg.InboundProxy = arg.InboundProxy.split(':')
        # InboundProxy should be (ip:)port:
        if len(arg.InboundProxy) not in [1, 2]:
            usage("Invalid argument for Inbound Proxy")
        else:
            try:
                int(arg.InboundProxy[-1])
            except ValueError:
                usage("Invalid port for Inbound Proxy")

    plugin_types_for_group = get_types_for_plugin_group(db, plugin_group)
    if arg.PluginType == 'all':
        arg.PluginType = plugin_types_for_group
    elif arg.PluginType == 'quiet':
        arg.PluginType = ['passive', 'semi_passive']

    scope = arg.Targets or []  # Arguments at the end are the URL target(s)
    num_targets = len(scope)
    if plugin_group != 'auxiliary' and num_targets == 0 and not arg.list_plugins:
        # TODO: Fix this
        pass
    elif num_targets == 1:  # Check if this is a file
        if os.path.isfile(scope[0]):
            logging.info("Scope file: trying to load targets from it ..")
            new_scope = []
            for target in open(scope[0]).read().split("\n"):
                CleanTarget = target.strip()
                if not CleanTarget:
                    continue  # Skip blank lines
                new_scope.append(CleanTarget)
            if len(new_scope) == 0:  # Bad file
                usage("Please provide a scope file (1 target x line)")
            scope = new_scope

    for target in scope:
        if target[0] == "-":
            usage("Invalid Target: " + target)

    args = ''
    if plugin_group == 'auxiliary':
        # For auxiliary plugins, the scope are the parameters.
        args = scope
        # auxiliary plugins do not have targets, they have metasploit-like parameters.
        scope = ['auxiliary']

    return {
        'list_plugins': arg.list_plugins,
        'Force_Overwrite': arg.ForceOverwrite,
        'Interactive': arg.Interactive == 'yes',
        'Scope': scope,
        'argv': sys.argv,
        'PluginType': arg.PluginType,
        'OnlyPlugins': arg.OnlyPlugins,
        'ExceptPlugins': arg.ExceptPlugins,
        'InboundProxy': arg.InboundProxy,
        'OutboundProxy': arg.OutboundProxy,
        'OutboundProxyAuth': arg.OutboundProxyAuth,
        'PluginGroup': plugin_group,
        'RPort': arg.RPort,
        'PortWaves': arg.PortWaves,
        'ProxyMode': arg.ProxyMode,
        'TOR_mode': arg.TOR_mode,
        'nowebui': arg.nowebui,
        'Args': args
    }


def initialise_framework(options):
    """This function initializes the entire framework

    :param options: Additional arguments for the component initializer
    :type options: `dict`
    :return: True if all commands do not fail
    :rtype: `bool`
    """
    logging.info("Loading framework please wait..")
    # No processing required, just list available modules.
    if options['list_plugins']:
        show_plugin_list(db, options['list_plugins'])
        finish(owtf_pid)
    target_urls = load_targets(session=db, options=options)
    load_works(session=db, target_urls=target_urls, options=options)
    start_proxy()
    return True


def patch_obj_args(args):
    setattr(plugin_handler, "options", args)
    setattr(plugin_handler, "simulation", args.get('Simulation', None))
    setattr(plugin_handler, "scope", args['Scope'])
    setattr(plugin_handler, "plugin_group", args['PluginGroup'])
    setattr(plugin_handler, "only_plugins", args['OnlyPlugins'])
    setattr(plugin_handler, "except_plugins", args['ExceptPlugins'])
    add_plugin_list = getattr(plugin_handler, "validate_format_plugin_list")
    setattr(plugin_handler, "only_plugins_list", add_plugin_list(session=db, plugin_codes=args['OnlyPlugins']))
    setattr(plugin_handler, "except_plugins_list", add_plugin_list(session=db, plugin_codes=args['OnlyPlugins']))
    exec_registry = getattr(plugin_handler, "init_exec_registry")
    exec_registry()


def x(args):
    """Start OWTF.
    :params dict args: Options from the CLI.
    """
    if initialise_framework(args):
        if not args['nowebui']:
            start_api_server()
            logging.warn("http://{}:{} <-- Web UI URL".format(SERVER_ADDR, str(UI_SERVER_PORT)))
            start_file_server()
        else:
            start_cli()


def finish(owtf_pid):
    kill_children(owtf_pid)


def main(args):
    """ The main wrapper which loads everything

    :param args: User supplied arguments dictionary
    :type args: `dict`
    :return:
    :rtype: None
    """
    banner()
    # Get tool path from script path:
    root_dir = os.path.dirname(os.path.abspath(args[0])) or '.'
    owtf_pid = os.getpid()
    create_temp_storage_dirs(owtf_pid)
    try:
        _ensure_default_session(db)
        load_framework_config_file(DEFAULT_FRAMEWORK_CONFIG, FALLBACK_FRAMEWORK_CONFIG, root_dir, owtf_pid)
        load_config_db_file(db, DEFAULT_GENERAL_PROFILE, FALLBACK_GENERAL_PROFILE)
        load_resources_from_file(db, DEFAULT_RESOURCES_PROFILE, FALLBACK_RESOURCES_PROFILE)
        load_mappings_from_file(db, DEFAULT_MAPPING_PROFILE, FALLBACK_MAPPING_PROFILE)
        load_test_groups(db, WEB_TEST_GROUPS, FALLBACK_WEB_TEST_GROUPS, "web")
        load_test_groups(db, NET_TEST_GROUPS, FALLBACK_NET_TEST_GROUPS, "net")
        load_test_groups(db, AUX_TEST_GROUPS, FALLBACK_AUX_TEST_GROUPS, "aux")
        # After loading the test groups then load the plugins, because of many-to-one relationship
        load_plugins(db)
    except exceptions.DatabaseNotRunningException:
        sys.exit(-1)

    args = process_options(args[1:])
    cli_env = os.environ.get('CLI', None)
    if cli_env:
        args["nowebui"] = cli_env
    config_handler.cli_options = deepcopy(args)

    # Patch args
    patch_obj_args(args)

    # Initialise Framework.
    try:
        if x(args):
            # Only if Start is for real (i.e. not just listing plugins, etc)
            sys.exit(0)  # Not Interrupted or Crashed.
    except KeyboardInterrupt:
        # NOTE: The user chose to interact: interactivity check redundant here:
        logging.warning("OWTF was aborted by the user:")
        logging.info("Please check report/plugin output files for partial results")
        # Interrupted. Must save the DB to disk, finish report, etc.
        sys.exit(-1)
    except SystemExit:
        pass  # Report already saved, framework tries to exit.
    finally:  # Needed to rename the temp storage dirs to avoid confusion.
        clean_temp_storage_dirs(owtf_pid)
