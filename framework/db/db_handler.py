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

This file handles all the database transactions.
'''
from framework.logQueue import logQueue
import json
import logging
import multiprocessing
import os
import random
import string

DB_Handler = '/tmp/owtf/db_handler'
Request_Folder = DB_Handler+"/request"
Response_Folder = DB_Handler+"/response"
file_name_length=50

class DBHandler:
        
    def __init__(self,CoreObj):
        self.core = CoreObj
        self.core.Shell.shell_exec("rm -rf "+DB_Handler)
        self.core.Shell.shell_exec("mkdir /tmp/owtf")
        self.core.Shell.shell_exec("mkdir "+DB_Handler)
        self.core.Shell.shell_exec("mkdir "+Request_Folder)
        self.core.Shell.shell_exec("mkdir "+Response_Folder)
      
    def randomnum(self):
        return ''.join(random.choice(string.lowercase) for x in range(file_name_length))  
      
    def dorequest(self,args):
        content = json.dumps(args)
        pid = self.randomnum()
        self.filename = pid
        filename = Request_Folder+"/"+str(pid)
        try:
            while(os.path.exists(filename)==True):
                pass
        except KeyboardInterrupt:
            raise KeyboardInterrupt    
        #print "requesting "+filename + "writing "+str(args)
        fo = open(filename, "w+")
        fo.write(content);
        fo.close()

    def getresponse(self):
        pid = self.filename
        filename = Response_Folder+"/"+str(pid)
        try:
            while(os.path.exists(filename)==False):
                pass
            while os.path.getsize(filename)==0:
                pass
        except KeyboardInterrupt:
            raise KeyboardInterrupt    
        fo = open(filename, "r")
        content = fo.read()
        fo.close()
        #print "deleting response file "+ filename
        self.core.Shell.shell_exec("rm -rf "+filename)
        return json.loads(content)
    
    def process_request(self,pid):
        filename = Request_Folder+"/"+str(pid)
        #print "reading request "+filename
        try:
            while os.path.getsize(filename)==0:
                pass
        except KeyboardInterrupt:
            raise KeyboardInterrupt    
        fo = open(filename, "r")
        content = fo.readline()
        fo.close()
        #print "request gonne be "+content
        request = json.loads(content)
        self.core.Shell.shell_exec("rm -rf "+filename)
            
        flag = True
        function = request[0]
        #print "function is "+function
        if function == 'GetFieldSeparator':
            response = self.core.DB.GetFieldSeparator()
        elif function == 'GetPath':
            DBName = request[1]
            response = self.core.DB.GetPath(DBName)
        elif function == 'Get':
            DBName = request[1]
            Path = request[2]
            response = self.core.DB.Get(DBName,Path)
        elif function == 'GetData':
            DBName = request[1]
            Path = request[2]
            response = self.core.DB.GetData(DBName,Path)
        elif function == 'GetRecord':
            DBName = request[1]
            index = request[2]
            Path = request[3]
            response = self.core.DB.GetRecord(DBName,index,Path)             
        elif function == 'ModifyRecord':
            flag=False
            DBName = request[1]
            index = request[2]
            value = request[3]
            Path = request[4]
            response = self.core.DB.ModifyRecord(DBName,index,value,Path)
        elif function == 'GetRecordAsMatch':
            Record = request[1]
            NAME_TO_OFFSET= request[2]
            response = self.core.DB.GetRecordAsMatch(Record,NAME_TO_OFFSET) 
        elif function == 'Search':
            DBName = request[1]   
            Criteria = request[2]
            NAME_TO_OFFSET= request[3] 
            response = self.core.DB.Search(DBName,Criteria,NAME_TO_OFFSET)
        elif function == 'GetSyncCount': 
            DBName = request[1]
            Path = request[2]
            response = self.core.DB.GetSyncCount(DBName,Path)
        elif function == 'IncreaseSync':
            flag=False
            DBName = request[1]
            Path = request[2]
            response = self.core.DB.IncreaseSync(DBName,Path)
        elif function == 'CalcSync':
            flag=False
            DBName = request[1]
            Path = request[2]
            response = self.core.DB.CalcSync(DBName,Path) 
        elif function == 'Add':
            flag=False
            DBName = request[1]
            Data = request[2]
            Path = request[3]
            response = self.core.DB.Add(DBName,Data,Path)
        elif function == 'GetLength':
            DBName = request[1]
            Path = request[2]
            response = self.core.DB.GetLength(DBName,Path)         
        elif function == 'IsEmpty':
            DBName = request[1]
            Path = request[2]
            response = self.core.DB.IsEmpty(DBName,Path)
        elif function == 'GetDBNames':
            response = self.core.DB.GetDBNames()              
        elif function == 'GetNextHTMLID':
            response = self.core.DB.GetNextHTMLID()
        elif function == 'LoadDB':
            flag=False
            Path = request[1]
            DBName = request[2]
            response = self.core.DB.LoadDB(Path,DBName)     
        elif function == 'SaveDBs':
            flag=False
            response = self.core.DB.SaveDBs()       
        elif function == 'SaveDBLine':
            flag=False
            file = request[1]
            DBName = request[2]
            Line = request[3]
            response = self.core.DB.SaveDBLine(file,DBName,Line)
        elif function ==  'SaveDB':
            flag=False  
            Path = request[1]
            DBName = request[2]
            response = self.core.DB.SaveDB(Path,DBName)
        elif function == 'GetSeed':
            response = self.core.DB.GetSeed()
        elif function == 'AddError':
            flag=False
            ErrorTrace = request[1]
            response = self.core.DB.AddError()            
        elif function == 'ErrorCount':
            response = self.core.DB.ErrorCount()    
        if flag:
            
            content = json.dumps(response)
            
            filename = Response_Folder+"/"+str(pid)
            #print "writing response "+filename
            fo = open(filename, "w+")
            fo.write(content);
            fo.close()
   
    def GetFieldSeparator(self):
        arguments=['GetFieldSeparator']
        self.dorequest(arguments)
        return self.getresponse()

    def GetPath(self, DBName):
        arguments=['GetPath',DBName]
        self.dorequest(arguments)
        return self.getresponse()

    def Get(self, DBName, Path = None):
        arguments=['Get',DBName,Path]
        self.dorequest(arguments)
        return self.getresponse()

    def GetData(self, DBName, Path = None):
        arguments=['GetData',DBName,Path]
        self.dorequest(arguments)
        return self.getresponse()

    def GetRecord(self, DBName, Index, Path = None):
        arguments=['GetRecord',DBName,Index,Path]
        self.dorequest(arguments)
        return self.getresponse()

    def ModifyRecord(self, DBName, Index, Value, Path = None):
        arguments=['ModifyRecord',DBName,Index, Value,Path]
        self.dorequest(arguments)

    def GetRecordAsMatch(self, Record, NAME_TO_OFFSET):
        arguments=['GetRecordAsMatch',Record, NAME_TO_OFFSET]
        self.dorequest(arguments)
        return self.getresponse()

    def Search(self, DBName, Criteria, NAME_TO_OFFSET): # Returns DB Records in an easy-to-use dictionary format { 'field1' : 'value1', ... }
        arguments=['Search', DBName, Criteria, NAME_TO_OFFSET]
        self.dorequest(arguments)
        return self.getresponse()

    def GetSyncCount(self, DBName, Path = None):
        arguments=['GetSyncCount', DBName, Path]
        self.dorequest(arguments)
        return self.getresponse()

    def IncreaseSync(self, DBName, Path = None):
        arguments=['IncreaseSync', DBName, Path]
        self.dorequest(arguments)

    def CalcSync(self, DBName, Path = None):
        arguments=['CalcSync', DBName, Path]
        self.dorequest(arguments)

    def Add(self, DBName, Data, Path = None):
        arguments=['Add', DBName, Data,Path]
        self.dorequest(arguments)

    def GetLength(self, DBName, Path = None):
        arguments=['GetLength', DBName, Path]
        self.dorequest(arguments)
        return self.getresponse()
    
    def IsEmpty(self, DBName, Path = None):
        arguments=['IsEmpty', DBName, Path]
        self.dorequest(arguments)
        return self.getresponse()

    def GetDBNames(self):
        arguments=['GetDBNames']
        self.dorequest(arguments)
        return self.getresponse()

    def GetNextHTMLID(self):
        arguments=['GetNextHTMLID']
        self.dorequest(arguments)
        return self.getresponse()
            
    def LoadDB(self, Path, DBName): # Load DB to memory
        arguments=['LoadDB',Path,DBName]
        self.dorequest(arguments)
        
    def SaveDBs(self):
        arguments=['SaveDBs']
        self.dorequest(arguments)

    def SaveDBLine(self, file, DBName, Line): # Contains the logic on how each line must be saved depending on the type of DB
        arguments=['SaveDBLine', file, DBName, Line]
        self.dorequest(arguments)

    def SaveDB(self, Path, DBName):
        arguments=['SaveDB', Path, DBName]
        self.dorequest(arguments)
    
    def GetSeed(self):
        arguments=['GetSeed']
        self.dorequest(arguments)
        return self.getresponse()

    def AddError(self, ErrorTrace):
        arguments=['AddError', ErrorTrace]
        self.dorequest(arguments)

    def ErrorCount(self):
        arguments=['ErrorCount']
        self.dorequest(arguments)
        return self.getresponse()
    
    def handledb(self):
        while 1:
            if(len(os.walk(Request_Folder).next()[2]) > 0):
                    files = os.listdir(Request_Folder)
                    files = [os.path.join(Request_Folder, f) for f in files] # add path to each file
                    files.sort(key=lambda x: os.path.getmtime(x))
                    for f in files:
                       ar = f.split('/')
                       pid = ar[len(ar)-1]
                       self.process_request(pid)
        
