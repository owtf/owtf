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
from sqlalchemy import create_engine, event, exc
from sqlalchemy.engine import Engine
from sqlalchemy.pool import NullPool
from framework.db import models, plugin_manager, target_manager, resource_manager, \
    config_manager, poutput_manager, transaction_manager, url_manager, \
    command_register, error_manager, mapping_manager, vulnexp_manager, \
    session_manager, worklist_manager
import logging
import os
import re
from framework.utils import FileOperations


class DB(BaseComponent, DBInterface):

    COMPONENT_NAME = "db"

    def __init__(self):
        self.register_in_service_locator()
        self.config = self.get_component("config")
        self.error_handler = self.get_component("error_handler")
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
        self._db_settings = self._get_db_settings()
        self.create_session()

    def init(self):
        self.config = self.get_component("config")
        self.Transaction = self.get_component("transaction")
        self.URL = self.get_component("url_manager")
        self.Plugin = self.get_component("db_plugin")
        self.POutput = self.get_component("plugin_output")
        self.Target = self.get_component("target")
        self.Resource = self.get_component("resource")
        self.Config = self.get_component("db_config")
        self.Error = self.get_component("db_error")
        self.CommandRegister = self.get_component("command_register")
        self.Mapping = self.get_component("mapping_db")
        self.error_handler = self.get_component("error_handler")
        self.OWTFSession = self.get_component("session_db")
        self.Worklist = self.get_component("worklist_manager")
        #self.Vulnexp = self.get_component("vulnexp_db")
        self.DBHealthCheck()

    def get_category(self, plugin_code):
        return self.Mapping.GetCategory(plugin_code)

    def DBHealthCheck(self):
        # TODO: Fix this for psotgres
        return
        self.Target.DBHealthCheck()

    def create_session(self):
        self.Session = self.CreateScopedSession()
        self.session = self.Session()

    def clean_up(self):
        """Close the sqlalchemy session opened by DB."""
        self.session.close()

    def _get_db_settings(self):
        """Create DB settings according to the configuration file."""
        config_path = os.path.expanduser(
            self.config.FrameworkConfigGet('DATABASE_SETTINGS_FILE'))
        settings = {}
        with FileOperations.open(config_path, 'r') as f:
            for line in f:
                line = line.rstrip()
                # Ignore empty/comment lines.
                if not line or line.startswith('#'):
                    continue
                try:
                    key, value = line.split(':')
                    settings[key.strip()] = value.strip()
                except ValueError:
                    self.error_handler.FrameworkAbort(
                        "Problem in config file: '%s' -> Cannot parse line: %s"
                        % (config_path, line))
        return settings

    def CreateEngine(self, BaseClass):
        try:
            engine = create_engine(
                "postgresql+psycopg2://{0}:{1}@{2}:{3}/{4}".format(
                    self._db_settings['DATABASE_USER'],
                    self._db_settings['DATABASE_PASS'],
                    self._db_settings['DATABASE_IP'],
                    self._db_settings['DATABASE_PORT'],
                    self._db_settings['DATABASE_NAME']),
                poolclass=NullPool)  # TODO: Fix for forking
            BaseClass.metadata.create_all(engine)
            return engine
        except KeyError:  # Indicates incomplete db config file
            self.error_handler.FrameworkAbort(
                "Incomplete database configuration settings in "
                "" + self.config.FrameworkConfigGet('DATABASE_SETTINGS_FILE'))
        except exc.OperationalError as e:
            self.error_handler.FrameworkAbort(
                "[DB] " + str(e) + "\nRun scripts/db_run.sh to start/setup db")

    def CreateScopedSession(self):
        # Not to be used apart from main process, use CreateSession instead
        self.engine = self.CreateEngine(models.Base)
        session_factory = sessionmaker(bind=self.engine)
        return scoped_session(session_factory)
