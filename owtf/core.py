"""
owtf.core
~~~~~~~~~

The core is the glue that holds the components together and allows some of them to
communicate with each other. Basically injects dependencies so that they can be used
across modules.
"""

import os
import sys
import socket
import logging
import multiprocessing
from copy import deepcopy
try: #PY3
    from urllib.parse import urlparse
except ImportError:  #PY2
     from urlparse import urlparse

import tornado

from owtf.config import config_handler
from owtf.lib.exceptions import UnresolvableTargetException, DBIntegrityException
from owtf.managers.target import add_target, get_target_config_dicts
from owtf.api import server
from owtf.proxy import proxy, transaction_logger
from owtf.settings import INBOUND_PROXY_IP, INBOUND_PROXY_PORT, INBOUND_PROXY_CACHE_DIR, PROXY_LOG, SERVER_ADDR, \
    UI_SERVER_PORT
from owtf.utils.error import abort_framework
from owtf.utils.file import catch_io_errors, FileOperations, get_logs_dir, get_log_path, create_temp_storage_dirs
from owtf.utils.formatters import FileFormatter, ConsoleFormatter
from owtf.utils.process import kill_children
from owtf.managers.worklist import add_work
from owtf.plugin.plugin_handler import plugin_handler
from owtf.managers.worker import worker_manager
from owtf.managers.plugin import get_all_plugin_dicts
from owtf.plugin.plugin_params import plugin_params


class Core(object):
    """Main entry point for OWTF that manages the OWTF components."""

    def __init__(self):
        """
        :return: instance of :class:`owtf.core.Core`
        :rtype::class:`owtf.core.Core`

        """
        self.file_handler = catch_io_errors(logging.FileHandler)
        self.owtf_pid = os.getppid()
        self.plugin_handler = plugin_handler
        self.worker_manager = worker_manager
        self.tor_process = None
        self.proxy_process = None
        FileOperations.create_missing_dirs(get_logs_dir())
        create_temp_storage_dirs(self.owtf_pid)
        self.enable_logging()

    def start_proxy(self, options):
        """ The proxy along with supporting processes are started here

        :param options: Optional arguments
        :type options: `dict`
        :return:
        :rtype: None
        """
        if True:
            # Check if port is in use
            try:
                temp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                temp_socket.bind((INBOUND_PROXY_IP, INBOUND_PROXY_PORT))
                temp_socket.close()
            except socket.error:
                abort_framework("Inbound proxy address already in use")
            # If everything is fine.
            self.proxy_process = proxy.ProxyProcess()
            self.proxy_process.initialize(options['OutboundProxy'], options['OutboundProxyAuth'])
            self.transaction_logger = transaction_logger.TransactionLogger(cache_dir=INBOUND_PROXY_CACHE_DIR)
            logging.warn("{0}:{1} <-- HTTP(S) Proxy to which requests can be directed".format(INBOUND_PROXY_IP,
                str(INBOUND_PROXY_PORT)))
            self.proxy_process.start()
            logging.debug("Starting transaction logger process")
            self.transaction_logger.start()
            logging.debug("Proxy transaction's log file at %s", PROXY_LOG)


    def enable_logging(self, **kwargs):
        """Enables both file and console logging

         . note::

        + process_name <-- can be specified in kwargs
        + Must be called from inside the process because we are kind of
          overriding the root logger

        :param kwargs: Additional arguments to the logger
        :type kwargs: `dict`
        :return:
        :rtype: None
        """
        process_name = kwargs.get("process_name", multiprocessing.current_process().name)
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        file_handler = self.file_handler(get_log_path(process_name), mode="w+")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(FileFormatter())

        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel(logging.INFO)
        stream_handler.setFormatter(ConsoleFormatter())

        # Replace any old handlers
        logger.handlers = [file_handler, stream_handler]

    def disable_console_logging(self, **kwargs):
        """Disables console logging

        . note::
            Must be called from inside the process because we should remove handler for that root logger. Since we add
            console handler in the last, we can remove the last handler to disable console logging

        :param kwargs: Additional arguments to the logger
        :type kwargs: `dict`
        :return:
        :rtype: None
        """
        logger = logging.getLogger()
        if isinstance(logger.handlers[-1], logging.StreamHandler):
            logger.removeHandler(logger.handlers[-1])

    def start(self, options):
        """Start OWTF.

        :params list options: Options from the CLI.

        """
        if self.initialise_framework(options):
            if not options['nowebui']:
                return self.run_server()
            else:
                return self.run_cli()

    def initialise_framework(self, options):
        """This function initializes the entire framework

        :param options: Additional arguments for the component initializer
        :type options: `dict`
        :return: True if all commands do not fail
        :rtype: `bool`
        """
        self.proxy_mode = options["ProxyMode"]
        logging.info("Loading framework please wait..")
        # No processing required, just list available modules.
        if options['list_plugins']:
            show_plugin_list(options['list_plugins'])
            self.finish()
        target_urls = self.load_targets(options)
        self.load_works(target_urls, options)

        self.start_proxy(options)  # Proxy mode is started in that function.
        return True

    def run_server(self):
        """This method starts the interface server"""
        self.interface_server = server.APIServer()
        logging.warn("http://%s:%s <-- Web UI URL".format(SERVER_ADDR, UI_SERVER_PORT))
        logging.info("Press Ctrl+C to exit.")
        self.disable_console_logging()
        self.interface_server.start()
        self.file_server = server.FileServer()
        self.file_server.start()

    def run_cli(self):
        """This method starts the CLI server."""
        self.cli_server = server.CliServer()
        self.cli_server.start()

    def load_works(self, target_urls, options):
        """Select the proper plugins to run against the target URLs.

        :param list target_urls: the target URLs
        :param dict options: the options from the CLI.

        """
        for target_url in target_urls:
            if target_url:
                self.load_work(target_url, options)

    def load_work(self, target_url, options):
        """Select the proper plugins to run against the target URL.

        .. note::

            If plugin group is not specified and several targets are fed, OWTF
            will run the WEB plugins for targets that are URLs and the NET
            plugins for the ones that are IP addresses.

        :param str target_url: the target URL
        :param dict options: the options from the CLI.
        """
        target = get_target_config_dicts({'target_url': target_url})
        group = options['PluginGroup']
        if options['OnlyPlugins'] is None:
            # If the plugin group option is the default one (not specified by the user).
            if group is None:
                group = 'web'  # Default to web plugins.
                # Run net plugins if target does not start with http (see #375).
                if not target_url.startswith(('http://', 'https://')):
                    group = 'network'
            filter_data = {'type': options['PluginType'], 'group': group}
        else:
            filter_data = {"code": options.get("OnlyPlugins"), "type": options.get("PluginType")}
        plugins = get_all_plugin_dicts(filter_data)
        if not plugins:
            logging.error("No plugin found matching type '%s' and group '%s' for target '%s'!" %
                          (options['PluginType'], group, target))
        add_work(target, plugins, force_overwrite=options["Force_Overwrite"])

    def load_targets(self, options):
        """Load targets into the DB

        :param options: User supplied arguments
        :type options: `dict`
        :return: Added targets
        :rtype: `list`
        """
        scope = options['Scope']
        if options['PluginGroup'] == 'auxiliary':
            scope = self.get_aux_target(options)
        added_targets = list()
        for target in scope:
            try:
                add_target(target)
                added_targets.append(target)
            except DBIntegrityException:
                logging.warning("%s already exists in DB" % target)
                added_targets.append(target)
            except UnresolvableTargetException as e:
                logging.error("%s" % e.parameter)
        return added_targets

    def get_aux_target(self, options):
        """This function returns the target for auxiliary plugins from the parameters provided

        :param options: User supplied arguments
        :type options: `dict`
        :return: List of targets for aux plugins
        :rtype: `list`
        """
        # targets can be given by different params depending on the aux plugin we are running
        # so "target_params" is a list of possible parameters by which user can give target
        target_params = ['RHOST', 'TARGET', 'SMB_HOST', 'BASE_URL', 'SMTP_HOST']
        targets = None
        if plugin_params.process_args():
            for param in target_params:
                if param in plugin_params.args:
                    targets = plugin_params.args[param]
                    break  # it will capture only the first one matched
            repeat_delim = ','
            if targets is None:
                logging.error("Aux target not found! See your plugin accepted parameters in ./plugins/ folder")
                return list()
            if 'REPEAT_DELIM' in plugin_params.args:
                repeat_delim = plugin_params.args['REPEAT_DELIM']
            return targets.split(repeat_delim)
        else:
            return list()

    def finish(self):
        """Finish OWTF framework after freeing resources.

        :return: None
        :rtype: None

        """
        if getattr(self, "tor_process", None) is not None:
            self.tor_process.terminate()
        else:
            if getattr(self, "plugin_handler", None) is not None:
                self.plugin_handler.clean_up()
            if getattr(self, "proxy_process", None) is not None:
                logging.info("Stopping inbound proxy processes and cleaning up. Please wait!")
                self.proxy_process.clean_up()
                kill_children(int(self.proxy_process.pid))
                self.proxy_process.join()
            if getattr(self, "transaction_logger", None) is not None:
                # No signal is generated during closing process by terminate()
                self.transaction_logger.poison_q.put('done')
                self.transaction_logger.join()
            if getattr(self, "worker_manager", None) is not None:
                # Properly stop the workers.
                self.worker_manager.clean_up()
            if getattr(self, "db", None) is not None:
                # Properly stop any DB instances.
                self.db.clean_up()
            # Stop any tornado instance.
            if getattr(self, "cli_server", None) is not None:
                self.cli_server.clean_up()
            tornado.ioloop.IOLoop.instance().stop()
            sys.exit(0)

