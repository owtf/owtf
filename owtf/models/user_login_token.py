"""
owtf.models.user_login_token
~~~~~~~~~~~~~~~~

"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, UniqueConstraint
from owtf.db.model_base import Model
import uuid
from datetime import datetime, timedelta
from owtf.settings import JWT_EXP_DELTA_SECONDS
from owtf.models.user import User


class UserLoginToken(Model):
    __tablename__ = "user_login_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey(User.id))
    token = Column(String, nullable=False)

    @classmethod
    def find_by_userid_and_token(cls, session, user_id, token):
        """Find a api_token by user_id and token
        Returns None if not found.
        """
        return session.query(UserLoginToken).filter_by(user_id=user_id, token=token).first()

    @classmethod
    def add_user_login_token(cls, session, token, user_id):
        """Adds an user_login_token to the DB"""
        new_token = cls(user_id=user_id, token=token.decode("ascii"))
        session.add(new_token)
        session.commit()

    @classmethod
    def delete_user_login_token(cls, session, token):
        """Delete the user_login_token from the DB"""
        token_obj = session.query(cls).filter_by(token=token).first()
        if token_obj is not None:
            session.delete(token_obj)
            session.commit()
