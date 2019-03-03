"""
owtf.models.plugin
~~~~~~~~~~~~~~~~~~

"""
from sqlalchemy import Column, String, ForeignKey, UniqueConstraint, or_
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from owtf.db.model_base import Model
from owtf.utils.timer import timer


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

    def to_dict(self):
        pdict = dict(self.__dict__)
        pdict.pop("_sa_instance_state")
        # Remove outputs array if present
        if "outputs" in list(pdict.keys()):
            pdict.pop("outputs")
        pdict["min_time"] = None
        min_time = self.min_time
        if min_time is not None:
            pdict["min_time"] = timer.get_time_as_str(min_time)
        return pdict

    @classmethod
    def get_all_plugin_groups(cls, session):
        groups = session.query(Plugin.group).distinct().all()
        groups = [i[0] for i in groups]
        return groups

    @classmethod
    def get_all_plugin_types(cls, session):
        """Get all plugin types from the DB

        :return: All available plugin types
        :rtype: `list`
        """
        plugin_types = session.query(Plugin.type).distinct().all()
        plugin_types = [i[0] for i in plugin_types]  # Necessary because of sqlalchemy
        return plugin_types

    @classmethod
    def get_groups_for_plugins(cls, session, plugins):
        """Gets available groups for selected plugins

        :param plugins: Plugins selected
        :type plugins: `list`
        :return: List of available plugin groups
        :rtype: `list`
        """
        groups = (
            session.query(Plugin.group).filter(or_(Plugin.code.in_(plugins), Plugin.name.in_(plugins))).distinct().all()
        )
        groups = [i[0] for i in groups]
        return groups

    @classmethod
    def name_to_code(cls, session, codes):
        """Given list of names, get the corresponding codes

        :param codes: The codes to fetch
        :type codes: `list`
        :return: Corresponding plugin codes as a list
        :rtype: `list`
        """
        checklist = ["OWTF-", "PTES-"]
        query = session.query(Plugin.code)
        for count, name in enumerate(codes):
            if all(check not in name for check in checklist):
                code = query.filter(Plugin.name == name).first()
                codes[count] = str(code[0])
        return codes

    __table_args__ = (UniqueConstraint("type", "code"),)
