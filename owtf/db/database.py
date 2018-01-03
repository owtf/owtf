"""
owtf.db.db
~~~~~~~~~~

This file handles all the database transactions.
"""

import logging
from contextlib import contextmanager
from multiprocessing.util import register_after_fork

from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import create_engine, exc
from sqlalchemy.pool import QueuePool
from sqlalchemy.orm import Session as BaseSession

from owtf import config
from owtf.db import models
from owtf.settings import DATABASE_IP, DATABASE_PORT, DATABASE_NAME, DATABASE_USER, DATABASE_PASS
from owtf.utils.error import abort_framework


class Session(BaseSession):
    def __init__(self, *a, **kw):
        super(Session, self).__init__(*a, **kw)
        self._in_atomic = False

    @contextmanager
    def atomic(self):
        """Transaction context manager.

        .note::
            Will commit the transaction on successful completion of the block, or roll it back on error.
            Supports nested usage (via save points).

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


class SQLAlchemy(object):

    def __init__(self):
        self.create_session()

    def create_session(self):
        """Create a DB session

        :return: None
        :rtype: None
        """
        self._session = self.create_scoped_session()
        self.session = self._session()

    def create_engine(self, base):
        """Create the SQLAlchemy engine with parameters

        :return: None
        :rtype: None
        """
        try:
            engine = create_engine(
                "postgresql+psycopg2://%s:%s@%s:%s/%s".format(DATABASE_USER, DATABASE_PASS, DATABASE_IP, DATABASE_PORT,
                DATABASE_NAME, poolclass=QueuePool, pool_size=5, max_overflow=10))
            base.metadata.create_all(engine)
            # Fix for forking
            register_after_fork(engine, engine.dispose)
            return engine
        except ValueError as e:  # Potentially corrupted DB config.
            logging.error("Potentially corrupt DB, exiting...")
        except KeyError:  # Indicates incomplete db config file
            abort_framework("Incomplete database configuration settings")
        except exc.OperationalError as e:
            abort_framework("[DB] %s\nRun 'make db-run' to start/setup db".format(str(e)))

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
