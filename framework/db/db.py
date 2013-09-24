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
from framework.db import db_handler, transaction_manager, url_manager, \
    run_manager, plugin_register, report_register, command_register, debug

from framework.db.db_client import *
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

class DB:
        
    def __init__(self,CoreObj):
        self.core = CoreObj
        self.DBHandler = db_handler.DBHandler(CoreObj)
        self.Transaction = transaction_manager.TransactionManager(CoreObj)
        self.URL = url_manager.URLManager(CoreObj)
        self.Run = run_manager.RunManager(CoreObj)
        self.PluginRegister = plugin_register.PluginRegister(CoreObj)
        self.ReportRegister = report_register.ReportRegister(CoreObj)
        self.CommandRegister = command_register.CommandRegister(CoreObj)
        self.Debug = debug.DebugDB(CoreObj)

    def Init(self):
        self.DBHandler.Init()
      
    #these all functions call db_pull or db_push to do request
    def GetFieldSeparator(self):
        return self.DBHandler.GetFieldSeparator()

    def GetPath(self, DBName):
        arguments={'function':'GetPath','arguments':[DBName]}
        return db_pull(arguments)

    def Get(self, DBName, Path = None):
        arguments={'function':'Get','arguments':[DBName,Path]}
        return db_pull(arguments)

    def GetData(self, DBName, Path = None):
        arguments={'function':'GetData','arguments':[DBName,Path]}
        return db_pull(arguments)

    def GetRecord(self, DBName, Index, Path = None):
        arguments={'function':'GetRecord','arguments':[DBName,Index,Path]}
        return db_pull(arguments)

    def ModifyRecord(self, DBName, Index, Value, Path = None):
        arguments={'function':'ModifyRecord','arguments':[DBName,Index, Value,Path]}
        return db_push(arguments)

    def GetRecordAsMatch(self, Record, NAME_TO_OFFSET):
        arguments={'function':'GetRecordAsMatch','arguments':[Record, NAME_TO_OFFSET]}
        return db_pull(arguments)

    def Search(self, DBName, Criteria, NAME_TO_OFFSET): # Returns DB Records in an easy-to-use dictionary format { 'field1' : 'value1', ... }
        arguments={'function':'Search', 'arguments':[DBName, Criteria, NAME_TO_OFFSET]}
        return db_pull(arguments)

    def GetSyncCount(self, DBName, Path = None):
        arguments={'function':'GetSyncCount', 'arguments':[DBName, Path]}
        return db_pull(arguments)

    def IncreaseSync(self, DBName, Path = None):
        arguments={'function':'IncreaseSync', 'arguments':[DBName, Path]}
        return db_push(arguments)

    def CalcSync(self, DBName, Path = None):
        arguments={'function':'CalcSync', 'arguments':[DBName, Path]}
        return db_push(arguments)

    def Add(self, DBName, Data, Path = None):
        arguments={'function':'Add','arguments':[DBName, Data,Path]}
        return db_push(arguments)

    def GetLength(self, DBName, Path = None):
        arguments={'function':'GetLength', 'arguments':[DBName, Path]}
        return int(db_pull(arguments))
    
    def IsEmpty(self, DBName, Path = None):
        arguments={'function':'IsEmpty','arguments':[DBName, Path]}
        return db_pull(arguments)
    
    def GetDBNames(self):
        arguments={'function':'GetDBNames','arguments':[]}
        return db_pull(arguments)
    
    def GetNextHTMLID(self):
        arguments={'function':'GetNextHTMLID','arguments':[]}
        return db_pull(arguments)
    
    def LoadDB(self, Path, DBName): # Load DB to memory
        arguments={'function':'LoadDB','arguments':[Path,DBName]}
        return db_push(arguments)
    
    def SaveDBs(self):
        arguments={'function':'SaveDBs','arguments':[]}
        return db_push(arguments)

    def SaveDBLine(self, file, DBName, Line): # Contains the logic on how each line must be saved depending on the type of DB
        arguments={'function':'SaveDBLine', 'arguments':[file, DBName, Line]}
        return db_push(arguments)
    
    def SaveDB(self, Path, DBName):
        arguments={'function':'SaveDB','arguments':[Path, DBName]}
        return db_push(arguments)
    
    def GetSeed(self):
        arguments={'function':'GetSeed','arguments':[]}
        return db_pull(arguments)

    def AddError(self, ErrorTrace):
        arguments={'function':'AddError', 'arguments':[ErrorTrace]}
        return db_push(arguments)
    
    def ErrorCount(self):
        arguments={'function':'ErrorCount','arguments':[]}
        return db_pull(arguments,"pull")
    
    #callback function which calls DB functions and is invoked by messaging server
    def db_callback_function(self,data,response_type):
        message = json.loads(data)
        function = message['function']
        args = message['arguments']
    #checks if function is valid or not
        if(is_valid(function, args, response_type)):

            result = CallMethod(self.DBHandler, function, args)
            return json.dumps(result)