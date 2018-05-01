"""
owtf.models.error
~~~~~~~~~~~~~~~~~

"""
from owtf.lib.exceptions import InvalidErrorReference
from sqlalchemy import Boolean, Column, Integer, String

from owtf.db.model_base import Model
from owtf.db.session import flush_transaction


class Error(Model):
    __tablename__ = "errors"

    id = Column(Integer, primary_key=True)
    owtf_message = Column(String)
    traceback = Column(String, nullable=True)
    user_message = Column(String, nullable=True)
    reported = Column(Boolean, default=False)
    github_issue_url = Column(String, nullable=True)

    def __repr__(self):
        return "<Error (traceback='{!s}')>".format(self.traceback)

    @classmethod
    def add_error(cls, session, message, trace):
        obj = Error(owtf_message=message, traceback=trace)
        session.add(obj)
        session.commit()
        return obj

    @classmethod
    def get_error(cls, session, error_id):
        error = session.query(Error).get(error_id)
        if not error:  # If invalid error id, bail out
            raise InvalidErrorReference("No error with id {!s}".format(error_id))
        return error.to_dict()

    @classmethod
    def delete_error(cls, session, id):
        error = session.query(cls).get(id)
        if error:
            session.delete(error)
            session.commit()
        else:
            raise InvalidErrorReference("No error with id {!s}".format(id))

    def to_dict(self):
        obj = dict(self.__dict__)
        obj.pop("_sa_instance_state", None)
        return obj

    @classmethod
    def get_all_dict(cls, session):
        errors = session.query(Error).all()
        result = []
        for err in errors:
            result.append(err.to_dict())
        return result

    @classmethod
    def update_error(cls, session, error_id, user_message):
        obj = session.query(Error).filter(id=error_id)
        if not obj:  # If invalid error id, bail out
            raise InvalidErrorReference("No error with id {!s}".format(error_id))
        obj.user_message = user_message
        session.merge(obj)
        session.commit()
