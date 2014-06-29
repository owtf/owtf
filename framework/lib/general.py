#!/usr/bin/env python
"""
owtf is an OWASP+PTES-focused try to unite great tools and facilitate pen testing
Copyright (c) 2011, Abraham Aranguren <name.surname@gmail.com> Twitter: @7a_ http://7-a.org                                                        
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

This library contains helper functions and exceptions for the framework
"""

from collections import defaultdict
from framework.lib.filelock import FileLock
import logging
import multiprocessing
import os
import pprint
import random
import string
import sys
import threading
import time,base64

class FrameworkException(Exception):
    def __init__(self, value):
        self.parameter = value

    def __str__(self):
        return repr(self.parameter)

class FrameworkAbortException(FrameworkException):
    pass

class PluginAbortException(FrameworkException):
    pass

class UnreachableTargetException(FrameworkException):
    pass

class DBIntegrityException(FrameworkException):
    pass

class InvalidTargetReference(FrameworkException):
    pass

class InvalidTransactionReference(FrameworkException):
    pass

class InvalidParameterType(FrameworkException):
    pass

class InvalidWorkerReference(FrameworkException):
    pass

class InvalidConfigurationReference(FrameworkException):
    pass

def ConfigGet(Key): # Kludge wrapper function
        global Config # kludge global to avoid having to pass the config around to other components that need it (temporary until I figure out a better way!)
        return Config.Get(Key)

def cprint(Message):
        Pad = "[*] "
        print Pad+str(Message).replace("\n", "\n"+Pad)
        return Message

def p(Variable, CallFunctions = True):
        for i in dir(Variable):
                print i
                try:
                        Attrib = getattr(Variable, i)
                        print str(Attrib)
                        if CallFunctions and callable(Attrib):
                                Attrib()
                except:
                        pass
        cprint("depth = 1")
        pprint.PrettyPrinter(indent=4,depth=1).pprint(Variable)
        cprint("depth = 2")
        pprint.PrettyPrinter(indent=4,depth=2).pprint(Variable)
        cprint("pprint")
        pprint.pprint(Variable)
        cprint("print dir")
        cprint(dir(Variable))

# Perform multiple replacements in one go using the replace dictionary in format: { 'search' : 'replace' }
def MultipleReplace(Text, ReplaceDict):
        NewText = Text
        for Search,Replace in ReplaceDict.items():
                NewText = NewText.replace(Search, str(Replace))
        return NewText

def WipeBadCharsForFilename(Filename):
        return MultipleReplace(Filename, { '(':'', ' ':'_', ')':'', '/':'_' })

def RemoveListBlanks(src):
    return [el for el in src if el]

def List2DictKeys(List):
        Dictionary = defaultdict(list)
        for Item in List:
                Dictionary[Item] = ''
        return Dictionary

def AddToDict(FromDict, ToDict):
        for Key, Value in FromDict.items():
                if hasattr(Value, 'copy') and callable(getattr(Value, 'copy')):
                        ToDict[Key] = Value.copy()
                else:
                        ToDict[Key] = Value

def MergeDicts(Dict1, Dict2): # Returns a by-value copy contained the merged content of the 2 passed dictionaries
        NewDict = defaultdict(list)
        AddToDict(Dict1, NewDict)
        AddToDict(Dict2, NewDict)
        return NewDict
                 
def TruncLines(Str, NumLines, EOL = "\n"):
        return EOL.join(Str.split(EOL)[0:NumLines])

def DeriveHTTPMethod(Method, Data): # Derives the HTTP method from Data, etc
        DMethod = Method
        if DMethod == None or DMethod == '': # Method not provided: Determine method from params
                DMethod = 'GET'
                if Data != '' and Data != None:
                        DMethod = 'POST'
        return DMethod

def CallMethod(Object, Method, ArgList): # Calls Object.Method(ArgList) dynamically, this helps avoiding code repetition via wrapper convenience functions
        return getattr(Object, Method)(*ArgList)

def GetUnique(List):
        NewList = []
        for Item in List:
                if Item not in NewList:
                        NewList.append(Item)
        return NewList

def PathsExist(PathList):
        ValidPaths = True
        for Path in PathList:
                if Path and not os.path.exists(Path):
                        log("WARNING: The path '" + Path + "' does not exist!")
                        ValidPaths = False
        return ValidPaths

def GetFileAsList(Filename):
        try:
                Output = open(Filename, 'r').read().split("\n")
                cprint("Loaded file: '"+Filename+"'")
        except IOError, error:
                log("Cannot open file: '"+Filename+"' ("+str(sys.exc_info())+")")
                Output = []
        return Output

def AppendToFile(Filename, Data):
        try:
                #cprint("Writing to file: '"+Filename+"'")
                open(Filename, 'a').write(Data)
        except IOError, error:
                log("Cannot write to file: '"+Filename+"' ("+str(sys.exc_info())+")")

def get_files(request_dir):
    files = os.listdir(request_dir)
    files = [os.path.join(request_dir, f) for f in files if ".lock" not in f]
    files.sort(key=lambda x: os.path.getmtime(x))
    return files
#this function waits for the directory existance.
# if it doesnot it sleeps for delay seconds and then it try again
# if there is some exception it raises the exception
def wait_until_dir_exists(request_dir,delay):
    while True:
        if(os.path.exists(request_dir)):
            return
        time.sleep(delay)

#sleep delay for different sleeps
sleep_delay = 0.025
   
    
#this function writes to a file atomically
def atomic_write_to_file(dirname,file,data):
    filename = dirname+"/"+file
    try:
        
        with FileLock(filename):
            fd = open(filename,'w+')
            fd.write(data)
            fd.close()
            
        return 1
    except KeyboardInterrupt:
        raise KeyboardInterrupt
    except:
        return 0

#this function atomically read from the given file
#if skip_if_locked is true then it tries 2 times to acquire the lock and if 
#lock is not available it returns with ""
#else if skip_if_locked is false then default settings are used

def atomic_read_from_file(requests_dir, partial_filename, skip_if_locked = True):
    if skip_if_locked:
        delay=0.30
    else: 
        delay=30
    try:
        
        filename = requests_dir+"/"+partial_filename
        data=""
        while not os.path.exists(filename):
            #AppendToFile("file1", "file is not there "+filename+"\n")
            time.sleep(sleep_delay)
            
        with FileLock(filename, timeout=delay):
            fd = open(filename,'r')
            data = fd.read()
            fd.close()

        return data
    except KeyboardInterrupt:
        raise KeyboardInterrupt
    except:
        return ""    

def get_random_str(len):
    """function returns random strings of length len"""
    return base64.urlsafe_b64encode(os.urandom(len))[0:len]

    
#cleanly remove directories
def removeDirs(dir):
    for f in os.listdir(dir):
        os.remove(dir+"/"+f)
    os.rmdir(dir)

# Done through framework_config.cfg
# Files for messaging system
#OWTF_FILE_QUEUE_DIR = "/tmp/owtf/"
db_pushQ="push"
db_pullQ="pull"
QUEUES = {db_pushQ,db_pullQ}

#logging function
#log levels
CRITICAL = logging.CRITICAL
ERROR = logging.ERROR
WARNING = logging.WARNING
INFO = logging.INFO
DEBUG = logging.DEBUG
BENCHMARK = 0
#LOG_THRESHOLD=7

#log level to string mapping
LOG_LEVELS = { CRITICAL : 'CRITICAL'
            , ERROR : 'ERROR'
            , WARNING : 'WARNING'
            , INFO : 'INFO'
            , DEBUG : 'DEBUG' 
            ,BENCHMARK:'BENCHMARK'}

def get_short_info():
    fr = sys._getframe(3)
    #XXX ^-- still depends on call-depth.
    #XXX     we go from get_short_info-frame, up to log-frame, up to log's caller frame
    if 'self' in fr.f_locals:
        name = fr.f_locals['self'].__class__.__name__
        # we resolve 'self' if present and get the classname out of it
    else:
        name = fr.f_code.co_name
    return {'filename': fr.f_code.co_filename, 'name': name}
       
def get_source_info():
    """
    Retrieves the Source class, function, process and thread, useful to know/process based on where things came from
    """
    process_name = multiprocessing.current_process().name # Obviously, you need to create processes giving them a reasonable name for this to be useful!

    #XXX moving this code into another function/scope will cause it to FAIL.
    #XXX  the offests in inspect.stack() depend on the call stack. increasing
    #XXX  or decreasing function nesting will therefore mess things up.
    source = get_short_info()['name']
    return {
            'Process' : process_name
            , 'Thread' : threading.currentThread().getName() # MainThread if not threading
            , 'Source' : source # Class Name / Func Name logging the message
            }

def get_default_logger(source_info):
    """
        Give default log element for given source_info.. 
        For now it is simply returning general log
    """
    return logging.getLogger("general")
    
def get_default_logfile(source_info):
    """
        Give default log file for given source_info.. 
        For now it is simply returning log file given in config file
    """
    return logging.getLogger("logfile")

def log(message, type = INFO, overrides = {}.copy()):
    """
    Logs a message to call
    """
    source_info = get_source_info() # Retrieve Source class, function, process and thread
    defaultlog = overrides.get('Logger',get_default_logger(source_info))
    defaultfile = overrides.get('LogFile',get_default_logfile(source_info))
    if type!=BENCHMARK:
        defaultlog.info(message)
    log_enteries = {'processname':source_info['Process'],'functionname':source_info['Source'],'type':LOG_LEVELS[type]}
    defaultfile.info(message,extra=log_enteries)
