"""
owtf.db.config_manager
~~~~~~~~~~~~~~~~~~~~~~

"""
import os
import logging
try:
    import configparser as parser
except ImportError:
    import ConfigParser as parser

from owtf.utils.strings import multi_replace, str2bool
from owtf.lib.exceptions import InvalidConfigurationReference
from owtf.db import models
from owtf.config import config_handler
from owtf.utils.error import abort_framework


def load_config_db_file(file_path):
    """Load Db config from file

    :param file_path: The path to config file
    :type file_path: `str`
    :return: None
    :rtype: None
    """
    file_path = config_handler.discover_config(file_path)
    logging.info("Loading Configuration from: %s.." % file_path)
    config_parser = parser.RawConfigParser()
    config_parser.optionxform = str  # Otherwise all the keys are converted to lowercase xD
    if not os.path.isfile(file_path):  # check if the config file exists
        abort_framework("Config file not found at: %s" % file_path)
    config_parser.read(file_path)
    for section in config_parser.sections():
        for key, value in config_parser.items(section):
            old_config_obj = db.session.query(models.ConfigSetting).get(key)
            if not old_config_obj or not old_config_obj.dirty:
                if not key.endswith("_DESCRIP"):  # _DESCRIP are help values
                    config_obj = models.ConfigSetting(key=key, value=value, section=section)
                    # If _DESCRIP at the end, then use it as help text
                    if config_parser.has_option(section, "%s_DESCRIP" % key):
                        config_obj.descrip = config_parser.get(section, "%s_DESCRIP" % key)
                    db.session.merge(config_obj)
    db.session.commit()


def get_config_val(self, key):
    """Get the value of the key from DB

    :param key: Key to lookup
    :type key: `str`
    :return: Value
    :rtype: `str`
    """
    obj = self.db.session.query(models.ConfigSetting).get(key)
    if obj:
        return multi_replace(obj.value, get_replacement_dict())
    else:
        return None


def derive_config_dict(config_obj):
    """Get the config dict from the obj

    :param config_obj: The config object
    :type config_obj:
    :return:
    :rtype:
    """
    if config_obj:
        config_dict = dict(config_obj.__dict__)
        config_dict.pop("_sa_instance_state")
        return config_dict
    else:
        return config_obj


def derive_config_dicts(config_obj_list):
    """Derive multiple config dicts

    :param config_obj_list: List of all config objects
    :type config_obj_list: `list`
    :return: List of config dicts
    :rtype: `list`
    """
    config_dict_list = []
    for config_obj in config_obj_list:
        if config_obj:
            config_dict_list.append(derive_config_dict(config_obj))
    return config_dict_list


def config_gen_query(criteria):
    """Generate query

    :param criteria: Filter criteria
    :type criteria: `dict`
    :return:
    :rtype:
    """
    query = db.session.query(models.ConfigSetting)
    if criteria.get("key", None):
        if isinstance(criteria["key"], str):
            query = query.filter_by(key=criteria["key"])
        if isinstance(criteria["key"], list):
            query = query.filter(models.ConfigSetting.key.in_(criteria["key"]))
    if criteria.get("section", None):
        if isinstance(criteria["section"], str):
            query = query.filter_by(section=criteria["section"])
        if isinstance(criteria["section"], list):
            query = query.filter(models.ConfigSetting.section.in_(criteria["section"]))
    if criteria.get('dirty', None):
        if isinstance(criteria.get('dirty'), list):
            criteria['dirty'] = criteria['dirty'][0]
        query = query.filter_by(dirty=str2bool(criteria['dirty']))
    return query.order_by(models.ConfigSetting.key)


def get_all_config_dicts(criteria=None):
    """Get all config dicts for a criteria

    :param criteria: Filter criteria
    :type criteria: `str`
    :return: Config dict
    :rtype: `dict`
    """
    if not criteria:
        criteria = {}
    query = config_gen_query(criteria)
    return derive_config_dicts(query.all())


def get_all_tools():
    """Get all tools from the config DB

    :return: Config dict for all tools
    :rtype: `dict`
    """
    results = db.session.query(models.ConfigSetting).filter(models.ConfigSetting.key.like("%TOOL_%")).all()
    config_dicts = derive_config_dicts(results)
    for config_dict in config_dicts:
        config_dict["value"] = multi_replace(config_dict["value"], get_replacement_dict())
    return config_dicts


def get_sections_config():
    """Get all sections in from the config db

    :return: List of sections
    :rtype: `list`
    """
    sections = db.session.query(models.ConfigSetting.section).distinct().all()
    sections = [i[0] for i in sections]
    return sections


def update_config_val(key, value):
    """Update the configuration value for a key

    :param key: Key whose value to update
    :type key: `str`
    :param value: New value
    :type value: `str`
    :return: None
    :rtype: None
    """
    config_obj = db.session.query(models.ConfigSetting).get(key)
    if config_obj:
        config_obj.value = value
        config_obj.dirty = True
        db.session.merge(config_obj)
        db.session.commit()
    else:
        raise InvalidConfigurationReference("No setting exists with key: %s" % str(key))


def get_replacement_dict(self):
    """Get the config dict

    :return: Replaced dict
    :rtype: `dict`
    """
    config_dict = {}
    config_list = db.session.query(models.ConfigSetting.key, models.ConfigSetting.value).all()
    for key, value in config_list:  # Need a dict
        config_dict[key] = value
    return config_dict


def get_tcp_ports(start_port, end_port):
    """Get TCP ports from the config file

    :param start_port: Start port in a range
    :type start_port: `str`
    :param end_port: End port
    :type end_port: `str`
    :return: Comma-separate string of tcp ports
    :rtype: `str`
    """
    return ','.join(config_handler.get("TCP_PORTS").split(',')[int(start_port):int(end_port)])


def get_udp_ports(start_port, end_port):
    """Get UDP ports from the config file

    :param start_ort: Start port in a range
    :type start_port: `str`
    :param end_port: End port
    :type end_port: `str`
    :return: Comma-separate string of udp ports
    :rtype: `str`
    """
    return ','.join(config_handler.get("UDP_PORTS").split(',')[int(start_port):int(end_port)])
