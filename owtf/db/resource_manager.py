"""
owtf.db.resource_manager
~~~~~~~~~~~~~~~~~~~~~~~~

"""

import os
import logging

from owtf.utils import FileOperations
from owtf.db import models
from owtf.dependency_management.dependency_resolver import BaseComponent
from owtf.dependency_management.interfaces import ResourceInterface
from owtf.lib.general import cprint


class ResourceDB(BaseComponent, ResourceInterface):

    COMPONENT_NAME = "resource"

    def __init__(self):
        self.register_in_service_locator()
        self.config = self.get_component("config")
        self.db_config = self.get_component("db_config")
        self.target = self.get_component("target")
        self.db = self.get_component("db")
        self.error_handler = self.get_component("error_handler")

    def init(self):
        self.load_resources_from_file(self.config.get_profile_path("RESOURCES_PROFILE"))

    def load_resources_from_file(self, file_path):
        """Parses the resources config file and loads data into the DB
        .note::
            This needs to be a list instead of a dictionary to preserve order in python < 2.7

        :param file_path: Path to the resources config file
        :type file_path: `str`
        :return: None
        :rtype: None
        """
        file_path = self.config.select_user_or_default_config_path(file_path)
        logging.info("Loading Resources from: %s..", file_path)
        if not os.path.isfile(file_path):  # check if the resource file exists
            self.error_handler.abort_framework("Resource file not found at: %s" % file_path)
        resources = self.get_resources_from_file(file_path)
        # Delete all old resources which are not edited by user
        # because we may have updated the resource
        self.db.session.query(models.Resource).filter_by(dirty=False).delete()
        for type, name, resource in resources:
            self.db.session.add(models.Resource(resource_type=type, resource_name=name, resource=resource))
        self.db.session.commit()

    def get_resources_from_file(self, resource_file):
        """Fetch resources for a file

        :param resource_file: Path to the resource file
        :type resource_file: `str`
        :return: Resources as a set
        :rtype: `set`
        """
        resources = set()
        config_file = FileOperations.open(resource_file, 'r').read().splitlines()  # To remove stupid '\n' at the end
        for line in config_file:
            if '#' == line[0]:
                continue  # Skip comment lines
            try:
                type, name, resource = line.split('_____')
                resources.add((type, name, resource))
            except ValueError:
                cprint("ERROR: The delimiter is incorrect in this line at Resource File: %s" % str(line.split('_____')))
        return resources

    def get_replacement_dict(self):
        """Get the configuration update changes as a dict

        :return:
        :rtype:
        """
        configuration = self.db_config.get_replacement_dict()
        configuration.update(self.target.get_target_config())
        configuration.update(self.config.get_replacement_dict())
        configuration.update(self.config.get_framework_config_dict()) # for aux plugins
        return configuration

    def get_raw_resources(self, resource_type):
        """Fetch raw resources filtered on type

        :param resource_type: Resource type
        :type resource_type: `str`
        :return: List of raw resources
        :rtype: `list`
        """
        filter_query = self.db.session.query(models.Resource.resource_name, models.Resource.resource).filter_by(
            resource_type=resource_type)
        # Sorting is necessary for working of ExtractURLs, since it must run after main command, so order is imp
        sort_query = filter_query.order_by(models.Resource.id)
        raw_resources = sort_query.all()
        return raw_resources

    def get_resources(self, resource_type):
        """Fetch resources filtered on type

        :param resource_type: Resource type
        :type resource_type: `str`
        :return: List of resources
        :rtype: `list`
        """
        replacement_dict = self.get_replacement_dict()
        raw_resources = self.get_raw_resources(resource_type)
        resources = []
        for name, resource in raw_resources:
            resources.append([name, self.config.multi_replace(resource, replacement_dict)])
        return resources

    def get_raw_resource_list(self, resource_list):
        """Get raw resources as from a resource list

        :param resource_list: List of resource types
        :type resource_list: `list`
        :return: List of raw resources
        :rtype: `list`
        """
        raw_resources = self.db.session.query(models.Resource.resource_name, models.Resource.resource).filter(
            models.Resource.resource_type.in_(resource_list)).all()
        return raw_resources

    def get_resource_list(self, resource_type_list):
        """Get list of resources from list of types

        :param resource_type_list: List of resource types
        :type resource_type_list: `list`
        :return: List of resources
        :rtype: `list`
        """
        replacement_dict = self.get_replacement_dict()
        raw_resources = self.get_raw_resource_list(resource_type_list)
        resources = []
        for name, resource in raw_resources:
            resources.append([name, self.config.multi_replace(resource, replacement_dict)])
        return resources
