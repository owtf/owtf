"""
owtf.db.db
~~~~~~~~~~

This file handles all the database transactions.
"""

import os
from contextlib import contextmanager
from multiprocessing.util import register_after_fork

from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import create_engine, exc
from sqlalchemy.pool import QueuePool
from sqlalchemy.orm import Session as BaseSession

from owtf.utils import FileOperations
from owtf.dependency_management.dependency_resolver import BaseComponent
from owtf.dependency_management.interfaces import DBInterface
from owtf.db import models


class Session(BaseSession):
    def __init__(self, *a, **kw):
        super(Session, self).__init__(*a, **kw)
        self._in_atomic = False

    @contextmanager
    def atomic(self):
        """Transaction context manager.

        .note::
            Will commit the transaction on successful completion of the block, or roll it back on error.
            Supports nested usage (via savepoints).

        :return: None
        :rtype: None
        """
        nested = self._in_atomic
        self.begin(nested=nested)
        self._in_atomic = True
        try:
            yield
        except:
            self.rollback()
            raise
        else:
            self.commit()
        finally:
            if not nested:
                self._in_atomic = False


class DB(BaseComponent, DBInterface):

    COMPONENT_NAME = "db"

    def __init__(self):
        self.register_in_service_locator()
        self.config = self.get_component("config")
        self.error_handler = self.get_component("error_handler")
        self.error_db_session = None
        self.transaction = None
        self.url = None
        self.plugin = None
        self.poutput = None
        self.target = None
        self.resource = None
        self.error = None
        self.command_register = None
        self.mapping = None
        self._db_settings = self._get_db_settings()
        self.create_session()

    def init(self):
        self.config = self.get_component("config")
        self.transaction = self.get_component("transaction")
        self.url = self.get_component("url_manager")
        self.plugin = self.get_component("db_plugin")
        self.poutput = self.get_component("plugin_output")
        self.target = self.get_component("target")
        self.resource = self.get_component("resource")
        self.config = self.get_component("db_config")
        self.error = self.get_component("db_error")
        self.command_register = self.get_component("command_register")
        self.mapping = self.get_component("mapping_db")
        self.error_handler = self.get_component("error_handler")
        self.owtf_session = self.get_component("session_db")
        self.worklist = self.get_component("worklist_manager")

    def get_category(self, plugin_code):
        """Get the mapping for a plugin code

        :param plugin_code: Plugin code
        :type plugin_code: `str`
        :return:
        :rtype:
        """
        return self.mapping.get_category(plugin_code)

    def create_session(self):
        """Create a DB session

        :return: None
        :rtype: None
        """
        self._session = self.create_scoped_session()
        self.session = self._session()

    def clean_up(self):
        """Close the sqlalchemy session opened by DB

        :return: None
        :rtype: None
        """
        self.session.close()

    def _get_db_settings(self):
        """Create DB settings according to the configuration file.

        :return: Settings dict
        :rtype: `dict`
        """
        config_path = os.path.expanduser(self.config.get_val('DATABASE_SETTINGS_FILE'))
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
                    self.error_handler.abort_framework("Problem in config file: '%s' -> Cannot parse line: %s" %
                                                       (config_path, line))
        return settings

    def create_engine(self, base):
        """Create the SQLAlchemy engine with parameters

        :return: None
        :rtype: None
        """
        try:
            engine = create_engine(
                "postgresql+psycopg2://%s:%s@%s:%s/%s" % (
                    self._db_settings['DATABASE_USER'],
                    self._db_settings['DATABASE_PASS'],
                    self._db_settings['DATABASE_IP'],
                    self._db_settings['DATABASE_PORT'],
                    self._db_settings['DATABASE_NAME']),
                poolclass=QueuePool,
                pool_size=5,
                max_overflow=10)
            base.metadata.create_all(engine)
            # Fix for forking
            register_after_fork(engine, engine.dispose)
            return engine
        except ValueError as e:  # Potentially corrupted DB config.
            self.error_handler.abort_framework(
                "Database configuration file is potentially corrupted. Please check %s\n[DB] %s" %
                (self.config.get_val('DATABASE_SETTINGS_FILE'), str(e)))
        except KeyError:  # Indicates incomplete db config file
            self.error_handler.abort_framework("Incomplete database configuration settings in %s" %
                                               self.config.get_val('DATABASE_SETTINGS_FILE'))
        except exc.OperationalError as e:
            self.error_handler.abort_framework("[DB] %s\nRun 'make db-run' to start/setup db" % str(e))

    def create_scoped_session(self):
        """Scoped session for the main OWTF process

        .note::
            Not to be used apart from main process, use CreateSession instead

        :return:
        :rtype:
        """
        self.engine = self.create_engine(models.Base)
        session_factory = sessionmaker(bind=self.engine, class_=Session)
        return scoped_session(session_factory)
