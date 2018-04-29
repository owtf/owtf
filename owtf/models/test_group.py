"""
owtf.models.test_group
~~~~~~~~~~~~~~~~~~~~~~

"""
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from owtf.db.model_base import Model


class TestGroup(Model):
    __tablename__ = "test_groups"

    code = Column(String, primary_key=True)
    group = Column(String)  # web, network
    descrip = Column(String)
    hint = Column(String, nullable=True)
    url = Column(String)
    priority = Column(Integer)
    plugins = relationship("Plugin")
