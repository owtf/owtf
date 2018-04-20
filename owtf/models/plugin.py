"""
owtf.models.plugin
~~~~~~~~~~~~~~~~~~

"""
from sqlalchemy import Column, String, ForeignKey, UniqueConstraint
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from owtf.db.model_base import Model


class Plugin(Model):
    __tablename__ = "plugins"

    key = Column(String, primary_key=True)  # key = type@code
    title = Column(String)
    name = Column(String)
    code = Column(String, ForeignKey("test_groups.code"))
    group = Column(String)
    type = Column(String)
    descrip = Column(String, nullable=True)
    file = Column(String)
    attr = Column(String, nullable=True)
    works = relationship("Work", backref="plugin", cascade="delete")
    outputs = relationship("PluginOutput", backref="plugin")

    def __repr__(self):
        return "<Plugin (code='{!s}', group='{!s}', type='{!s}')>".format(self.code, self.group, self.type)

    @hybrid_property
    def min_time(self):
        """
        Consider last 5 runs only, better performance and accuracy
        """
        poutputs_num = len(self.outputs)
        if poutputs_num != 0:
            if poutputs_num < 5:
                run_times = [poutput.run_time for poutput in self.outputs]
            else:
                run_times = [poutput.run_time for poutput in self.outputs[-5:]]
            return min(run_times)
        else:
            return None

    @hybrid_property
    def max_time(self):
        """
        Consider last 5 runs only, better performance and accuracy
        """
        poutputs_num = len(self.outputs)
        if poutputs_num != 0:
            if poutputs_num < 5:
                run_times = [poutput.run_time for poutput in self.outputs]
            else:
                run_times = [poutput.run_time for poutput in self.outputs[-5:]]
            return max(run_times)
        else:
            return None

    __table_args__ = (UniqueConstraint('type', 'code'),)
