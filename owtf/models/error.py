"""
owtf.models.error
~~~~~~~~~~~~~~~~~

"""
from sqlalchemy import Boolean, Column, Integer, String

from owtf.db.model_base import Model


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
