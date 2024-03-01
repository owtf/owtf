"""
owtf.managers.config_manager
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Manage configuration methods.
"""
import logging
import os
import yaml

from owtf.config import config_handler
from owtf.lib.exceptions import InvalidConfigurationReference
from owtf.models.config import Config
from owtf.utils.error import abort_framework
from owtf.utils.file import FileOperations
from owtf.utils.strings import multi_replace, str2bool
from owtf.utils.pycompat import iteritems


def load_config_file(file_path, fallback_file_path):
    """Load YAML format configuration file

    :param file_path: The path to config file
    :type file_path: `str`
    :param fallback_file_path: The fallback path to config file
    :type fallback_file_path: `str`
    :return: config_map
    :rtype: dict
    """
    file_path = file_path if os.path.isfile(file_path) else fallback_file_path
    logging.info("Loading %s..", file_path)
    if not os.path.isfile(file_path):
        # check if the config file exists
        abort_framework("Config file not found at: {}".format(file_path))
    try:
        config_map = yaml.safe_load(FileOperations.open(file_path, "r"))
        return config_map
    except yaml.YAMLError:
        abort_framework("Error parsing config file at: {}".format(file_path))


def load_general_config(session, default, fallback):
    """Load Db config from file

    :param session: SQLAlchemy database session
    :type session: `object`
    :param default: The fallback path to config file
    :type default: `str`
    :param fallback: The path to config file
    :type fallback: `str`
    :return: None
    :rtype: None
    """
    config_dump = load_config_file(default, fallback)
    for section, config_list in iteritems(config_dump):
        for config_map in config_list:
            try:
                old_config_obj = session.query(Config).get(config_map["config"])
                if not old_config_obj or not old_config_obj.dirty:
                    config_obj = Config(
                        key=config_map["config"],
                        value=str(config_map["value"]),
                        section=section,
                    )
                    config_obj.descrip = config_map.get("description", "")
                    session.merge(config_obj)
            except KeyError:
                logging.debug("Got a key error while parsing general config")
    session.commit()


def load_framework_config(default, fallback, root_dir, owtf_pid):
    """Load framework configuration into a global dictionary.

    :param default: The path to config file
    :type default: str
    :param fallback: The fallback path to config file
    :type fallback: str
    :param fallback: OWTF root directory
    :type fallback: str
    :param fallback: PID of running program
    :type fallback: int
    :return: None
    :rtype: None
    """
    config_dump = load_config_file(default, fallback)
    config_handler.set_val("FRAMEWORK_DIR", root_dir)  # Needed Later.
    for section, config_list in iteritems(config_dump):
        for config_map in config_list:
            try:
                config_handler.set_val(
                    config_map["config"],
                    multi_replace(
                        str(config_map["value"]),
                        {"FRAMEWORK_DIR": root_dir, "OWTF_PID": str(owtf_pid)},
                    ),
                )
            except KeyError as e:
                logging.debug("Exception while parsing framework config: %s", str(e))
                pass


def config_gen_query(session, criteria):
    """Generate query

    :param criteria: Filter criteria
    :type criteria: `dict`
    :return:
    :rtype:
    """
    query = session.query(Config)
    if criteria.get("key", None):
        if isinstance(criteria["key"], str):
            query = query.filter_by(key=criteria["key"])
        if isinstance(criteria["key"], list):
            query = query.filter(Config.key.in_(criteria["key"]))
    if criteria.get("section", None):
        if isinstance(criteria["section"], str):
            query = query.filter_by(section=criteria["section"])
        if isinstance(criteria["section"], list):
            query = query.filter(Config.section.in_(criteria["section"]))
    if criteria.get("dirty", None):
        if isinstance(criteria.get("dirty"), list):
            criteria["dirty"] = criteria["dirty"][0]
        query = query.filter_by(dirty=str2bool(criteria["dirty"]))
    return query.order_by(Config.key)


def get_all_config_dicts(session, criteria=None):
    """Get all config dicts for a criteria

    :param criteria: Filter criteria
    :type criteria: `dict`
    :return: Config dict
    :rtype: `dict`
    """
    if not criteria:
        criteria = {}
    query = config_gen_query(session, criteria)
    return [config_obj.to_dict() for config_obj in query.all() if config_obj]


def get_all_tools(session):
    """Get all tools from the config DB

    :return: Config dict for all tools
    :rtype: `dict`
    """
    results = session.query(Config).filter(Config.key.like("%TOOL_%")).all()
    config_dicts = [config_obj.to_dict() for config_obj in results if config_obj]
    for config_dict in config_dicts:
        config_dict["value"] = multi_replace(
            config_dict["value"], config_handler.get_replacement_dict
        )
    return config_dicts


def update_config_val(session, key, value):
    """Update the configuration value for a key

    :param key: Key whose value to update
    :type key: `str`
    :param value: New value
    :type value: `str`
    :return: None
    :rtype: None
    """
    config_obj = session.query(Config).get(key)
    if config_obj:
        config_obj.value = value
        config_obj.dirty = True
        session.merge(config_obj)
        session.commit()
    else:
        raise InvalidConfigurationReference(
            "No setting exists with key: {!s}".format(key)
        )


def get_conf(session):
    """Get the config dict

    :return: Replaced dict
    :rtype: `dict`
    """
    config_dict = {}
    config_list = session.query(Config.key, Config.value).all()
    for key, value in config_list:  # Need a dict
        config_dict[key] = value
    return config_dict
