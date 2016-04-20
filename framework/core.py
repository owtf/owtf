#!/usr/bin/env python
"""
The core is the glue that holds the components together and allows some of them
to communicate with each other
"""

import os
import sys
import signal
import socket
import logging
import multiprocessing
import subprocess

import tornado

from framework.dependency_management.dependency_resolver import BaseComponent
from framework.dependency_management.component_initialiser import ComponentInitialiser
from framework.utils import FileOperations, catch_io_errors, OutputCleaner, OWTFLogger
from framework.interface import server, cli
from framework.http.proxy import proxy, transaction_logger
from framework.plugin import worker_manager
from framework.lib.formatters import ConsoleFormatter, FileFormatter


class Core(BaseComponent):

    """Main entry point for OWTF that manages the OWTF components."""

    COMPONENT_NAME = "core"

    def __init__(self):
        """Initialize a Core instance.

        .. note::

            [*] Tightly coupled, cohesive framework components
            [*] Order is important

            + IO decorated so as to abort on any permission errors
            + Required folders created
            + All other components are attached to core: shell, db etc... (using ServiceLocator)

        :return: instance of :class:`framework.core.Core`
        :rtype::class:`framework.core.Core`

        """
        self.register_in_service_locator()
        # ------------------------ IO decoration ------------------------ #
        self.file_handler = catch_io_errors(logging.FileHandler)
        # -------------------- Component attachment -------------------- #
        self.db = self.get_component("db")
        self.config = self.get_component("config")
        self.db_config = self.get_component("db_config")
        self.error_handler = self.get_component("error_handler")
        # ----------------------- Directory creation ----------------------- #
        self.create_dirs()
        self.pnh_log_file()  # <-- This is not supposed to be here
        self.enable_logging()
        # The following attributes will be initialised later
        self.tor_process = None

    def create_dirs(self):
        """
        Any directory which needs to be created at the start of owtf
        needs to be placed inside here. No hardcoding of paths please
        """
        # Logs folder creation
        if not os.path.exists(self.config.FrameworkConfigGetLogsDir()):
            FileOperations.create_missing_dirs(self.config.FrameworkConfigGetLogsDir())
        # Temporary storage directories creation
        self.create_temp_storage_dirs()

    def create_temp_storage_dirs(self):
        """Create a temporary directory in /tmp with pid suffix."""
        tmp_dir = os.path.join('/tmp', 'owtf')
        if not os.path.exists(tmp_dir):
            tmp_dir = os.path.join(tmp_dir, str(self.config.OwtfPid))
            if not os.path.exists(tmp_dir):
                FileOperations.make_dirs(tmp_dir)

    def clean_temp_storage_dirs(self):
        """Rename older temporary directory to avoid any further confusions."""
        curr_tmp_dir = os.path.join('/tmp', 'owtf', str(self.config.OwtfPid))
        new_tmp_dir = os.path.join(
            '/tmp', 'owtf', 'old-%d' % self.config.OwtfPid)
        if os.path.exists(curr_tmp_dir) and os.access(curr_tmp_dir, os.W_OK):
            os.rename(curr_tmp_dir, new_tmp_dir)

    def pnh_log_file(self):
        self.path = self.config.FrameworkConfigGet('PNH_EVENTS_FILE')
        self.mode = "w"
        try:
            if os.path.isfile(self.path):
                pass
            else:
                with FileOperations.open(self.path, self.mode, owtf_clean=False):
                    pass
        except IOError as e:
            OWTFLogger.log("I/O error ({0}): {1}".format(e.errno, e.strerror))
            raise

    def write_event(self, content, mode):
        self.content = content
        self.mode = mode
        self.file_path = self.config.FrameworkConfigGet('PNH_EVENTS_FILE')

        if (os.path.isfile(self.file_path) and os.access(self.file_path, os.W_OK)):
            try:
                with FileOperations.open(self.file_path, self.mode, owtf_clean=False) as log_file:
                    log_file.write(self.content)
                    log_file.write("\n")
                return True
            except IOError:
                return False

    def get_command(self, argv):
        """Format command to remove directory and space-separated arguments.

        :params list argv: Arguments for the CLI.

        :return: Arguments without directory and space-separated arguments.
        :rtype: list

        """
        return " ".join(argv).replace(argv[0], os.path.basename(argv[0]))

    def start_botnet_mode(self, options):
        ComponentInitialiser.intialise_proxy_manager(options)

    def start_proxy(self, options):
        # The proxy along with supporting processes are started
        if True:
            # Check if port is in use
            try:
                temp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                temp_socket.bind((
                    self.db_config.Get('INBOUND_PROXY_IP'),
                    int(self.db_config.Get('INBOUND_PROXY_PORT'))))
                temp_socket.close()
            except socket.error:
                self.error_handler.FrameworkAbort(
                    "Inbound proxy address " +
                    self.db_config.Get('INBOUND_PROXY_IP') + ":" +
                    self.db_config.Get("INBOUND_PROXY_PORT") +
                    " already in use")

            # If everything is fine.
            self.ProxyProcess = proxy.ProxyProcess()
            self.ProxyProcess.initialize(
                options['OutboundProxy'],
                options['OutboundProxyAuth']
            )
            self.TransactionLogger = transaction_logger.TransactionLogger(
                cache_dir=self.db_config.Get('INBOUND_PROXY_CACHE_DIR')
            )
            logging.warn(
                "%s:%s <-- HTTP(S) Proxy to which requests can be directed",
                self.db_config.Get('INBOUND_PROXY_IP'),
                self.db_config.Get("INBOUND_PROXY_PORT"))
            self.ProxyProcess.start()
            logging.debug("Starting Transaction logger process")
            self.TransactionLogger.start()
            logging.debug(
                "Proxy transaction's log file at %s",
                self.db_config.Get("PROXY_LOG"))
        else:
            ComponentInitialiser.initialisation_phase_3(options['OutboundProxy'])

    def enable_logging(self, **kwargs):
        """
        + process_name <-- can be specified in kwargs
        + Must be called from inside the process because we are kind of
          overriding the root logger
        + Enables both file and console logging
        """
        process_name = kwargs.get(
            "process_name",
            multiprocessing.current_process().name
        )
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        file_handler = self.file_handler(
            self.config.FrameworkConfigGetLogPath(process_name),
            mode="w+"
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(FileFormatter())

        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel(logging.INFO)
        stream_handler.setFormatter(ConsoleFormatter())

        # Replace any old handlers
        logger.handlers = [file_handler, stream_handler]

    def disable_console_logging(self, **kwargs):
        """
        + Must be called from inside the process because we should
          remove handler for that root logger
        + Since we add console handler in the last, we can remove
          the last handler to disable console logging
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
        self.ProxyMode = options["ProxyMode"]
        logging.info("Loading framework please wait..")
        # self.initlogger()

        proxy_infos = [self.db_config.Get('INBOUND_PROXY_IP'), self.db_config.Get('INBOUND_PROXY_PORT')]
        ComponentInitialiser.initialisation_phase_3(proxy_infos, options)
        self.initialise_plugin_handler_and_params(options)
        # No processing required, just list available modules.
        if options['list_plugins']:
            self.PluginHandler.show_plugin_list(options['list_plugins'])
            self.finish()
        self.config.ProcessOptions(options)
        command = self.get_command(options['argv'])

        self.start_botnet_mode(options)
        self.start_proxy(options)  # Proxy mode is started in that function.
        # Set anonymised invoking command for error dump info.
        self.error_handler.SetCommand(OutputCleaner.anonymise_command(command))
        return True

    def initialise_plugin_handler_and_params(self, options):
        # The order is important here ;)
        self.PluginHandler = self.get_component("plugin_handler")
        self.PluginParams = self.get_component("plugin_params")
        # If OWTF is run without the Web UI, the WorkerManager should exit as
        # soon as all jobs have been completed. Otherwise, keep WorkerManager
        # alive.
        self.WorkerManager = worker_manager.WorkerManager(
            keep_working=not options['nowebui'])

    def run_server(self):
        """
        This method starts the interface server
        """
        self.interface_server = server.InterfaceServer()
        logging.warn(
            "http://%s:%s <-- Web UI URL",
            self.config.FrameworkConfigGet("SERVER_ADDR"),
            self.config.FrameworkConfigGet("UI_SERVER_PORT"))
        logging.info("Press Ctrl+C when you spawned a shell ;)")
        self.disable_console_logging()
        self.interface_server.start()
        self.FileServer = server.FileServer()
        self.FileServer.start()

    def run_cli(self):
        """This method starts the CLI server."""
        self.cli_server = cli.CliServer()
        self.cli_server.start()

    def finish(self):
        """Finish OWTF framework after freeing resources.

        :return: None
        :rtype: None

        """
        if getattr(self, "TOR_process", None) is not None:
            self.TOR_process.terminate()
        # TODO: Fix this for lions_2014
        # if self.db_config.Get('SIMULATION'):
        #    exit()
        else:
            if getattr(self, "PluginHandler", None) is not None:
                self.PluginHandler.clean_up()
            if getattr(self, "ProxyProcess", None) is not None:
                logging.info(
                    "Stopping inbound proxy processes and cleaning up. Please wait!")
                self.ProxyProcess.clean_up()
                self.kill_children(self.ProxyProcess.pid)
                self.ProxyProcess.join()
            if getattr(self, "TransactionLogger", None) is not None:
                # No signal is generated during closing process by
                # terminate()
                self.TransactionLogger.poison_q.put('done')
                self.TransactionLogger.join()
            if getattr(self, "WorkerManager", None) is not None:
                # Properly stop the workers.
                self.WorkerManager.clean_up()
            if getattr(self, "db", None) is not None:
                # Properly stop any DB instances.
                self.db.clean_up()
            # Stop any tornado instance.
            if getattr(self, "cli_server", None) is not None:
                self.cli_server.clean_up()
            tornado.ioloop.IOLoop.instance().stop()
            exit(0)

    def kill_children(self, parent_pid, sig=signal.SIGINT):
        ps_command = subprocess.Popen(
            "ps -o pid --ppid %d --noheaders" % parent_pid,
            shell=True,
            stdout=subprocess.PIPE)
        ps_output = ps_command.stdout.read()
        for pid_str in ps_output.split("\n")[:-1]:
            self.kill_children(int(pid_str), sig)
            try:
                os.kill(int(pid_str), sig)
            except:
                logging.warning("Unable to kill the processus: '%s'", pid_str)
