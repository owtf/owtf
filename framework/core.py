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
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

The core is the glue that holds the components together and allows some of them
to communicate with each other

"""

import os
import re
import sys
import time
import fcntl
import shutil
import codecs
import signal
import socket
import logging
import multiprocessing
import subprocess
from threading import Thread

from framework import timer, error_handler
from framework.config import config
from framework.db import db
from framework.http import requester
from framework.http.proxy import proxy, transaction_logger, tor_manager
from framework.http.proxy.proxy_manager import Proxy_manager, Proxy_Checker
from framework.http.proxy.outbound_proxyminer import Proxy_Miner
from framework.plugin import plugin_handler, plugin_helper, \
    plugin_params, worker_manager
from framework.protocols import smtp, smb
from framework.interface import reporter, server
from framework import zest, zap
from framework.lib.formatters import ConsoleFormatter, FileFormatter
from framework.selenium import selenium_handler
from framework.shell import blocking_shell, interactive_shell
from framework.wrappers.set import set_handler
from framework.lib.general import cprint, RemoveListBlanks, \
    List2DictKeys, WipeBadCharsForFilename


class Core(object):
    """
    The glue which holds everything together
    """
    def __init__(self, root_dir, owtf_pid):
        """
        [*] Tightly coupled, cohesive framework components
        [*] Order is important

        + IO decorated so as to abort on any permission errors
        + Attach error handler and config
        + Required folders created
        + All other components are attached to core: shell, db etc...
        + Required booleans and attributes are initialised
        + If modules have Init calls, they are run
          Init procedures can exist only if the component can do some
          initialisation only after addition of all components
        """
        # ------------------------ IO decoration ------------------------ #
        self.decorate_io()

        # -------------------- Component attachment -------------------- #
        # (Order is important, if there is a dependency on some other
        # other component please mention in a comment)
        # Shell might be needed in some places
        # As soon as you have config create logger for MainProcess
        # DB needs Config for some settings
        self.DB = db.DB(self)
        self.Config = config.Config(root_dir, owtf_pid, self)
        self.zest = zest.Zest(self)
        self.zap_api_handler = zap.ZAP_API(self)
        self.Error = error_handler.ErrorHandler(self)
        self.DB.Init()  # Separate Init because of self reference
        # Zest related components
        self.Config.init()
        self.zest.init()

        # ----------------------- Directory creation ----------------------- #
        self.create_dirs()
        self.pnh_log_file()  # <-- This is not supposed to be here

        self.Timer = timer.Timer(self.DB.Config.Get('DATE_TIME_FORMAT'))
        self.Shell = blocking_shell.Shell(self)
        self.enable_logging()
        # Plugin Helper needs access to automate Plugin tasks
        self.PluginHelper = plugin_helper.PluginHelper(self)
        # Reporter needs access to Core to access Config, etc
        self.Reporter = reporter.Reporter(self)
        self.Selenium = selenium_handler.Selenium(self)
        self.InteractiveShell = interactive_shell.InteractiveShell(self)
        self.SET = set_handler.SETHandler(self)
        self.SMTP = smtp.SMTP(self)
        self.SMB = smb.SMB(self)




        # -------------------- Booleans and attributes -------------------- #
        self.IsIPInternalRegexp = re.compile(
            "^127.\d{123}.\d{123}.\d{123}$|^10.\d{123}.\d{123}.\d{123}$|"
            "^192.168.\d{123}$|^172.(1[6-9]|2[0-9]|3[0-1]).[0-9]{123}.[0-9]{123}$"
        )
        self.TOR_process = None

        # --------------------------- Init calls --------------------------- #
        # Nothing as of now

    def create_dirs(self):
        """
        Any directory which needs to be created at the start of owtf
        needs to be placed inside here. No hardcoding of paths please
        """
        # Logs folder creation
        if not os.path.exists(self.Config.FrameworkConfigGetLogsDir()):
            self.CreateMissingDirs(self.Config.FrameworkConfigGetLogsDir())
        # Temporary storage directories creation
        self.create_temp_storage_dirs()

    def create_temp_storage_dirs(self):
        """Create a temporary directory in /tmp with pid suffix."""
        tmp_dir = os.path.join('/tmp', 'owtf')
        if not os.path.exists(tmp_dir):
            tmp_dir = os.path.join(tmp_dir, str(self.Config.OwtfPid))
            if not os.path.exists(tmp_dir):
                self.makedirs(tmp_dir)

    def clean_temp_storage_dirs(self):
        """Rename older temporary directory to avoid any further confusions."""
        curr_tmp_dir = os.path.join('/tmp', 'owtf', str(self.Config.OwtfPid))
        new_tmp_dir = os.path.join(
            '/tmp', 'owtf', 'old-%d' % self.Config.OwtfPid)
        if os.path.exists(curr_tmp_dir) and os.access(curr_tmp_dir, os.W_OK):
            os.rename(curr_tmp_dir, new_tmp_dir)

    # wrapper to logging.info function
    def log(self, msg, *args, **kwargs):
        logging.info(msg, *args, **kwargs)

    def CreateMissingDirs(self, path):
        if os.path.isfile(path):
            dir = os.path.dirname(path)
        else:
            dir = path
        if not os.path.exists(dir):
            self.makedirs(dir)  # Create any missing directories.

    def pnh_log_file(self):
        self.path = self.Config.FrameworkConfigGet('PNH_EVENTS_FILE')
        self.mode = "w"
        try:
            if os.path.isfile(self.path):
                pass
            else:
                with self.open(self.path, self.mode, owtf_clean=False):
                    pass
        except IOError as e:
            self.log("I/O error ({0}): {1}".format(e.errno, e.strerror))
            raise

    def write_event(self, content, mode):
        self.content = content
        self.mode = mode
        self.file_path = self.Config.FrameworkConfigGet('PNH_EVENTS_FILE')

        if (os.path.isfile(self.file_path) and os.access(self.file_path, os.W_OK)):
            try:
                with self.open(self.file_path, self.mode, owtf_clean=False) as log_file:
                    log_file.write(self.content)
                    log_file.write("\n")
                return True
            except IOError:
                return False

    def DumpFile(self, filename, contents, directory):
        save_path = os.path.join(directory, WipeBadCharsForFilename(filename))
        self.CreateMissingDirs(directory)
        with self.codecs_open(save_path, 'wb', 'utf-8') as f:
            f.write(contents.decode('utf-8', 'replace'))
        return save_path

    def get_child_pids(self, parent_pid):
        ps_command = subprocess.Popen(
            "ps -o pid --ppid %d --noheaders" % parent_pid,
            shell=True,
            stdout=subprocess.PIPE)
        output, error = ps_command.communicate()
        return [int(child_pid) for child_pid in output.readlines("\n")[:-1]]

    def GetCommand(self, argv):
        # Format command to remove directory and space-separate arguments.
        return " ".join(argv).replace(argv[0], os.path.basename(argv[0]))

    def AnonymiseCommand(self, command):
        # Host name setting value for all targets in scope.
        for host in self.DB.Target.GetAll('HOST_NAME'):
            if host:  # Value is not blank
                command = command.replace(host, 'some.target.com')
        for ip in self.DB.Target.GetAll('HOST_IP'):
            if ip:
                command = command.replace(ip, 'xxx.xxx.xxx.xxx')
        return command

    def Start_TOR_Mode(self, options):
        if options['TOR_mode'] is not None:
            if options['TOR_mode'][0] != "help":
                if tor_manager.TOR_manager.is_tor_running():
                    self.TOR_process = tor_manager.TOR_manager(
                        self,
                        options['TOR_mode'])
                    self.TOR_process = self.TOR_process.Run()
                else:
                    tor_manager.TOR_manager.msg_start_tor(self)
                    tor_manager.TOR_manager.msg_configure_tor(self)
                    self.Error.FrameworkAbort("TOR Daemon is not running")
            else:
                tor_manager.TOR_manager.msg_configure_tor()
                self.Error.FrameworkAbort("Configuration help is running")

    def StartBotnetMode(self, options):
        self.Proxy_manager = None
        if options['Botnet_mode'] is not None:
            self.Proxy_manager = Proxy_manager()
            answer = "Yes"
            proxies = []
            if options['Botnet_mode'][0] == "miner":
                miner = Proxy_Miner()
                proxies = miner.start_miner()

            if options['Botnet_mode'][0] == "list":  # load proxies from list
                proxies = self.Proxy_manager.load_proxy_list(
                    options['Botnet_mode'][1]
                )
                answer = raw_input(
                    "[#] Do you want to check the proxy list? [Yes/no] : "
                )

            if answer.upper() in ["", "YES", "Y"]:
                proxy_q = multiprocessing.Queue()
                proxy_checker = multiprocessing.Process(
                    target=Proxy_Checker.check_proxies,
                    args=(proxy_q, proxies,)
                )
                logging.info("Checking Proxies...")
                start_time = time.time()
                proxy_checker.start()
                proxies = proxy_q.get()
                proxy_checker.join()

            self.Proxy_manager.proxies = proxies
            self.Proxy_manager.number_of_proxies = len(proxies)

            if options['Botnet_mode'][0] == "miner":
                logging.info("Writing proxies to disk(~/.owtf/proxy_miner/proxies.txt)")
                miner.export_proxies_to_file("proxies.txt", proxies)
            if answer.upper() in ["", "YES", "Y"]:
                logging.info(
                    "Proxy Check Time: %s",
                    time.strftime(
                        '%H:%M:%S',
                        time.localtime(time.time() - start_time - 3600)
                    )
                )
                cprint("Done")

            proxy = self.Proxy_manager.get_next_available_proxy()

            # check proxy var... http:// sock://
            options['OutboundProxy'] = []
            options['OutboundProxy'].append(proxy["proxy"][0])
            options['OutboundProxy'].append(proxy["proxy"][1])

    def StartProxy(self, options):
        # The proxy along with supporting processes are started
        if True:
            # Check if port is in use
            try:
                temp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                temp_socket.bind((
                    self.DB.Config.Get('INBOUND_PROXY_IP'),
                    int(self.DB.Config.Get('INBOUND_PROXY_PORT'))))
                temp_socket.close()
            except socket.error:
                self.Error.FrameworkAbort(
                    "Inbound proxy address " +
                    self.DB.Config.Get('INBOUND_PROXY_IP') + ":" +
                    self.DB.Config.Get("INBOUND_PROXY_PORT") +
                    " already in use")

            # If everything is fine.
            self.ProxyProcess = proxy.ProxyProcess(self)
            self.ProxyProcess.initialize(
                options['OutboundProxy'],
                options['OutboundProxyAuth']
            )
            self.TransactionLogger = transaction_logger.TransactionLogger(
                self,
                cache_dir=self.DB.Config.Get('INBOUND_PROXY_CACHE_DIR')
            )
            logging.info(
                "Starting Inbound proxy at %s:%s",
                self.DB.Config.Get('INBOUND_PROXY_IP'),
                self.DB.Config.Get("INBOUND_PROXY_PORT"))
            self.ProxyProcess.start()
            logging.info("Starting Transaction logger process")
            self.TransactionLogger.start()
            self.Requester = requester.Requester(
                self, [
                    self.DB.Config.Get('INBOUND_PROXY_IP'),
                    self.DB.Config.Get('INBOUND_PROXY_PORT')]
                )
            logging.info(
                "Proxy transaction's log file at %s",
                self.DB.Config.Get("PROXY_LOG"))
            logging.info(
                "Interface server log file at %s",
                self.DB.Config.Get("SERVER_LOG"))
            logging.info(
                "Execution of OWTF is halted. You can browse through "
                "OWTF proxy) Press Enter to continue with OWTF")
        else:
            self.Requester = requester.Requester(
                self,
                options['OutboundProxy'])

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
        file_handler = self.FileHandler(
            self.Config.FrameworkConfigGetLogPath(process_name),
            mode="w+"
        )
        file_handler.setFormatter(FileFormatter())

        stream_handler = logging.StreamHandler(sys.stdout)
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
        logger.removeHandler(logger.handlers[-1])

    def Start(self, options):
        if self.initialise_framework(options):
            return self.run_server()

    def initialise_framework(self, options):
        self.ProxyMode = options["ProxyMode"]
        cprint("Loading framework please wait..")
        # self.initlogger()

        # No processing required, just list available modules.
        if options['ListPlugins']:
            self.PluginHandler.ShowPluginList()
            self.exit_output()
            return False
        self.Config.ProcessOptions(options)
        command = self.GetCommand(options['argv'])

        self.StartBotnetMode(options)
        self.StartProxy(options)  # Proxy mode is started in that function.
        self.initialise_plugin_handler_and_params(options)
        # Set anonymised invoking command for error dump info.
        self.Error.SetCommand(self.AnonymiseCommand(command))
        return True

    def initialise_plugin_handler_and_params(self, options):
        # The order is important here ;)
        self.PluginHandler = plugin_handler.PluginHandler(self, options)
        ## the following init() are invoked because they have dependency with plugin handler
        self.DB.POutput.init()
        self.Reporter.init()
        self.Requester.init()
        self.PluginParams = plugin_params.PluginParams(self, options)
        self.WorkerManager = worker_manager.WorkerManager(self)

    def run_server(self):
        """
        This method starts the interface server
        """
        self.InterfaceServer = server.InterfaceServer(self)
        logging.info(
            "Interface Server started. Visit http://%s:%s",
            self.Config.FrameworkConfigGet("UI_SERVER_ADDR"),
            self.Config.FrameworkConfigGet("UI_SERVER_PORT"))
        #self.disable_console_logging()
        logging.info("Press Ctrl+C when you spawned a shell ;)")
        self.InterfaceServer.start()

    def ReportErrorsToGithub(self):
        cprint(
            "Do you want to add any extra info to the bug report? "
            "[Just press Enter to skip]")
        info = raw_input("> ")
        cprint(
            "Do you want to add your GitHub username to the report? "
            "[Press Enter to skip]")
        user = raw_input("Reported by @")
        if self.Error.AddGithubIssue(Info=info, User=user):
            cprint("Github issue added, Thanks for reporting!!")
        else:
            cprint("Unable to add github issue, but thanks for trying :D")

    def Finish(self, status='Complete', report=True):
        if self.TOR_process != None:
            self.TOR_process.terminate()
        # TODO: Fix this for lions_2014
        # if self.DB.Config.Get('SIMULATION'):
        #    exit()
        else:
            try:
                self.PluginHandler.CleanUp()
            except AttributeError:  # DB not instantiated yet!
                cprint("OWTF :P")
            finally:
                if self.ProxyMode:
                    try:
                        cprint(
                            "Stopping inbound proxy processes and "
                            "cleaning up, Please wait!")
                        self.KillChildProcesses(self.ProxyProcess.pid)
                        self.ProxyProcess.terminate()
                        # No signal is generated during closing process by
                        # terminate()
                        self.TransactionLogger.poison_q.put('done')
                        self.TransactionLogger.join()
                    except:  # It means the proxy was not started.
                        pass
                exit()

    def IsIPInternal(self, IP):
        return len(self.IsIPInternalRegexp.findall(IP)) == 1

    def KillChildProcesses(self, parent_pid, sig=signal.SIGINT):
        ps_command = subprocess.Popen(
            "ps -o pid --ppid %d --noheaders" % parent_pid,
            shell=True,
            stdout=subprocess.PIPE)
        ps_output = ps_command.stdout.read()
        for pid_str in ps_output.split("\n")[:-1]:
            self.KillChildProcesses(int(pid_str), sig)
            try:
                os.kill(int(pid_str), sig)
            except:
                cprint("unable to kill it")

    def decorate_io(self):
        """Decorate different I/O functions to ensure OWTF to properly quit."""
        def catch_error(func):
            """Decorator on I/O functions.

            If an error is detected, force OWTF to quit properly.

            """
            def io_error(*args, **kwargs):
                """Call the original function while checking for errors.

                If `owtf_clean` parameter is not explicitely passed or if it is
                set to `True`, it force OWTF to properly exit.

                """
                owtf_clean = kwargs.pop('owtf_clean', True)
                try:
                    return func(*args, **kwargs)
                except (OSError, IOError) as e:
                    if owtf_clean:
                        self.Error.FrameworkAbort(
                            "Error when calling '%s'! %s." %
                            (func.__name__, str(e)))
                    raise e
            return io_error

        # Decorated functions
        self.open = catch_error(open)
        self.codecs_open = catch_error(codecs.open)
        self.mkdir = catch_error(os.mkdir)
        self.makedirs = catch_error(os.makedirs)
        self.rmtree = catch_error(shutil.rmtree)
        self.FileHandler = catch_error(logging.FileHandler)


def Init(root_dir, owtf_pid):
    return Core(root_dir, owtf_pid)
