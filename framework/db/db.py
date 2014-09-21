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
from framework.dependency_management.dependency_resolver import BaseComponent
from framework.dependency_management.interfaces import DBInterface
from framework.lib.general import cprint
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import create_engine, event
from sqlalchemy import exc
from framework.db import models, plugin_manager, target_manager, resource_manager, \
        config_manager, poutput_manager, transaction_manager, url_manager, \
        command_register, error_manager, mapping_manager, vulnexp_manager
import logging
import os
import re
from framework.utils import FileOperations


def re_fn(regexp, item):
    # TODO: Can remove this after ensuring that nothing is using this in DB calls
    #                                                           - tunnelshade
    regex = re.compile(regexp, re.IGNORECASE | re.DOTALL) # Compile before the loop for speed
    results = regex.findall(item)
    return results

class DB(BaseComponent, DBInterface):

    COMPONENT_NAME = "db"

    def __init__(self):
        self.register_in_service_locator()
        self.config = None
        self.ErrorDBSession = None
        self.Transaction = None
        self.URL = None
        self.Plugin = None
        self.POutput = None
        self.Target = None
        self.Resource = None
        self.Error = None
        self.CommandRegister = None
        self.Mapping = None
        self.Vulnexp = None

    def Init(self):
        self.config = self.get_component("config")
        FileOperations.create_missing_dirs(os.path.join(self.config.FrameworkConfigGet("OUTPUT_PATH"), self.config.FrameworkConfigGet("DB_DIR")))
        self.ErrorDBSession = self.CreateScopedSession(self.config.FrameworkConfigGetDBPath("ERROR_DB_PATH"), models.ErrorBase)
        self.CommandRegister = self.get_component("command_register")
        self.Target = self.get_component("target")
        self.URL = self.get_component("url_manager")
        self.Transaction = self.get_component("transaction")
        self.Plugin = self.get_component("db_plugin")
        self.POutput = self.get_component("plugin_output")
        self.Resource = self.get_component("resource")
        self.Error = self.get_component("db_error")
        self.Mapping = self.get_component("mapping_db")
        self.Vulnexp = self.get_component("vulnexp_db")
        self.DBHealthCheck()

    def get_category(self, plugin_code):
        return self.Mapping.GetCategory(plugin_code)

    def DBHealthCheck(self):
        self.Target.DBHealthCheck()

    def SaveDBs(self):
        pass

    def EnsureDBWithBase(self, DB_PATH, BaseClass):
        logging.info("Ensuring if DB exists at " + DB_PATH)
        if not os.path.exists(DB_PATH):
            self.CreateDBUsingBase(DB_PATH, BaseClass)

    def CreateDBUsingBase(self, DB_PATH, BaseClass):
        logging.info("Creating DB at " + DB_PATH)
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
        logging.info("Creating Scoped session factory for " + DB_PATH)
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
                logging.info("Lock occured (might be)")
            finally:
                session.close()
                if success: return success
