"""
owtf.models.session
~~~~~~~~~~~~~~~~~~~

"""
from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship

from owtf.db.model_base import Model
from owtf.models.target import target_association_table


class Session(Model):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True)
    active = Column(Boolean, default=False)
    targets = relationship("Target", secondary=target_association_table, backref="sessions")
