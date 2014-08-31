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
from sqlalchemy import create_engine, event, exc
from sqlalchemy.engine import Engine
from sqlalchemy.pool import NullPool
from framework.db import models, plugin_manager, target_manager, resource_manager, \
    config_manager, poutput_manager, transaction_manager, url_manager, \
    command_register, error_manager, mapping_manager, vulnexp_manager, \
    session_manager
import logging
import os
import re


class DB(object):

    def __init__(self,CoreObj):
        self.Core = CoreObj
        # Fetch settings only once for consistency
        self._db_settings = self._get_db_settings()
        # self.Core.CreateMissingDirs(os.path.join(self.Core.Config.FrameworkConfigGet("OUTPUT_PATH"), self.Core.Config.FrameworkConfigGet("DB_DIR")))
        self.create_session()

    def Init(self):
        self.Transaction = transaction_manager.TransactionManager(self.Core)
        self.URL = url_manager.URLManager(self.Core)
        self.Plugin = plugin_manager.PluginDB(self.Core)
        self.POutput = poutput_manager.POutputDB(self.Core)
        self.Target = target_manager.TargetDB(self.Core)
        self.Resource = resource_manager.ResourceDB(self.Core)
        self.Config = config_manager.ConfigDB(self.Core)
        self.Error = error_manager.ErrorDB(self.Core)
        self.CommandRegister = command_register.CommandRegister(self.Core)
        self.Mapping = mapping_manager.MappingDB(self.Core)
        self.OWTFSession = session_manager.OWTFSessionDB(self.Core)
        #self.Vulnexp = vulnexp_manager.VulnexpDB(self.Core)
        self.DBHealthCheck()

    def DBHealthCheck(self):
        # TODO: Fix this for psotgres
        return
        self.Target.DBHealthCheck()

    def create_session(self):
        self.Session = self.CreateScopedSession()
        self.session = self.Session()

    def _get_db_settings(self):
        """
        Get database settings, must be used only here
        """
        config_path = os.path.expanduser(self.Core.Config.FrameworkConfigGet(
            'DATABASE_SETTINGS_FILE'))
        config_file = self.Core.open(
            config_path,
            'r')
        settings = {}
        for line in config_file:
            try:
                key = line.split(':')[0]
                if key[0] == '#':  # Ignore comment lines.
                    continue
                value = line.replace(key + ": ", "").strip()
                settings[key] = value
            except ValueError:
                self.Core.Error.FrameworkAbort(
                    "Problem in config file: '" + config_path +
                    "' -> Cannot parse line: " + line)
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
            self.Core.Error.FrameworkAbort(
                "Incomplete database configuration settings in "
                "" + self.Core.Config.FrameworkConfigGet('DATABASE_SETTINGS_FILE'))
        except exc.OperationalError as e:
            self.Core.Error.FrameworkAbort("[DB] " + str(e))

    def CreateScopedSession(self):
        # Not to be used apart from main process, use CreateSession instead
        self.engine = self.CreateEngine(models.Base)
        session_factory = sessionmaker(bind=self.engine)
        return scoped_session(session_factory)
