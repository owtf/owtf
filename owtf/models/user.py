"""
owtf.models.user
~~~~~~~~~~~~~~~~

"""
from sqlalchemy import Column, Integer, Unicode
from owtf.db.model_base import Model
import uuid


class User(Model):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Unicode(255))
    email = Column(Unicode(255), nullable=False, unique=True)
    password = Column(Unicode(255), nullable=False)

    @classmethod
    def find(cls, session, name):
        """Find a user by name.
        Returns None if not found.
        """
        return session.query(cls).filter_by(name=name).all()

    @classmethod
    def find_by_email(cls, session, email):
        """Find a user by email.
        Returns None if not found.
        """
        return session.query(cls).filter_by(email=email).all()

    @classmethod
    def add_user(cls, session, user):
        """Adds an user to the DB"""
        new_user = cls(
            name=user["name"],
            email=user["email"],
            password=user["password"].decode("utf-8"),
        )
        session.add(new_user)
        session.commit()
