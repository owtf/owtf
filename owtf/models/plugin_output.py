"""
owtf.models.plugin_output
~~~~~~~~~~~~~~~~~~~~~~~~~

"""
import datetime
import json

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.ext.hybrid import hybrid_property

from owtf.db.model_base import Model
from owtf.settings import DATE_TIME_FORMAT
from owtf.utils.timer import timer


class PluginOutput(Model):
    __tablename__ = "plugin_outputs"

    target_id = Column(Integer, ForeignKey("targets.id"))
    plugin_key = Column(String, ForeignKey("plugins.key"))
    # There is a column named plugin which is caused by backref from the plugin class
    id = Column(Integer, primary_key=True)
    plugin_code = Column(String)  # OWTF Code
    plugin_group = Column(String)
    plugin_type = Column(String)
    date_time = Column(DateTime, default=datetime.datetime.now())
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    output = Column(String, nullable=True)
    error = Column(String, nullable=True)
    status = Column(String, nullable=True)
    user_notes = Column(String, nullable=True)
    user_rank = Column(Integer, nullable=True, default=-1)
    owtf_rank = Column(Integer, nullable=True, default=-1)
    output_path = Column(String, nullable=True)

    @hybrid_property
    def run_time(self):
        return self.end_time - self.start_time

    def to_dict(self, inc_output=False):
        pdict = dict(self.__dict__)
        pdict.pop("_sa_instance_state", None)
        pdict.pop("date_time")
        # If output is present, json decode it
        if inc_output:
            if pdict.get("output", None):
                pdict["output"] = json.loads(pdict["output"])
        else:
            pdict.pop("output")
        pdict["start_time"] = self.start_time.strftime(DATE_TIME_FORMAT)
        pdict["end_time"] = self.end_time.strftime(DATE_TIME_FORMAT)
        pdict["run_time"] = timer.get_time_as_str(self.run_time)
        return pdict

    __table_args__ = (UniqueConstraint("plugin_key", "target_id"),)
