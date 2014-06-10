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
from framework.lib.general import cprint
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import create_engine, event
from sqlalchemy import exc
from framework.db import models, plugin_manager, target_manager, resource_manager, \
        config_manager, poutput_manager, transaction_manager, url_manager, \
        command_register, error_manager
import logging
import os
import re

def re_fn(regexp, item):
    # TODO: Can remove this after ensuring that nothing is using this in DB calls
    #                                                           - tunnelshade
    regex = re.compile(regexp, re.IGNORECASE | re.DOTALL) # Compile before the loop for speed
    results = regex.findall(item)
    return results

class DB(object):
        
    def __init__(self,CoreObj):
        self.Core = CoreObj
        self.Core.CreateMissingDirs(os.path.join(self.Core.Config.FrameworkConfigGet("OUTPUT_PATH"), self.Core.Config.FrameworkConfigGet("DB_DIR")))
        #self.Run = run_manager.RunManager(CoreObj)
        #self.PluginRegister = plugin_register.PluginRegister(CoreObj)
        #self.ReportRegister = report_register.ReportRegister(CoreObj)
        #self.CommandRegister = command_register.CommandRegister(CoreObj)
        #self.Debug = debug.DebugDB(CoreObj)

    def Init(self):
        self.ErrorDBSession = self.CreateScopedSession(self.Core.Config.FrameworkConfigGetDBPath("ERROR_DB_PATH"), models.ErrorBase)
        self.Transaction = transaction_manager.TransactionManager(self.Core)
        self.URL = url_manager.URLManager(self.Core)
        self.Plugin = plugin_manager.PluginDB(self.Core)
        self.POutput = poutput_manager.POutputDB(self.Core)
        self.Target = target_manager.TargetDB(self.Core)
        self.Resource = resource_manager.ResourceDB(self.Core)
        self.Config = config_manager.ConfigDB(self.Core)
        self.Error = error_manager.ErrorDB(self.Core)
        self.CommandRegister = command_register.CommandRegister(self.Core)
        self.DBHealthCheck()

    def DBHealthCheck(self):
        self.Target.DBHealthCheck()

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
        @event.listens_for(engine, "begin")
        def do_begin(conn):
            conn.connection.create_function('regexp', 2, re_fn)
        session_factory = sessionmaker(bind = engine)
        cprint("Creating Scoped session factory for " + DB_PATH)
        return scoped_session(session_factory)

    def CreateSession(self, DB_PATH):
        engine = create_engine("sqlite:///" + DB_PATH)
        @event.listens_for(engine, "begin")
        def do_begin(conn):
            conn.connection.create_function('regexp', 2, re_fn)
        return sessionmaker(bind = engine)

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
