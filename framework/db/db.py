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
from framework.db import models, plugin, target, resource, config
import json
import logging
import multiprocessing
import os
import random
import string

class DB(object):
        
    def __init__(self,CoreObj):
        self.Core = CoreObj
        self.Core.EnsureDirPath(self.Core.Config.FrameworkConfigGet("DB_DIR"))
        #self.Run = run_manager.RunManager(CoreObj)
        #self.PluginRegister = plugin_register.PluginRegister(CoreObj)
        #self.ReportRegister = report_register.ReportRegister(CoreObj)
        #self.CommandRegister = command_register.CommandRegister(CoreObj)
        #self.Debug = debug.DebugDB(CoreObj)

    def Init(self):
        self.ErrorDBSession = self.CreateScopedSession(os.path.expanduser(self.Core.Config.FrameworkConfigGet("ERROR_DB_PATH")), models.ErrorBase)
        self.Transaction = transaction_manager.TransactionManager(self.Core)
        self.URL = url_manager.URLManager(self.Core)
        self.Plugin = plugin.PluginDB(self.Core)
        self.Target = target.TargetDB(self.Core)
        self.Resource = resource.ResourceDB(self.Core)
        self.Config = config.ConfigDB(self.Core)
        # self.DBHealthCheck()

    def SaveDBs(self):
        pass

    def EnsureDBWithBase(self, DB_PATH, BaseClass):
        cprint("Ensuring if DB exists at " + DB_PATH)
        if not os.path.exists(DB_PATH):
            self.CreateDBUsingBase(DB_PATH, BaseClass)

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

    def TransactionDBSessionForTarget(self, target_url):
        db_path = self.Core.Config.GetTransactionDBPathForTarget(target_url)
        return self.CreateSession(db_path)

    def TransactionDBSession(self):
        return self.TransactionDBSessionForTarget(self.Core.Config.Target)

    def SearchTransactionDB(self, Criteria):
        # Criteria = { 'URL' : URL.strip(), 'Method' : Method, 'Data' : self.DerivePOSTToStr(Data) }
        Session = self.TransactionDBSession()
        db_session = Session()
        results = db_session.query(models.Transaction).filter_by(url=Criteria.get('URL')).all()
        db_session.close()
        return results

    def UrlDBSessionForTarget(self, target_url):
        db_path = self.Core.Config.GetUrlDBPathForTarget(target_url)
        return self.CreateSession(db_path)

    def UrlDBSession(self):
        return self.UrlDBSessionForTarget(self.Core.Config.Target)

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
