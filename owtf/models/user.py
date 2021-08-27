"""
owtf.models.user
~~~~~~~~~~~~~~~~

"""
from sqlalchemy import Column, Integer, Unicode, Boolean
from owtf.db.model_base import Model
from owtf.models.email_confirmation import EmailConfirmation
from sqlalchemy.orm import relationship
import uuid


class User(Model):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Unicode(255), nullable=False, unique=True)
    email = Column(Unicode(255), nullable=False, unique=True)
    password = Column(Unicode(255), nullable=False)
    is_active = Column(Boolean, default=False)  # checks whether user email is verified
    otp_secret_key = Column(Unicode(255), nullable=False, unique=True)  # used to generate unique otp
    email_confirmations = relationship(EmailConfirmation, cascade="delete")
    user_login_tokens = relationship("UserLoginToken", cascade="delete")

    @classmethod
    def find(cls, session, name):
        """Find a user by name.
        Returns None if not found.
        """
        return session.query(cls).filter_by(name=name).all()

    @classmethod
    def find_by_email(cls, session, email):
        """Find a user by email(email is unique).
        Returns None if not found.
        """
        return session.query(cls).filter_by(email=email).first()

    @classmethod
    def find_by_name(cls, session, name):
        """Find a user by username(username is unique).
        Returns None if not found.
        """
        return session.query(cls).filter_by(name=name).first()

    @classmethod
    def add_user(cls, session, user):
        """Adds an user to the DB"""
        new_user = cls(
            name=user["name"],
            email=user["email"],
            password=user["password"].decode("utf-8"),
            otp_secret_key=user["otp_secret_key"],
        )
        session.add(new_user)
        session.commit()

    @classmethod
    def activate_user(cls, session, user_id):
        db_obj = session.query(cls).filter_by(id=user_id).first()
        db_obj.is_active = True
        session.commit()

    @classmethod
    def find_by_id(cls, session, id):
        """Find a user by id.
        Returns None if not found.
        """
        return session.query(cls).filter_by(id=id).first()

    @classmethod
    def change_password(cls, session, email, password):
        db_obj = session.query(cls).filter_by(email=email).first()
        db_obj.password = password
        session.commit()
