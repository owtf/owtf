"""
owtf.db.session
~~~~~~~~~~~~~~~

This file handles all the database transactions.
"""
import functools
import sys
import logging

from sqlalchemy import create_engine, exc, func
from sqlalchemy.orm import Session, sessionmaker

from owtf.db.model_base import Model
from owtf.settings import (
    DATABASE_IP,
    DATABASE_NAME,
    DATABASE_PASS,
    DATABASE_USER,
    DATABASE_PORT,
)

DB_URI = "postgresql+psycopg2://{}:{}@{}:{}/{}".format(
    DATABASE_USER, DATABASE_PASS, DATABASE_IP, DATABASE_PORT, DATABASE_NAME
)


def get_count(q):
    count_q = q.statement.with_only_columns([func.count()]).order_by(None)
    count = q.session.execute(count_q).scalar()
    return count


def flush_transaction(method):

    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        dry_run = kwargs.pop("dryrun", False)
        try:
            ret = method(self, *args, **kwargs)
            if dry_run:
                self.session.rollback()
            else:
                self.session.flush()
        except Exception:
            logging.exception("Transaction Failed. Rolling back.")
            if self.session is not None:
                self.session.rollback()
            raise
        return ret

    return wrapper


def get_db_engine():
    try:
        engine = create_engine(DB_URI)
        Model.metadata.create_all(engine)
        return engine
    except exc.OperationalError as e:
        logging.error("Could not create engine - Exception occured\n%s", str(e))
        sys.exit(1)


def get_scoped_session():
    _session = sessionmaker()
    _session.configure(bind=get_db_engine())
    return _session()
