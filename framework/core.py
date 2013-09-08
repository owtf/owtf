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
from framework.http.proxy import proxy, transaction_logger
from framework.lib.general import *
from framework.plugin import plugin_handler, plugin_helper, plugin_params
from framework.protocols import smtp, smb
from framework.report import reporter, summary
from framework.selenium import selenium_handler
from framework.shell import blocking_shell, interactive_shell
from framework.wrappers.set import set_handler
from threading import Thread
from urlparse import urlparse
import fcntl
import logging
import multiprocessing
import os
import re
import shutil
import signal
import subprocess
from framework import random
from framework.lib.messaging import messaging_admin
 
class Core:
    def __init__(self, RootDir):
        # Tightly coupled, cohesive framework components:
        self.Error = error_handler.ErrorHandler(self)
        self.Shell = blocking_shell.Shell(self) # Config needs to find plugins via shell = instantiate shell first
        self.Config = config.Config(RootDir, self)
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
        self.messaging_admin = messaging_admin.message_admin(self)
        self.showOutput=True

    #wrapper to log function
    def log(self,*args):
        log(*args)
        
    def IsInScopeURL(self, URL): # To avoid following links to other domains
        ParsedURL = urlparse(URL)
        #URLHostName = URL.split("/")[2]
        for HostName in self.Config.GetAll('HOST_NAME'): # Get all known Host Names in Scope
            #if URLHostName == HostName:
            if ParsedURL.hostname == HostName:
                return True
        return False

    def CreateMissingDirs(self, Path):
        Dir = os.path.dirname(Path)
        if not os.path.exists(Dir):
            os.makedirs(Dir) # Create any missing directories

    def DumpFile(self, Filename, Contents, Directory):
        SavePath=Directory+WipeBadCharsForFilename(Filename)
        self.CreateMissingDirs(Directory)
        with open(SavePath, 'wb') as file:
            file.write(Contents)
        return SavePath

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
        return " ".join(argv).replace(os.path.dirname(argv[0])+"/", '')

    def AnonymiseCommand(self, Command):
        for Host in self.Config.GetAll('HOST_NAME'): # Host name setting value for all targets in scope
            if Host: # Value is not blank
                Command.replace(Host, 'some.target.com')
        return Command
        
    def StartProxy(self, Options):
        # The proxy along with supporting processes are started
        if Options["ProxyMode"]:
            if not os.path.exists(self.Config.Get('CACHE_DIR')):
                os.makedirs(self.Config.Get('CACHE_DIR'))
            else:
                shutil.rmtree(self.Config.Get('CACHE_DIR'))
                os.makedirs(self.Config.Get('CACHE_DIR'))
            InboundProxyOptions = [self.Config.Get('INBOUND_PROXY_IP'), self.Config.Get('INBOUND_PROXY_PORT')]    
            for folder_name in ['url', 'req-headers', 'req-body', 'resp-code', 'resp-headers', 'resp-body', 'resp-time']:
                folder_path = os.path.join(self.Config.Get('CACHE_DIR'), folder_name)
                if not os.path.exists(folder_path):
                    os.mkdir(folder_path)
            if self.Config.Get('COOKIES_BLACKLIST_NATURE'):
                regex_cookies_list = [ cookie + "=([^;]+;?)" for cookie in self.Config.Get('COOKIES_LIST') ]
                blacklist = True
            else:
                regex_cookies_list = [ "(" + cookie + "=[^;]+;?)" for cookie in self.Config.Get('COOKIES_LIST') ]
                blacklist = False
            regex_string = '|'.join(regex_cookies_list)
            cookie_regex = re.compile(regex_string)
            cookie_filter = {'BLACKLIST':blacklist, 'REGEX':cookie_regex}
            self.ProxyProcess = proxy.ProxyProcess( self,
                                                    self.Config.Get('INBOUND_PROXY_PROCESSES'),
                                                    InboundProxyOptions,
                                                    self.Config.Get('CACHE_DIR'),
                                                    self.Config.Get('INBOUND_PROXY_SSL'),
                                                    cookie_filter,
                                                    Options['OutboundProxy'],
                                                    Options['OutboundProxyAuth']
                                                  )
            self.TransactionLogger = transaction_logger.TransactionLogger(self)
            cprint("Started Inbound proxy at " + self.Config.Get('INBOUND_PROXY'))
            self.ProxyProcess.start()
            # self.TransactionLogger.start() # <= OMG!!! Have to fix this :P
            self.Requester = requester.Requester(self, InboundProxyOptions)
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
        infohandler = logging.FileHandler('/tmp/logfile',mode="w+")
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
        self.Config.ProcessOptions(Options)
        self.initlogger()

        self.Timer = timer.Timer(self.Config.Get('DATE_TIME_FORMAT')) # Requires user config
        self.Timer.StartTimer('core')
        self.initialise_plugin_handler_and_params(Options)
        if Options['ListPlugins']:
            self.PluginHandler.ShowPluginList()
            self.exitOutput()
            return False # No processing required, just list available modules
        self.DB = db.DB(self) # DB is initialised from some Config settings, must be hooked at this point

        self.DB.Init()
        self.messaging_admin.Init()
        Command = self.GetCommand(Options['argv'])
        self.DB.Run.StartRun(Command) # Log owtf run options, start time, etc
        if self.Config.Get('SIMULATION'):
            cprint("WARNING: In Simulation mode plugins are not executed only plugin sequence is simulated")
        self.StartProxy(Options)
        if self.ProxyMode:
            cprint("Proxy Mode is activated. Press Enter to continue to owtf")
            cprint("Visit http://" + self.Config.Get('INBOUND_PROXY') + "/proxy to use Plug-n-Hack standard")
            raw_input()
            self.TransactionLogger.start()
        # Proxy Check
        ProxySuccess, Message = self.Requester.ProxyCheck()
        cprint(Message)
        if not ProxySuccess: # Regardless of interactivity settings if the proxy check fails = no point to move on
            self.Error.FrameworkAbort(Message) # Abort if proxy check failed
        # Each Plugin adds its own results to the report, the report is updated on the fly after each plugin completes (or before!)
        self.Error.SetCommand(self.AnonymiseCommand(Command)) # Set anonymised invoking command for error dump info
        return True

    def initialise_plugin_handler_and_params(self, Options):
        self.PluginHandler = plugin_handler.PluginHandler(self, Options)
        self.PluginParams = plugin_params.PluginParams(self, Options)

    def run_plugins(self):
        Status = self.PluginHandler.ProcessPlugins()
        if Status['AllSkipped']:
            self.Finish('Complete: Nothing to do')
        elif not Status['SomeSuccessful'] and Status['SomeAborted']:
            self.Finish('Aborted')
            return False
        elif not Status['SomeSuccessful']: # Not a single plugin completed successfully, major crash or something
            self.Finish('Crashed')
            return False
        return True # Scan was successful

    def Finish(self, Status = 'Complete', Report = True):
        if self.Config.Get('SIMULATION'):
            if hasattr(self,'messaging_admin'):
                self.messaging_admin.finishMessaging()
            self.exitOutput()    
            exit()
        else:
            try:
                cprint("Saving DBs")
                self.DB.Run.EndRun(Status)
                self.DB.SaveDBs() # Save DBs prior to producing the report :)
                if Report:
                    cprint("Finishing iteration and assembling report again (with updated run information)")
                    PreviousTarget = self.Config.GetTarget()
                    for Target in self.Config.GetTargets(): # We have to finish all the reports in this run to update run information
                        self.Config.SetTarget(Target) # Much save the report for each target
                        self.Reporter.ReportFinish() # Must save the report again at the end regarless of Status => Update Run info
                    self.Config.SetTarget(PreviousTarget) # Restore previous target
                cprint("owtf iteration finished")
                if self.DB.ErrorCount() > 0: # Some error occurred (counter not accurate but we only need to know if sth happened)
                    cprint("Please report the sanitised errors saved to "+self.Config.Get('ERROR_DB'))
                #self.dbHandlerProcess.join()    
            except AttributeError: # DB not instantiated yet!
                cprint("owtf finished: No time to report anything! :P")
            finally:
                if self.ProxyMode:
                    try:
                        cprint("Stopping inbound proxy processes and cleaning up, Please wait!")
                        self.KillChildProcesses(self.ProxyProcess.pid)
                        self.ProxyProcess.terminate()
                        # No signal is generated during closing process by terminate()
                        os.kill(int(self.TransactionLogger.pid), signal.SIGINT)
                    except: # It means the proxy was not started
                        pass
                if hasattr(self,'messaging_admin'):
                    self.messaging_admin.finishMessaging()
                self.exitOutput()
                exit()

    def exitOutput(self):
        if hasattr(self,'outputthread'):
            self.outputqueue.put('end')    
            self.outputthread.join()
            if os.path.exists("owtf_review"):
                shutil.move("/tmp/logfile", "owtf_review")
        
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
                    
def Init(RootDir):
    return Core(RootDir)
