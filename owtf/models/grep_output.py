"""
owtf.models.grep_output
~~~~~~~~~~~~~~~~~~~~~~~

"""
from sqlalchemy import Column, Integer, String, ForeignKey, Text, UniqueConstraint

from owtf.db.model_base import Model


class GrepOutput(Model):
    __tablename__ = "grep_outputs"

    target_id = Column(Integer, ForeignKey("targets.id"))
    id = Column(Integer, primary_key=True)
    name = Column(String)
    output = Column(Text)
    # Also has a column transactions, which is added by
    # using backref in transaction

    __table_args__ = (UniqueConstraint("name", "output", target_id),)
