from framework.dependency_management.dependency_resolver import BaseComponent
from framework.dependency_management.interfaces import DBConfigInterface
from framework.lib.exceptions import InvalidConfigurationReference
from framework.db import models
from framework.lib.general import cprint
import ConfigParser
import logging
import os


class ConfigDB(BaseComponent, DBConfigInterface):

    COMPONENT_NAME = "db_config"

    def __init__(self):
        self.register_in_service_locator()
        self.config = self.get_component("config")
        self.db = self.get_component("db")
        self.error_handler = self.get_component("error_handler")

    def init(self):
        self.LoadConfigDBFromFile(self.config.get_profile_path('GENERAL_PROFILE'))

    def IsConvertable(self, value, conv):
        try:
            return(conv(value))
        except ValueError:
            return None

    def LoadConfigDBFromFile(self, file_path):
        # TODO: Implementy user override mechanism
        logging.info("Loading Configuration from: " + file_path + " ..")
        config_parser = ConfigParser.RawConfigParser()
        config_parser.optionxform = str  # Otherwise all the keys are converted to lowercase xD
        if not os.path.isfile(file_path):  # check if the config file exists
            self.error_handler.FrameworkAbort("Config file not found at: %s" % file_path)
        config_parser.read(file_path)
        for section in config_parser.sections():
            for key, value in config_parser.items(section):
                old_config_obj = self.db.session.query(models.ConfigSetting).get(key)
                if not old_config_obj or not old_config_obj.dirty:
                    if not key.endswith("_DESCRIP"):  # _DESCRIP are help values
                        config_obj = models.ConfigSetting(key=key, value=value, section=section)
                        # If _DESCRIP at the end, then use it as help text
                        if config_parser.has_option(section, key + "_DESCRIP"):
                            config_obj.descrip = config_parser.get(section, key + "_DESCRIP")
                        self.db.session.merge(config_obj)
        self.db.session.commit()

    def Get(self, Key):
        obj = self.db.session.query(models.ConfigSetting).get(Key)
        if obj:
            return(self.config.MultipleReplace(obj.value, self.config.GetReplacementDict()))
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

    def GenerateQueryUsingSession(self, criteria):
        query = self.db.session.query(models.ConfigSetting)
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
            query = query.filter_by(dirty=self.config.ConvertStrToBool(criteria['dirty']))
        return query.order_by(models.ConfigSetting.key)

    def GetAll(self, criteria=None):
        if not criteria:
            criteria = {}
        query = self.GenerateQueryUsingSession(criteria)
        return self.DeriveConfigDicts(query.all())

    def GetAllTools(self):
        results = self.db.session.query(models.ConfigSetting).filter(
            models.ConfigSetting.key.like("%TOOL_%")).all()
        config_dicts = self.DeriveConfigDicts(results)
        for config_dict in config_dicts:
            config_dict["value"] = self.config.MultipleReplace(
                config_dict["value"], self.config.GetReplacementDict())
        return(config_dicts)

    def GetSections(self):
        sections = self.db.session.query(models.ConfigSetting.section).distinct().all()
        sections = [i[0] for i in sections]
        return sections

    def Update(self, key, value):
        config_obj = self.db.session.query(models.ConfigSetting).get(key)
        if config_obj:
            config_obj.value = value
            config_obj.dirty = True
            self.db.session.merge(config_obj)
            self.db.session.commit()
        else:
            raise InvalidConfigurationReference("No setting exists with key: " + str(key))

    def GetReplacementDict(self):
        config_dict = {}
        config_list = self.db.session.query(models.ConfigSetting.key, models.ConfigSetting.value).all()
        for key, value in config_list:  # Need a dict
            config_dict[key] = value
        return config_dict

    def GetTcpPorts(self, startport, endport):
        return ','.join(self.Get("TCP_PORTS").split(',')[int(startport):int(endport)])

    def GetUdpPorts(self, startport, endport):
        return ','.join(self.Get("UDP_PORTS").split(',')[int(startport):int(endport)])
