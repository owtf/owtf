"""
owtf.models.user
~~~~~~~~~~~~~~~~

"""
from sqlalchemy import Column, Integer, Unicode

from owtf.db.model_base import Model


class User(Model):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Unicode(255), unique=True)
    cookie_id = Column(Unicode(255), default=None, nullable=False, unique=True)

    @classmethod
    def find(cls, db, name):
        """Find a user by name.
        Returns None if not found.
        """
        return db.query(cls).filter(cls.name == name).first()
