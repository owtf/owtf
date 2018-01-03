"""
owtf.db.resource_manager
~~~~~~~~~~~~~~~~~~~~~~~~

"""

import os
import logging

from owtf import config
from owtf.db import models
from owtf.managers.config import get_replacement_dict
from owtf.utils.error import abort_framework
from owtf.utils.file import FileOperations
from owtf.utils.strings import multi_replace, cprint


def get_raw_resources(resource_type):
    """Fetch raw resources filtered on type

    :param resource_type: Resource type
    :type resource_type: `str`
    :return: List of raw resources
    :rtype: `list`
    """
    filter_query = db.session.query(models.Resource.resource_name, models.Resource.resource).filter_by(
        resource_type=resource_type)
    # Sorting is necessary for working of ExtractURLs, since it must run after main command, so order is imp
    sort_query = filter_query.order_by(models.Resource.id)
    raw_resources = sort_query.all()
    return raw_resources


def get_resources(resource_type):
    """Fetch resources filtered on type

    :param resource_type: Resource type
    :type resource_type: `str`
    :return: List of resources
    :rtype: `list`
    """
    replacement_dict = get_replacement_dict()
    raw_resources = get_raw_resources(resource_type)
    resources = list()
    for name, resource in raw_resources:
        resources.append([name, config.multi_replace(resource, replacement_dict)])
    return resources


def get_raw_resource_list(resource_list):
    """Get raw resources as from a resource list

    :param resource_list: List of resource types
    :type resource_list: `list`
    :return: List of raw resources
    :rtype: `list`
    """
    raw_resources = db.session.query(models.Resource.resource_name, models.Resource.resource).filter(
        models.Resource.resource_type.in_(resource_list)).all()
    return raw_resources


def get_resource_list(resource_type_list):
    """Get list of resources from list of types

    :param resource_type_list: List of resource types
    :type resource_type_list: `list`
    :return: List of resources
    :rtype: `list`
    """
    replacement_dict = get_replacement_dict()
    raw_resources = get_raw_resource_list(resource_type_list)
    resources = list()
    for name, resource in raw_resources:
        resources.append([name, multi_replace(resource, replacement_dict)])
    return resources


def get_resources_from_file(resource_file):
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


def load_resources_from_file(default, fallback):
    """Parses the resources config file and loads data into the DB
    .note::
        This needs to be a list instead of a dictionary to preserve order in python < 2.7

    :param file_path: Path to the resources config file
    :type file_path: `str`
    :return: None
    :rtype: None
    """
    file_path = default
    logging.info("Loading Resources from: %s..", default)
    if not os.path.isfile(default):  # check if the resource file exists
        file_path = fallback
    resources = get_resources_from_file(file_path)
    # Delete all old resources which are not edited by user
    # because we may have updated the resource
    db.session.query(models.Resource).filter_by(dirty=False).delete()
    for type, name, resource in resources:
        db.session.add(models.Resource(resource_type=type, resource_name=name, resource=resource))
    db.session.commit()
