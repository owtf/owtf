"""
owtf.managers.mapping
~~~~~~~~~~~~~~~~~~~~~
Manages the mapping between different plugin groups and codes
"""
import json

from owtf.lib.exceptions import InvalidMappingReference
from owtf.managers.config import load_config_file
from owtf.models.mapping import Mapping
from owtf.utils.pycompat import iteritems

mapping_types = []


def get_mapping_types():
    """In memory data saved when loading db
    :return: None
    :rtype: None
    """
    return mapping_types


def get_mappings(session, mapping_type):
    """Fetches mappings from DB based on mapping type

    :param mapping_type: Mapping type like OWTF, OWASP (v3, v4, Top 10), NIST, CWE
    :type mapping_type: `str`
    :return: Mappings
    :rtype: `dict`
    """
    if mapping_type in mapping_types:
        mapping_objs = session.query(Mapping).all()
        obj_dicts = [obj.to_dict() for obj in mapping_objs]
        mappings = {}
        for mapping_dict in obj_dicts:
            if mapping_dict["mappings"].get(mapping_type, None):
                mappings[mapping_dict["owtf_code"]] = mapping_dict["mappings"][mapping_type]
        return mappings
    else:
        raise InvalidMappingReference("InvalidMappingReference {!s} requested".format(mapping_type))


def load_mappings(session, default, fallback):
    """Loads the mappings from the config file

    .. note::
        This needs to be a list instead of a dictionary to preserve order in python < 2.7

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
    for owtf_code, mappings in iteritems(config_dump):
        category = None
        if "category" in mappings:
            category = mappings.pop("category")
        session.merge(Mapping(owtf_code=owtf_code, mappings=json.dumps(mappings), category=category))
    session.commit()
