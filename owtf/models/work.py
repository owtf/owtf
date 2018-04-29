"""
owtf.models.work
~~~~~~~~~~~~~~~~

"""
from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, UniqueConstraint

from owtf.db.model_base import Model


class Work(Model):
    __tablename__ = "worklist"

    id = Column(Integer, primary_key=True, autoincrement=True)
    target_id = Column(Integer, ForeignKey("targets.id"))
    plugin_key = Column(String, ForeignKey("plugins.key"))
    active = Column(Boolean, default=True)
    # Columns plugin and target are created using backrefs

    __table_args__ = (UniqueConstraint("target_id", "plugin_key"),)

    def __repr__(self):
        return "<Work (target='{!s}', plugin='{!s}')>".format(self.target_id, self.plugin_key)
