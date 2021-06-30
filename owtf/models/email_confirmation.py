"""
owtf.models.email_confirmation
~~~~~~~~~~~~~~~~~~~~~~

"""
from sqlalchemy import Column, Integer, Unicode, ForeignKey, DateTime
from owtf.db.model_base import Model


class EmailConfirmation(Model):
    __tablename__ = "email_confirmation"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key_value = Column(Unicode(255), nullable=True)
    expiration_time = Column(DateTime)
    user_id = Column(Integer, ForeignKey("users.id"))

    @classmethod
    def get_by_userid(cls, session, user_id):
        return session.query(cls).filter_by(user_id=user_id).all()

    @classmethod
    def add_confirm_password(cls, session, cf):
        """Adds an user to the DB"""
        new_cf = cls(
            key_value=cf["key_value"],
            expiration_time=cf["expiration_time"],
            user_id=cf["user_id"],
        )
        session.add(new_cf)
        session.commit()

    @classmethod
    def find_by_key_value(cls, session, key_value):
        return session.query(cls).filter_by(key_value=key_value).first()

    @classmethod
    def remove_previous_all(cls, session, user_id):
        email_confirmation_objects = session.query(cls).filter_by(user_id=user_id).all()
        if email_confirmation_objects is not None:
            for email_confirmation_obj in email_confirmation_objects:
                session.delete(email_confirmation_obj)
                session.commit()
