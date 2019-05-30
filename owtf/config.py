"""
owtf.config
~~~~~~~~~~~

The Configuration object parses all configuration files, loads them into
memory, derives some settings and provides framework modules with a central
repository to get info.
"""
import logging
from collections import defaultdict

try:  # PY3
    from urllib.parse import urlparse
except ImportError:  # PY2
    from urlparse import urlparse
try:
    import configparser as parser
except ImportError:
    import ConfigParser as parser

from owtf.lib.exceptions import PluginAbortException
from owtf.settings import CONFIG_TYPES, REPLACEMENT_DELIMITER, ROOT_DIR

__all__ = ["config_handler"]


class Config(object):
    target = None

    def __init__(self):
        self.root_dir = ROOT_DIR
        self.config = defaultdict(list)  # General configuration information.
        for type in CONFIG_TYPES:
            self.config[
                type
            ] = {}  # key can consist alphabets, numbers, hyphen & underscore.
        self.cli_options = {}

    def is_set(self, key):
        """Checks if the key is set in the config dict

        :param key: Key to check
        :type key: `str`
        :return: True if present, else False
        :rtype: `bool`
        """
        key = self.pad_key(key)
        config = self.get_config_dict
        for type in CONFIG_TYPES:
            if key in config[type]:
                return True
        return False

    def get_key_val(self, key):
        """Gets the right config for target / general.

        :param key: The key
        :type key: `str`
        :return: Value for the key
        """
        config = self.get_config_dict
        for type in CONFIG_TYPES:
            if key in config[type]:
                return config[type][key]

    def pad_key(self, key):
        """Add delimiters.

        :param key: Key to pad
        :type key: `str`
        :return: Padded key string
        :rtype: `str`
        """
        return REPLACEMENT_DELIMITER + key + REPLACEMENT_DELIMITER

    def strip_key(self, key):
        """Replaces key with empty space

        :param key: Key to clear
        :type key: `str`
        :return: Empty key
        :rtype: `str`
        """
        return key.replace(REPLACEMENT_DELIMITER, "")

    def get_val(self, key):
        """Transparently gets config info from target or General.

        :param key: Key
        :type key: `str`
        :return: The value for the key
        """
        try:
            key = self.pad_key(key)
            return self.get_key_val(key)
        except KeyError:
            message = "The configuration item: %s does not exist!" % key
            # Raise plugin-level exception to move on to next plugin.
            raise PluginAbortException(message)

    def get_as_list(self, key_list):
        """Get values for keys in a list

        :param key_list: List of keys
        :type key_list: `list`
        :return: List of corresponding values
        :rtype: `list`
        """
        value_list = []
        for key in key_list:
            value_list.append(self.get_val(key))
        return value_list

    def get_header_list(self, key):
        """Get list from a string of values for a key

        :param key: Key
        :type key: `str`
        :return: List of values
        :rtype: `list`
        """
        return self.get_val(key).split(",")

    def set_general_val(self, type, key, value):
        """ Set value for a key in any config file

        :param type: Type of config file, framework or general.cfg
        :type type: `str`
        :param key: The key
        :type key: `str`
        :param value: Value to be set
        :type value:
        :return: None
        :rtype: None
        """
        self.config[type][key] = value

    def set_val(self, key, value):
        """set config items in target-specific or General config."""
        # Store config in "replacement mode", that way we can multiple-replace
        # the config on resources, etc.
        key = REPLACEMENT_DELIMITER + key + REPLACEMENT_DELIMITER
        type = "other"
        # Only when value is a string, store in replacements config.
        if isinstance(value, str):
            type = "string"
        return self.set_general_val(type, key, value)

    @property
    def get_framework_config_dict(self):
        return self.get_config_dict["string"]

    def __getitem__(self, key):
        return self.get_val(key)

    def __setitem__(self, key, value):
        return self.set_val(key, value)

    @property
    def get_config_dict(self):
        """Get the global config dictionary

        :return: None
        :rtype: None
        """
        return self.config

    @property
    def get_replacement_dict(self):
        return {"FRAMEWORK_DIR": self.root_dir}

    def show(self):
        """Print all keys and values from configuration dictionary

        :return: None
        :rtype: None
        """
        logging.info("Configuration settings: ")
        for k, v in list(self.get_config_dict.items()):
            logging.info("%s => %s", str(k), str(v))

    def get_tcp_ports(self, start_port, end_port):
        """Get TCP ports from the config file

        :param start_port: Start port in a range
        :type start_port: `str`
        :param end_port: End port
        :type end_port: `str`
        :return: Comma-separate string of tcp ports
        :rtype: `str`
        """
        return ",".join(
            self.get_val("TCP_PORTS").split(",")[int(start_port):int(end_port)]
        )

    def get_udp_ports(self, start_port, end_port):
        """Get UDP ports from the config file

        :param start_ort: Start port in a range
        :type start_port: `str`
        :param end_port: End port
        :type end_port: `str`
        :return: Comma-separate string of udp ports
        :rtype: `str`
        """
        return ",".join(
            self.get_val("UDP_PORTS").split(",")[int(start_port):int(end_port)]
        )


config_handler = Config()
