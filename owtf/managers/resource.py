"""
owtf.managers.resource
~~~~~~~~~~~~~~~~~~~~~~
Provides helper functions for plugins to fetch resources.
"""
import logging
import os

from owtf.db.session import get_scoped_session
from owtf.managers.config import get_conf
from owtf.models.resource import Resource
from owtf.utils.file import FileOperations
from owtf.utils.strings import multi_replace


def get_raw_resources(session, resource_type):
    """Fetch raw resources filtered on type

    :param resource_type: Resource type
    :type resource_type: `str`
    :return: List of raw resources
    :rtype: `list`
    """
    filter_query = session.query(Resource.resource_name, Resource.resource).filter_by(
        resource_type=resource_type
    )
    # Sorting is necessary for working of ExtractURLs, since it must run after main command, so order is imp
    sort_query = filter_query.order_by(Resource.id)
    raw_resources = sort_query.all()
    return raw_resources


def get_rsrc_replacement_dict(session):
    """Get the configuration update changes as a dict
    :return:
    :rtype:
    """
    from owtf.managers.target import target_manager
    from owtf.managers.config import config_handler

    configuration = get_conf(session)
    configuration.update(target_manager.get_target_config)
    configuration.update(config_handler.get_replacement_dict)
    configuration.update(config_handler.get_framework_config_dict)  # for aux plugins
    return configuration


def get_resources(resource_type):
    """Fetch resources filtered on type

    :param resource_type: Resource type
    :type resource_type: `str`
    :return: List of resources
    :rtype: `list`
    """
    session = get_scoped_session()
    replacement_dict = get_rsrc_replacement_dict(session)
    raw_resources = get_raw_resources(session, resource_type)
    resources = []
    for name, resource in raw_resources:
        resources.append([name, multi_replace(resource, replacement_dict)])
    return resources


def get_raw_resource_list(session, resource_list):
    """Get raw resources as from a resource list

    :param resource_list: List of resource types
    :type resource_list: `list`
    :return: List of raw resources
    :rtype: `list`
    """
    raw_resources = session.query(Resource.resource_name, Resource.resource).filter(
        Resource.resource_type.in_(resource_list)
    ).all()
    return raw_resources


def get_resource_list(session, resource_type_list):
    """Get list of resources from list of types

    :param resource_type_list: List of resource types
    :type resource_type_list: `list`
    :return: List of resources
    :rtype: `list`
    """
    replacement_dict = get_rsrc_replacement_dict(session)
    raw_resources = get_raw_resource_list(session, resource_type_list)
    resources = []
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
    config_file = FileOperations.open(
        resource_file, "r"
    ).read().splitlines()  # To remove stupid '\n' at the end
    for line in config_file:
        if line.startswith("#"):
            continue  # Skip comment lines
        try:
            type, name, resource = line.split("_____")
            resources.add((type, name, resource))
        except ValueError:
            logging.info(
                "ERROR: The delimiter is incorrect in this line at Resource File: %s",
                str(line.split("_____")),
            )
    return resources


def load_resources_from_file(session, default, fallback):
    """Parses the resources config file and loads data into the DB
    .. note::

        This needs to be a list instead of a dictionary to preserve order in python < 2.7

    :param file_path: Path to the resources config file
    :type file_path: `str`
    :return: None
    :rtype: None
    """
    file_path = default
    logging.info("Loading resources from: %s..", default)
    if not os.path.isfile(default):  # check if the resource file exists
        file_path = fallback
    resources = get_resources_from_file(file_path)
    # Delete all old resources which are not edited by user
    # because we may have updated the resource
    session.query(Resource).filter_by(dirty=False).delete()
    for type, name, resource in resources:
        session.add(Resource(resource_type=type, resource_name=name, resource=resource))
    session.commit()
