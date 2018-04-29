"""
owtf.models.mapping
~~~~~~~~~~~~~~~~~~~

"""
from sqlalchemy import Column, String

from owtf.db.model_base import Model


class Mapping(Model):
    __tablename__ = "mappings"

    owtf_code = Column(String, primary_key=True)
    mappings = Column(String)
    category = Column(String, nullable=True)
