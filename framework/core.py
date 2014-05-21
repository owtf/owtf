#!/usr/bin/env python
'''
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

Description:
The core is the glue that holds the components together and allows some of them to communicate with each other
'''
from framework import timer, error_handler
from framework.lib.log_queue import logQueue
from framework.config import config
from framework.db import db
from framework.http import requester
from framework.http.proxy import proxy, transaction_logger, tor_manager
from framework.lib.general import *
from framework.plugin import plugin_handler, plugin_helper, plugin_params, process_manager
from framework.protocols import smtp, smb
from framework.interface import reporter, server
#from framework.report.reporting_process import reporting_process
from framework.selenium import selenium_handler
from framework.shell import blocking_shell, interactive_shell
from framework.wrappers.set import set_handler
from threading import Thread
import fcntl
import logging
import multiprocessing
import os
import re
import shutil
import signal
import subprocess
import socket
from framework import random
from framework.lib.messaging import messaging_admin

class Core:
    def __init__(self, RootDir, OwtfPid):
        self.CreateTempStorageDirs(OwtfPid)
        # Tightly coupled, cohesive framework components:
        self.Error = error_handler.ErrorHandler(self)
        self.Shell = blocking_shell.Shell(self) # Config needs to find plugins via shell = instantiate shell first
        self.Config = config.Config(RootDir, OwtfPid, self)
        self.Config.Init() # Now the the config is hooked to the core, init config sub-components
        self.PluginHelper = plugin_helper.PluginHelper(self) # Plugin Helper needs access to automate Plugin tasks
        self.Random = random.Random()
        self.IsIPInternalRegexp = re.compile("^127.\d{123}.\d{123}.\d{123}$|^10.\d{123}.\d{123}.\d{123}$|^192.168.\d{123}$|^172.(1[6-9]|2[0-9]|3[0-1]).[0-9]{123}.[0-9]{123}$")
        self.Reporter = reporter.Reporter(self) # Reporter needs access to Core to access Config, etc
        self.Selenium = selenium_handler.Selenium(self)
        self.InteractiveShell = interactive_shell.InteractiveShell(self)
        self.SET = set_handler.SETHandler(self)
        self.SMTP = smtp.SMTP(self)
        self.SMB = smb.SMB(self)
        #self.messaging_admin = messaging_admin.message_admin(self)
        self.DB = db.DB(self) # DB is initialised from some Config settings, must be hooked at this point
        self.DB.Init()

        self.Timer = timer.Timer(self.DB.Config.Get('DATE_TIME_FORMAT')) # Requires user config db
        self.showOutput=True
        self.TOR_process = None

    def CreateTempStorageDirs(self, OwtfPid):
        temp_storage = os.path.join("/tmp", "owtf", str(OwtfPid))
        if not os.path.exists(temp_storage):
            os.makedirs(temp_storage)

    def CleanTempStorageDirs(self, OwtfPid):
        temp_storage = os.path.join("/tmp", "owtf", str(OwtfPid))
        renamed_temp_storage = os.path.join("/tmp", "owtf", "old-"+str(OwtfPid))
        if os.path.exists(temp_storage):
            os.rename(temp_storage, renamed_temp_storage)

    #wrapper to log function
    def log(self,*args):
        log(*args)

    def CreateMissingDirs(self, Path):
        if os.path.isfile(Path):
            Dir = os.path.dirname(Path)
        else:
            Dir = Path
        if not os.path.exists(Dir):
            os.makedirs(Dir) # Create any missing directories

    def DumpFile(self, Filename, Contents, Directory):
        SavePath=Directory+WipeBadCharsForFilename(Filename)
        self.CreateMissingDirs(Directory)
        with open(SavePath, 'wb') as file:
            file.write(Contents)
        return SavePath

    def get_child_pids(self, parent_pid):
        PsCommand = subprocess.Popen("ps -o pid --ppid %d --noheaders" % parent_pid, shell=True, stdout=subprocess.PIPE)
        output, error = PsCommand.communicate()
        return [int(child_pid) for child_pid in output.readlines("\n")[:-1]]

    def GetPartialPath(self, Path):
        #return MultipleReplace(Path, List2DictKeys(RemoveListBlanks(self.Config.GetAsList( [ 'HOST_OUTPUT', 'OUTPUT_PATH' ]))))
        #print str(self.Config.GetAsList( [ 'HOST_OUTPUT', 'OUTPUT_PATH' ] ))
        #print "Path before="+Path
        #Path = MultipleReplace(Path, List2DictKeys(RemoveListBlanks(self.Config.GetAsList( [ 'OUTPUT_PATH' ]))))
        #Need to replace URL OUTPUT first so that "View Unique as HTML" Matches on body links work
        Path = MultipleReplace(Path, List2DictKeys(RemoveListBlanks(self.Config.GetAsList( [ 'HOST_OUTPUT', 'OUTPUT_PATH' ]))))
        #print "Path after="+Path

        if '/' == Path[0]: # Stripping out leading "/" if present
            Path = Path[1:]
        return Path

    def GetCommand(self, argv):
        # Format command to remove directory and space-separate arguments
        return " ".join(argv).replace(argv[0], os.path.basename(argv[0]))

    def AnonymiseCommand(self, Command):
        for Host in self.DB.Target.GetAll('HOST_NAME'): # Host name setting value for all targets in scope
            if Host: # Value is not blank
                Command = Command.replace(Host, 'some.target.com')
        for ip in self.DB.Target.GetAll('HOST_IP'):
            if ip:
                Command = Command.replace(ip, 'xxx.xxx.xxx.xxx')
        return Command        
        
    def Start_TOR_Mode(self, Options):
        if Options['TOR_mode'] != None:
            if Options['TOR_mode'][0] != "help":
                if tor_manager.TOR_manager.is_tor_running():
                    self.TOR_process = tor_manager.TOR_manager(self, Options['TOR_mode'])
                    self.TOR_process = self.TOR_process.Run()
                else:                    
                    tor_manager.TOR_manager.msg_start_tor(self)
                    tor_manager.TOR_manager.msg_configure_tor(self)
                    self.Error.FrameworkAbort("TOR Daemon is not running")
            else:
                tor_manager.TOR_manager.msg_configure_tor()
                self.Error.FrameworkAbort("Configuration help is running")
     
    def StartProxy(self, Options):
        # The proxy along with supporting processes are started
        if True:
            # Check if port is in use
            try:
                temp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                temp_socket.bind((self.DB.Config.Get('INBOUND_PROXY_IP'), int(self.DB.Config.Get('INBOUND_PROXY_PORT'))))
                temp_socket.close()
            except socket.error: #Exception:
                self.Error.FrameworkAbort("Inbound proxy address " + self.DB.Config.Get('INBOUND_PROXY_IP') + ":" + self.DB.Config.Get("INBOUND_PROXY_PORT") + " already in use")

            # If everything is fine
            self.ProxyProcess = proxy.ProxyProcess( 
                                                    self,
                                                    Options['OutboundProxy'],
                                                    Options['OutboundProxyAuth']
                                                  )
            poison_q = multiprocessing.Queue()
            self.TransactionLogger = transaction_logger.TransactionLogger(self, poison_q)
            cprint("Starting Inbound proxy at " + self.DB.Config.Get('INBOUND_PROXY_IP') + ":" + self.DB.Config.Get("INBOUND_PROXY_PORT"))
            self.ProxyProcess.start()
            cprint("Starting Transaction logger process")
            self.TransactionLogger.start()
            self.Requester = requester.Requester(self, [self.DB.Config.Get('INBOUND_PROXY_IP'), self.DB.Config.Get('INBOUND_PROXY_PORT')])
            cprint("Proxy transaction's log file at %s"%(self.DB.Config.Get("PROXY_LOG")))
            cprint("Visit http://" + self.DB.Config.Get('INBOUND_PROXY_IP') + ":" + self.DB.Config.Get("INBOUND_PROXY_PORT") + "/proxy to use Plug-n-Hack standard")
            cprint("Execution of OWTF is halted.You can browse through OWTF proxy) Press Enter to continue with OWTF")
            #if Options["Interactive"]:
            #    raw_input()
        else:
            self.Requester = requester.Requester(self, Options['OutboundProxy'])        
    
    def outputfunc(self,q):
        """
            This is the function/thread which writes on terminal
            It takes the content from queue and if showOutput is true it writes to console.
            Otherwise it appends to a variable. 
            If the next token is 'end' It simply writes to the console.
            
        """
        t=""
        #flags = fcntl.fcntl(sys.stdout, fcntl.F_GETFL)
        #fcntl.fcntl(sys.stdout, fcntl.F_SETFL, flags | os.O_NONBLOCK)
        while True:
            try:
                k = q.get()
                #print k
            except:
                continue
            if k=='end':
                try:
                    sys.stdout.write(t)
                except:
                    pass
                return
            t = t+k
            if(self.showOutput): 
                try:   
                    sys.stdout.write(t)
                    t=""
                except:
                    pass    
                                                    
                                
        
    def initlogger(self):
        """
            This function init two logger one for output in log file and stdout
        """
        #logger for output in console
        self.outputqueue = multiprocessing.Queue()
        result_queue = logQueue(self.outputqueue)
        log = logging.getLogger('general')
        infohandler = logging.StreamHandler(result_queue)
        log.setLevel(logging.INFO)
        infoformatter = logging.Formatter("%(message)s")
        infohandler.setFormatter(infoformatter)
        log.addHandler(infohandler)
        self.outputthread =Thread(target=self.outputfunc, args=(self.outputqueue,))
        self.outputthread.start()
        
        #logger for output in log file
        log = logging.getLogger('logfile')
        infohandler = logging.FileHandler(self.Config.FrameworkConfigGet("OWTF_LOG_FILE"),mode="w+")
        log.setLevel(logging.INFO)
        infoformatter = logging.Formatter("%(type)s - %(asctime)s - %(processname)s - %(functionname)s - %(message)s")
        infohandler.setFormatter(infoformatter)
        log.addHandler(infohandler)

    def Start(self, Options):
        if self.initialise_framework(Options):
            return self.run_plugins()

    def initialise_framework(self, Options):
        self.ProxyMode = Options["ProxyMode"]
        cprint("Loading framework please wait..")
        self.initlogger()

        if Options['ListPlugins']:
            self.PluginHandler.ShowPluginList()
            self.exitOutput()
            return False # No processing required, just list available modules
        #self.messaging_admin.Init()
        self.Config.ProcessOptions(Options)
        #self.Timer.StartTimer('core')
        Command = self.GetCommand(Options['argv'])

        #self.DB.Run.StartRun(Command) # Log owtf run options, start time, etc
        #else: # Reporter process is not needed unless a real run
        #    self.start_reporter()
        self.StartProxy(Options) # Proxy mode is started in that function
        #self.Start_TOR_Mode(Options)# TOR mode will start only if the Options are set
        # Proxy Check
        # TODO: Fix up proxy check, nothing but uncomment
        #ProxySuccess, Message = self.Requester.ProxyCheck()
        #cprint(Message)
        #if not ProxySuccess: # Regardless of interactivity settings if the proxy check fails = no point to move on
        #    self.Error.FrameworkAbort(Message) # Abort if proxy check failed
        # Each Plugin adds its own results to the report, the report is updated on the fly after each plugin completes (or before!)
        self.Error.SetCommand(self.AnonymiseCommand(Command)) # Set anonymised invoking command for error dump info
        self.initialise_plugin_handler_and_params(Options)
        return True

    def initialise_plugin_handler_and_params(self, Options):
        # The order is important here ;)
        self.PluginHandler = plugin_handler.PluginHandler(self, Options)
        self.PluginParams = plugin_params.PluginParams(self, Options)
        self.WorkerManager = process_manager.WorkerManager(self)

    def run_plugins(self):
        Status = self.PluginHandler.ProcessPlugins()
        self.InterfaceServer = server.InterfaceServer(self)
        cprint("Interface Server started. Visit http://" + self.Config.FrameworkConfigGet("UI_SERVER_ADDR") + ":" + self.Config.FrameworkConfigGet("UI_SERVER_PORT"))
        cprint("Press Ctrl+C when you spawned a shell ;)")
        self.InterfaceServer.start()
        if Status['AllSkipped']:
            self.Finish('Skipped')
        elif not Status['SomeSuccessful'] and Status['SomeAborted']:
            self.Finish('Aborted')
            return False
        elif not Status['SomeSuccessful']: # Not a single plugin completed successfully, major crash or something
            self.Finish('Crashed')
            return False
        return True # Scan was successful

    def ReportErrorsToGithub(self):
        cprint("Do you want to add any extra info to the bug report ? [Just press Enter to skip]")
        info = raw_input("> ")
        cprint("Do you want to add your GitHub username to the report? [Press Enter to skip]")
        user = raw_input("Reported by @")
        if self.Error.AddGithubIssue(Info=info, User=user):
            cprint("Github issue added, Thanks for reporting!!")
        else:
            cprint("Unable to add github issue, but thanks for trying :D")

    def Finish(self, Status = 'Complete', Report = True):
        if self.TOR_process != None:
            self.TOR_process.terminate()
        if self.DB.Config.Get('SIMULATION'):
            if hasattr(self,'messaging_admin'):
                self.messaging_admin.finishMessaging()
            self.exitOutput()
            exit()
        else:
            try:
                #self.DB.Run.EndRun(Status)
                self.PluginHandler.CleanUp()
                cprint("Saving DBs")
                self.DB.SaveDBs() # Save DBs prior to producing the report :)
                if Report:
                    cprint("Finishing iteration and assembling report again (with updated run information)")
                    #PreviousTarget = self.Config.GetTarget()
                    #for Target in self.Config.GetTargets(): # We have to finish all the reports in this run to update run information
                    #    self.Config.SetTarget(Target) # Much save the report for each target
                        #self.Reporter.ReportFinish() # Must save the report again at the end regarless of Status => Update Run info
                    #self.Config.SetTarget(PreviousTarget) # Restore previous target
                cprint("OWTF iteration finished")

                if self.DB.ErrorCount() > 0: # Some error occurred (counter not accurate but we only need to know if sth happened)
                    cprint('Errors saved to ' + self.Config.FrameworkConfigGet('ERROR_DB_NAME') + '. Would you like us to auto-report bugs ?')
                    choice = raw_input("[Y/n] ")
                    if choice != 'n' or choice != 'N':
                        self.ReportErrorsToGithub()
                    else:
                        cprint("We know that you are planning on submitting it manually ;)")
                #self.dbHandlerProcess.join()
            except AttributeError: # DB not instantiated yet!
                cprint("OWTF finished: No time to report anything! :P")
            finally:
                if self.ProxyMode:
                    try:
                        cprint("Stopping inbound proxy processes and cleaning up, Please wait!")
                        self.KillChildProcesses(self.ProxyProcess.pid)
                        self.ProxyProcess.terminate()
                        # No signal is generated during closing process by terminate()
                        self.TransactionLogger.poison_q.put('done')
                        self.TransactionLogger.join()
                    except: # It means the proxy was not started
                        pass
                if hasattr(self, 'DB'):
                    cprint("Saving DBs")
                    self.DB.SaveDBs() # So that detailed_report_register populated by reporting is saved :P
                self.exitOutput()
                #print self.Timer.GetElapsedTime('core')
                exit()

    def exitOutput(self):
        if hasattr(self,'outputthread'):
            self.outputqueue.put('end')    
            self.outputthread.join()
            if os.path.exists("owtf_review"):
                if os.path.exists("owtf_review/logfile"):
                    data = open(self.Config.FrameworkConfigGet("OWTF_LOG_FILE")).read()
                    AppendToFile("owtf_review/logfile", data)
                else:
                    shutil.move(self.Config.FrameworkConfigGet("OWTF_LOG_FILE"), "owtf_review")
        
    def GetSeed(self):
        try:
            return self.DB.GetSeed()
        except AttributeError: # DB not instantiated yet
            return ""

    def IsIPInternal(self, IP):
        return len(self.IsIPInternalRegexp.findall(IP)) == 1

    def IsTargetUnreachable(self, Target = ''):
        if not Target:
            Target = self.Config.GetTarget()
        #print "Target="+Target+" in "+str(self.DB.GetData('UNREACHABLE_DB'))+"?? -> "+str(Target in self.DB.GetData('UNREACHABLE_DB'))
        return Target in self.DB.GetData('UNREACHABLE_DB')

    def GetFileAsList(self, FileName):
        return GetFileAsList(FileName)

    def KillChildProcesses(self, parent_pid, sig=signal.SIGINT):
        PsCommand = subprocess.Popen("ps -o pid --ppid %d --noheaders" % parent_pid, shell=True, stdout=subprocess.PIPE)
        PsOutput = PsCommand.stdout.read()
        RetCode = PsCommand.wait()
        #assert RetCode == 0, "ps command returned %d" % RetCode
        for PidStr in PsOutput.split("\n")[:-1]:
                self.KillChildProcesses(int(PidStr),sig)
                #print PidStr
                try:
                    os.kill(int(PidStr), sig)
                except:
                    print("unable to kill it")    
                    
def Init(RootDir, OwtfPid):
    return Core(RootDir, OwtfPid)
