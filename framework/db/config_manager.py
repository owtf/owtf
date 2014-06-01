from framework.db import models
from framework.lib.general import cprint
from framework.lib import general
import ConfigParser


class ConfigDB(object):
    def __init__(self, Core):
        self.Core = Core
        self.ConfigDBSession = self.Core.DB.CreateScopedSession(self.Core.Config.FrameworkConfigGetDBPath("CONFIG_DB_PATH"), models.GeneralBase)
        self.LoadConfigDBFromFile(self.Core.Config.FrameworkConfigGet('DEFAULT_GENERAL_PROFILE'))

    def IsConvertable(self, value, conv):
        try:
            return(conv(value))
        except ValueError:
            return None

    def LoadConfigDBFromFile(self, file_path):
        # TODO: Implementy user override mechanism
        cprint("Loading Configuration from: " + file_path + " ..")
        config_parser = ConfigParser.RawConfigParser()
        config_parser.optionxform = str  # Otherwise all the keys are converted to lowercase xD
        config_parser.read(file_path)
        session = self.ConfigDBSession()
        for section in config_parser.sections():
            for key, value in config_parser.items(section):
                old_config_obj = session.query(models.ConfigSetting).get(key)
                if not old_config_obj or not old_config_obj.dirty:
                    if not key.endswith("_DESCRIP"):  # _DESCRIP are help values
                        config_obj = models.ConfigSetting(key=key, value=value, section=section)
                        # If _DESCRIP at the end, then use it as help text
                        if config_parser.has_option(section, key + "_DESCRIP"):
                            config_obj.descrip = config_parser.get(section, key + "_DESCRIP")
                        session.merge(config_obj)
        session.commit()
        session.close()

    def Get(self, Key):
        session = self.ConfigDBSession()
        obj = session.query(models.ConfigSetting).get(Key)
        session.close()
        if obj:
            return(self.Core.Config.MultipleReplace(obj.value, self.Core.Config.GetReplacementDict()))
        else:
            return(None)

    def DeriveConfigDict(self, config_obj):
        if config_obj:
            config_dict = dict(config_obj.__dict__)
            config_dict.pop("_sa_instance_state")
            return config_dict
        else:
            return config_obj

    def DeriveConfigDicts(self, config_obj_list):
        config_dict_list = []
        for config_obj in config_obj_list:
            if config_obj:
                config_dict_list.append(self.DeriveConfigDict(config_obj))
        return config_dict_list

    def GenerateQueryUsingSession(self, session, criteria):
        query = session.query(models.ConfigSetting)
        if criteria.get("key", None):
            if isinstance(criteria["key"], (str, unicode)):
                query = query.filter_by(key=criteria["key"])
            if isinstance(criteria["key"], list):
                query = query.filter(models.ConfigSetting.key.in_(criteria["key"]))
        if criteria.get("section", None):
            if isinstance(criteria["section"], (str, unicode)):
                query = query.filter_by(section=criteria["section"])
            if isinstance(criteria["section"], list):
                query = query.filter(models.ConfigSetting.section.in_(criteria["section"]))
        if criteria.get('dirty', None):
            if isinstance(criteria.get('dirty'), list):
                criteria['dirty'] = criteria['dirty'][0]
            query = query.filter_by(dirty=self.Core.Config.ConvertStrToBool(criteria['dirty']))
        return query

    def GetAll(self, criteria=None):
        if not criteria:
            criteria = {}
        session = self.ConfigDBSession()
        query = self.GenerateQueryUsingSession(session, criteria)
        return self.DeriveConfigDicts(query.all())

    def GetSections(self):
        session = self.ConfigDBSession()
        sections = session.query(models.ConfigSetting.section).distinct().all()
        session.close()
        sections = [i[0] for i in sections]
        return sections

    def Update(self, key, value):
        session = self.ConfigDBSession()
        config_obj = session.query(models.ConfigSetting).get(key)
        if config_obj:
            config_obj.value = value
            config_obj.dirty = True
            session.merge(config_obj)
            session.commit()
            session.close()
        else:
            session.close()
            raise general.InvalidConfigurationReference("No setting exists with key: " + str(key))

    def GetReplacementDict(self):
        config_dict = {}
        session = self.ConfigDBSession()
        config_list = session.query(models.ConfigSetting.key, models.ConfigSetting.value).all()
        session.close()
        for key, value in config_list:  # Need a dict
            config_dict[key] = value
        return config_dict

    def GetTcpPorts(self, startport, endport):
        return ','.join(self.Get("TCP_PORTS").split(',')[int(startport):int(endport)])

    def GetUdpPorts(self, startport, endport):
        return ','.join(self.Get("UDP_PORTS").split(',')[int(startport):int(endport)])
