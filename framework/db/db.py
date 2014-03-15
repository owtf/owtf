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
from framework.lib.general import cprint
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import create_engine
from sqlalchemy import exc
from framework.db import models
import json
import logging
import multiprocessing
import os
import random
import string

class DB(object):
        
    def __init__(self,CoreObj):
        self.Core = CoreObj
        self.Transaction = transaction_manager.TransactionManager(CoreObj)
        self.URL = url_manager.URLManager(CoreObj)
        #self.Run = run_manager.RunManager(CoreObj)
        #self.PluginRegister = plugin_register.PluginRegister(CoreObj)
        #self.ReportRegister = report_register.ReportRegister(CoreObj)
        #self.CommandRegister = command_register.CommandRegister(CoreObj)
        #self.Debug = debug.DebugDB(CoreObj)

    def Init(self):
        self.Core.EnsureDirPath(self.Core.Config.FrameworkConfigGet("DB_DIR"))
        self.ErrorDBSession = self.CreateScopedSession(os.path.expanduser(self.Core.Config.FrameworkConfigGet("ERROR_DB_PATH")), models.ErrorBase)
        self.TargetConfigDBSession = self.CreateScopedSession(os.path.expanduser(self.Core.Config.FrameworkConfigGet("TARGET_CONFIG_DB_PATH")), models.TargetBase)
        self.ResourceDBSession = self.CreateScopedSession(os.path.expanduser(self.Core.Config.FrameworkConfigGet("RESOURCE_DB_PATH")), models.ResourceBase)
        self.ConfigDBSession = self.CreateScopedSession(os.path.expanduser(self.Core.Config.FrameworkConfigGet("CONFIG_DB_PATH")), models.GeneralBase)
        self.DBHealthCheck()
        self.LoadDBs()

    def LoadDBs(self):
        self.LoadResourceDBFromFile(self.Core.Config.FrameworkConfigGet("DEFAULT_RESOURCES_PROFILE"))
        self.LoadConfigDBFromFile(self.Core.Config.FrameworkConfigGet("DEFAULT_GENERAL_PROFILE"))

    def DBHealthCheck(self):
        session = self.TargetConfigDBSession()
        target_list = session.query(models.Target).all()
        for target in target_list:
            self.Core.Config.Targets.append(target.url)
            self.EnsureDBsForTarget(target.url)

    def EnsureDBsForTarget(self, TargetURL):
        self.Core.Config.CreateDBDirForTarget(TargetURL)
        self.EnsureDBWithBase(self.Core.Config.GetTransactionDBPathForTarget(TargetURL), models.TransactionBase)
        self.EnsureDBWithBase(self.Core.Config.GetUrlDBPathForTarget(TargetURL), models.URLBase)
        self.EnsureDBWithBase(self.Core.Config.GetReviewDBPathForTarget(TargetURL), models.ReviewWebBase)

    def EnsureDBWithBase(self, DB_PATH, BaseClass):
        cprint("Ensuring if DB exists at " + DB_PATH)
        if not os.path.exists(DB_PATH):
            self.CreateDBUsingBase(DB_PATH, BaseClass)

    def LoadResourceDBFromFile(self, file_path): # This needs to be a list instead of a dictionary to preserve order in python < 2.7
        cprint("Loading Resources from: " + file_path + " ..")
        ConfigFile = open(file_path, 'r').read().splitlines() # To remove stupid '\n' at the end
        session = self.ResourceDBSession()
        for line in ConfigFile:
            if '#' == line[0]:
                continue # Skip comment lines
            try:
                Type, Name, Resource = line.split('_____')
                # Resource = Resource.strip()
                session.add(models.Resource(resource_type = Type, resource_name = Name, resource = Resource))
            except ValueError:
                cprint("ERROR: The delimiter is incorrect in this line at Resource File: "+str(line.split('_____')))
        session.commit()
        session.close()

    def LoadConfigDBFromFile(self, file_path):
        cprint("Loading Configuration from: " + file_path + " ..")
        ConfigFile = open(file_path, 'r').read().splitlines() # To remove stupid '\n' at the end
        session = self.ConfigDBSession()
        for line in ConfigFile:
            if not line or '#' == line[0]: continue
            try:
                key, value = line.split(":", 1)
                key, value = key.strip(), value.strip()
                session.add(models.ConfigSetting(key = key, value = value))
            except ValueError:
                cprint(line)
                cprint("Invalid configuration line")
        session.commit()
        session.close()

    def CreateDBUsingBase(self, DB_PATH, BaseClass):
        cprint("Creating DB at " + DB_PATH)
        engine = create_engine("sqlite:///" + DB_PATH)
        BaseClass.metadata.create_all(engine)
        return engine

    def CreateScopedSession(self, DB_PATH, BaseClass):
        # Not to be used apart from main process, use CreateSession instead
        if not os.path.exists(DB_PATH):
            engine = self.CreateDBUsingBase(DB_PATH, BaseClass)
        else:
            engine = create_engine("sqlite:///" + DB_PATH)
        session_factory = sessionmaker(bind = engine)
        cprint("Creating Scoped session factory for " + DB_PATH)
        return scoped_session(session_factory)

    def CreateSession(self, DB_PATH):
        engine = create_engine("sqlite:///" + DB_PATH)
        return sessionmaker(bind = engine)

    def GetTargetConfigFromDB(self, target_url):
        session = self.TargetConfigDBSession()
        return session.query(models.Target).get(target_url)

    def TransactionDBSessionForTarget(self, target_url):
        db_path = self.Core.Config.GetTransactionDBPathForTarget(target_url)
        return self.CreateSession(db_path)

    def UrlDBSessionForTarget(self, target_url):
        db_path = self.Core.Config.GetUrlDBPathForTarget(target_url)
        return self.CreateSession(db_path)

    def AddUsingSession(self, Obj, session):
        while True:
            try:
                session = session()
                session.add(Obj)
                session.commit()
                success = True
            except exc.OperationalError:
                cprint("Lock occured (might be)")
            finally:
                session.close()
                if success: return success

    def AddError(self, errorObj):
        self.AddUsingSession(errorObj, self.ErrorDBSession)

    def ErrorCount(self):
        session = self.ErrorDBSession()
        count = session.query(models.Error).count()
        return count

    def ErrorData(self):
        arguments={'function':'ErrorData','arguments':[]}
        return db_pull(arguments)

    def GetValueFromConfigDB(self, Key):
        session = self.ConfigDBSession()
        obj = session.query(models.ConfigSetting).get(Key)
        session.close()
        if obj:
            return(obj.value)
        return(None)
