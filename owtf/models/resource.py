"""
owtf.models.resource
~~~~~~~~~~~~~~~~~~~~

"""
from sqlalchemy import Boolean, Column, Integer, String, UniqueConstraint

from owtf.db.model_base import Model


class Resource(Model):
    __tablename__ = "resources"

    id = Column(Integer, primary_key=True)
    dirty = Column(Boolean, default=False)  # Dirty if user edited it. Useful while updating
    resource_name = Column(String)
    resource_type = Column(String)
    resource = Column(String)

    __table_args__ = (UniqueConstraint("resource", "resource_type", "resource_name"),)
