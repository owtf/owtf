"""
owtf.models.api_token
~~~~~~~~~~~~~~~~

"""
from sqlalchemy import Column, Integer, Unicode, ForeignKey
from owtf.db.model_base import Model
import uuid


class ApiToken(Model):
    __tablename__ = "api_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    key = Column(Unicode(255), nullable=False)

    @classmethod
    def find_by_userid(cls, session, user_id):
        """Find a api_token by user_id.
        Returns None if not found.
        """
        return session.query(ApiToken).filter_by(user_id=user_id).all()

    @classmethod
    def add_api_token(cls, session, key, user_id):
        """Adds an api_token to the DB"""
        new_token = cls(user_id=user_id, key=key)
        session.add(new_token)
        session.commit()
