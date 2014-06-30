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
from framework.plugin import plugin_handler, plugin_helper, plugin_params, process_manager
from framework.protocols import smtp, smb
from framework.interface import reporter, server
from framework.selenium import selenium_handler
from framework.shell import blocking_shell, interactive_shell
from framework.wrappers.set import set_handler
from framework.lib.messaging import messaging_admin
from framework.lib.general import cprint, log, MultipleReplace, LogQueue, \
                                  RemoveListBlanks, List2DictKeys, \
                                  GetFileAsList, AppendToFile, \
                                  WipeBadCharsForFilename


class Core(object):
    def __init__(self, root_dir, owtf_pid):
        # Tightly coupled, cohesive framework components:
        self.Error = error_handler.ErrorHandler(self)
        self.decorate_io()
        self.Shell = blocking_shell.Shell(self) # Config needs to find plugins via shell = instantiate shell first
        self.Config = config.Config(root_dir, owtf_pid, self)
        self.Config.Init() # Now the the config is hooked to the core, init config sub-components
        self.create_temp_storage_dirs()
        self.PluginHelper = plugin_helper.PluginHelper(self) # Plugin Helper needs access to automate Plugin tasks
        self.IsIPInternalRegexp = re.compile("^127.\d{123}.\d{123}.\d{123}$|^10.\d{123}.\d{123}.\d{123}$|^192.168.\d{123}$|^172.(1[6-9]|2[0-9]|3[0-1]).[0-9]{123}.[0-9]{123}$")
        self.Reporter = reporter.Reporter(self) # Reporter needs access to Core to access Config, etc
        self.Selenium = selenium_handler.Selenium(self)
        self.InteractiveShell = interactive_shell.InteractiveShell(self)
        self.SET = set_handler.SETHandler(self)
        self.SMTP = smtp.SMTP(self)
        self.SMB = smb.SMB(self)
        self.DB = db.DB(self) # DB is initialised from some Config settings, must be hooked at this point
        self.DB.Init()
        uilog = self.DB.Config.Get("SERVER_LOG")
        proxy_cache_log_dir = self.DB.Config.Get("INBOUND_PROXY_CACHE_DIR")

        self.Timer = timer.Timer(self.DB.Config.Get('DATE_TIME_FORMAT')) # Requires user config db
        self.showOutput=True
        self.TOR_process = None

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

    #wrapper to log function
    def log(self,*args):
        log(*args)

    def CreateMissingDirs(self, path):
        if os.path.isfile(path):
            dir = os.path.dirname(path)
        else:
            dir = path
        if not os.path.exists(dir):
            self.makedirs(dir)  # Create any missing directories.

    def DumpFile(self, filename, contents, directory):
        save_path = directory + WipeBadCharsForFilename(filename)
        self.CreateMissingDirs(directory)
        with self.open(save_path, 'wb') as file:
            file.write(contents)
        return save_path

    def get_child_pids(self, parent_pid):
        ps_command = subprocess.Popen(
            "ps -o pid --ppid %d --noheaders" % parent_pid,
            shell=True,
            stdout=subprocess.PIPE)
        output, error = ps_command.communicate()
        return [int(child_pid) for child_pid in output.readlines("\n")[:-1]]

    def GetPartialPath(self, path):
        path = MultipleReplace(
            path,
            List2DictKeys(RemoveListBlanks(
                self.Config.GetAsList(['HOST_OUTPUT', 'OUTPUT_PATH'])))
            )
        if '/' == path[0]:  # Stripping out leading "/" if present.
            path = path[1:]
        return path

    def GetCommand(self, argv):
        # Format command to remove directory and space-separate arguments.
        return " ".join(argv).replace(argv[0], os.path.basename(argv[0]))

    def AnonymiseCommand(self, command):
        # Host name setting value for all targets in scope.
        for host in self.DB.Target.GetAll('HOST_NAME'):
            if host: # Value is not blank
                command = command.replace(host, 'some.target.com')
        for ip in self.DB.Target.GetAll('HOST_IP'):
            if ip:
                command = command.replace(ip, 'xxx.xxx.xxx.xxx')
        return command

    def Start_TOR_Mode(self, options):
        if options['TOR_mode'] != None:
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
            self.ProxyProcess = proxy.ProxyProcess(
                self,
                options['OutboundProxy'],
                options['OutboundProxyAuth']
                )
            poison_q = multiprocessing.Queue()
            self.TransactionLogger = transaction_logger.TransactionLogger(
                self,
                poison_q)
            cprint(
                "Starting Inbound proxy at " +
                self.DB.Config.Get('INBOUND_PROXY_IP') + ":" +
                self.DB.Config.Get("INBOUND_PROXY_PORT"))
            self.ProxyProcess.start()
            cprint("Starting Transaction logger process")
            self.TransactionLogger.start()
            self.Requester = requester.Requester(
                self, [
                    self.DB.Config.Get('INBOUND_PROXY_IP'),
                    self.DB.Config.Get('INBOUND_PROXY_PORT')]
                )
            cprint(
                "Proxy transaction's log file at %s" %
                self.DB.Config.Get("PROXY_LOG"))
            cprint(
                "Interface server log file at %s" %
                self.DB.Config.Get("SERVER_LOG"))
            cprint(
                "Execution of OWTF is halted. You can browse through "
                "OWTF proxy) Press Enter to continue with OWTF")
        else:
            self.Requester = requester.Requester(
                self,
                options['OutboundProxy'])

    def outputfunc(self, queue):
        """This is the function/thread which writes on terminal.

        It takes the content from queue and if showOutput is True it writes to
        console. Otherwise it appends to a variable.
        If the next token is 'end' It simply writes to the console.

        """
        temp = u''
        while True:
            try:
                token = queue.get()
            except:
                continue
            if token == 'end':
                try:
                    sys.stdout.write(temp)
                except:
                    pass
                return
            temp += unicode(token.decode('utf-8'))
            if(self.showOutput):
                try:
                    sys.stdout.write(temp)
                    temp = u''
                except:
                    pass

    def initlogger(self):
        """Init loggers, one redirected to a log file, the other to stdout."""
        # Logger for output in console.
        self.outputqueue = multiprocessing.Queue()
        result_queue = LogQueue(self.outputqueue)
        log = logging.getLogger('general')
        infohandler = logging.StreamHandler(result_queue)
        log.setLevel(logging.INFO)
        infoformatter = logging.Formatter("%(message)s")
        infohandler.setFormatter(infoformatter)
        log.addHandler(infohandler)
        self.outputthread = Thread(
            target=self.outputfunc,
            args=(self.outputqueue,))
        self.outputthread.start()

        # Logger for output in log file.
        log = logging.getLogger('logfile')
        output_file = self.Config.FrameworkConfigGet("OWTF_LOG_FILE")
        infohandler = self.FileHandler(
            self.Config.FrameworkConfigGet("OWTF_LOG_FILE"), mode="w+")
        log.setLevel(logging.INFO)
        infoformatter = logging.Formatter(
            "%(type)s - %(asctime)s - %(processname)s - "
            "%(functionname)s - %(message)s")
        infohandler.setFormatter(infoformatter)
        log.addHandler(infohandler)

    def Start(self, options):
        if self.initialise_framework(options):
            return self.run_plugins()

    def initialise_framework(self, options):
        self.ProxyMode = options["ProxyMode"]
        cprint("Loading framework please wait..")
        self.initlogger()

        # No processing required, just list available modules.
        if options['ListPlugins']:
            self.PluginHandler.ShowPluginList()
            self.exit_output()
            return False
        self.Config.ProcessOptions(options)
        command = self.GetCommand(options['argv'])

        self.StartProxy(options)  # Proxy mode is started in that function.
        # Set anonymised invoking command for error dump info.
        self.Error.SetCommand(self.AnonymiseCommand(command))
        self.initialise_plugin_handler_and_params(options)
        return True

    def initialise_plugin_handler_and_params(self, options):
        # The order is important here ;)
        self.PluginHandler = plugin_handler.PluginHandler(self, options)
        self.PluginParams = plugin_params.PluginParams(self, options)
        self.WorkerManager = process_manager.WorkerManager(self)

    def run_plugins(self):
        status = self.PluginHandler.ProcessPlugins()
        self.InterfaceServer = server.InterfaceServer(self)
        cprint(
            "Interface Server started. Visit http://" +
            self.Config.FrameworkConfigGet("UI_SERVER_ADDR") + ":" +
            self.Config.FrameworkConfigGet("UI_SERVER_PORT"))
        cprint("Press Ctrl+C when you spawned a shell ;)")
        self.InterfaceServer.start()
        if status['AllSkipped']:
            self.Finish('Skipped')
        elif not status['SomeSuccessful'] and status['SomeAborted']:
            self.Finish('Aborted')
            return False
        # Not a single plugin completed successfully, major crash or something.
        elif not status['SomeSuccessful']:
            self.Finish('Crashed')
            return False
        return True  # Scan was successful.

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
        if self.DB.Config.Get('SIMULATION'):
            if hasattr(self,'messaging_admin'):
                self.messaging_admin.finishMessaging()
            self.exit_output()
            exit()
        else:
            try:
                self.PluginHandler.CleanUp()
                cprint("Saving DBs")
                self.DB.SaveDBs()  # Save DBs prior to producing the report :)
                if report:
                    cprint(
                        "Finishing iteration and assembling report again "
                        "(with updated run information)")
                cprint("OWTF iteration finished")
                # Some error occurred (counter not accurate but we only need to
                # know if sth happened).
                if self.DB.ErrorCount() > 0:
                    cprint(
                        'Errors saved to ' +
                        self.Config.FrameworkConfigGet('ERROR_DB_NAME') +
                        '. Would you like us to auto-report bugs?')
                    choice = raw_input("[Y/n] ")
                    if choice != 'n' or choice != 'N':
                        self.ReportErrorsToGithub()
                    else:
                        cprint(
                            "We know that you are planning on submitting it "
                            "manually ;)")
            except AttributeError:  # DB not instantiated yet!
                cprint("OWTF finished: No time to report anything! :P")
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
                if hasattr(self, 'DB'):
                    cprint("Saving DBs")
                    # So that detailed_report_register populated by reporting
                    # is saved :P
                    self.DB.SaveDBs()
                self.exit_output()
                exit()

    def exit_output(self):
        if hasattr(self,'outputthread'):
            self.outputqueue.put('end')
            self.outputthread.join()
            tmp_log = self.Config.FrameworkConfigGet("OWTF_LOG_FILE")
            if os.path.exists("owtf_review"):
                if os.path.isfile("owtf_review/logfile"):
                    if os.path.isfile(tmp_log):
                        data = self.open(tmp_log).read()
                        AppendToFile("owtf_review/logfile", data)
                else:
                    shutil.move(tmp_log, "owtf_review")

    def GetSeed(self):
        try:
            return self.DB.GetSeed()
        except AttributeError:  # DB not instantiated yet.
            return ""

    def IsIPInternal(self, IP):
        return len(self.IsIPInternalRegexp.findall(IP)) == 1

    def IsTargetUnreachable(self, target=''):
        if not target:
            target = self.Config.GetTarget()
        return target in self.DB.GetData('UNREACHABLE_DB')

    def GetFileAsList(self, fileName):
        return GetFileAsList(fileName)

    def KillChildProcesses(self, parent_pid, sig=signal.SIGINT):
        ps_command = subprocess.Popen(
            "ps -o pid --ppid %d --noheaders" % parent_pid,
            shell=True,
            stdout=subprocess.PIPE)
        ps_output = ps_command.stdout.read()
        for pid_str in ps_output.split("\n")[:-1]:
            self.KillChildProcesses(int(pid_str),sig)
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
