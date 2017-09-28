"""
owtf.db.mapping_manager
~~~~~~~~~~~~~~~~~~~~~~~

Manages the mapping between different plugin groups and codes
"""

import os
import json
import logging
try:
    import configparser as parser
except ImportError:
    import ConfigParser as parser

from owtf.db import models
from owtf.dependency_management.dependency_resolver import BaseComponent
from owtf.dependency_management.interfaces import MappingDBInterface
from owtf.lib.exceptions import InvalidMappingReference


class MappingDB(BaseComponent, MappingDBInterface):

    COMPONENT_NAME = "mapping_db"

    def __init__(self):
        """
        The mapping_types attributes contain the unique mappings in memory
        """
        self.register_in_service_locator()
        self.config = self.get_component("config")
        self.db = self.get_component("db")
        self.mapping_types = list()
        self.error_handler = self.get_component("error_handler")

    def init(self):
        self.load_mappings_from_file(self.config.get_profile_path("MAPPING_PROFILE"))

    def load_mappings_from_file(self, file_path):
        """Loads the mappings from the config file

        .note::
            This needs to be a list instead of a dictionary to preserve order in python < 2.7

        :param file_path: The path to the mappings config file
        :type file_path: `str`
        :return: None
        :rtype: None
        """
        file_path = self.config.select_user_or_default_config_path(file_path)
        logging.info("Loading Mapping from: %s..", file_path)
        config_parser = parser.RawConfigParser()
        # Otherwise all the keys are converted to lowercase xD
        config_parser.optionxform = str
        if not os.path.isfile(file_path):  # check if the mapping file exists
            self.error_handler.abort_framework("Mapping file not found at: %s" % file_path)
        config_parser.read(file_path)
        for owtf_code in config_parser.sections():
            mappings = {}
            category = None
            for mapping_type, data in config_parser.items(owtf_code):
                if mapping_type != 'category':
                    if mapping_type not in self.mapping_types:
                        self.mapping_types.append(mapping_type)
                    mapped_code, mapped_name = data.split('_____')
                    mappings[mapping_type] = [mapped_code, mapped_name]
                else:
                    category = data
            self.db.session.merge(models.Mapping(owtf_code=owtf_code, mappings=json.dumps(mappings), category=category))
        self.db.session.commit()

    def derive_mapping_dict(self, obj):
        """Fetch the mapping dict from an object

        :param obj: The mapping object
        :type obj:
        :return: Mappings dict
        :rtype: `dict`
        """
        if obj:
            pdict = dict(obj.__dict__)
            pdict.pop("_sa_instance_state", None)
            # If output is present, json decode it
            if pdict.get("mappings", None):
                pdict["mappings"] = json.loads(pdict["mappings"])
            return pdict

    def derive_mapping_dicts(self, obj_list):
        """Fetches the mapping dicts based on the objects list

        :param obj_list: The plugin object list
        :type obj_list: `list`
        :return: Mapping dicts as a list
        :rtype: `list`
        """
        dict_list = []
        for obj in obj_list:
            dict_list.append(self.derive_mapping_dict(obj))
        return dict_list

    def get_mapping_types(self):
        """In memory data saved when loading db

        :return: None
        :rtype: None
        """
        return self.mapping_types

    def get_all_mappings(self):
        """Create a mapping between OWTF plugins code and OWTF plugins description.

        :return: Mapping dictionary {code: [mapped_code, mapped_description], code2: [mapped_code, mapped_description], ...}
        :rtype: dict
        """
        mapping_objs = self.db.session.query(models.Mapping).all()
        return {mapping['owtf_code']: mapping['mappings'] for mapping in self.derive_mapping_dicts(mapping_objs)}

    def get_mappings(self, mapping_type):
        """Fetches mappings from DB based on mapping type

        :param mapping_type: Mapping type like OWTF, OWASP (v3, v4, Top 10), NIST, CWE
        :type mapping_type: `str`
        :return: Mappings
        :rtype: `dict`
        """
        if mapping_type in self.mapping_types:
            mapping_objs = self.db.session.query(models.Mapping).all()
            mappings = {}
            for mapping_dict in self.derive_mapping_dicts(mapping_objs):
                if mapping_dict["mappings"].get(mapping_type, None):
                    mappings[mapping_dict["owtf_code"]] = mapping_dict["mappings"][mapping_type]
            return mappings
        else:
            raise InvalidMappingReference("InvalidMappingReference %s requested" % mapping_type)

    def get_category(self, plugin_code):
        """Get the categories for a plugin code

        :param plugin_code: The code for the specific plugin
        :type plugin_code:  `int`
        :return: category for the plugin code
        :rtype: `str`
        """
        category = self.db.session.query(models.Mapping.category).get(plugin_code)
        # Getting the corresponding category back from db
        return category
