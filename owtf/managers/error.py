"""
owtf.db.error_manager
~~~~~~~~~~~~~~~~~~~~~

Component to handle data storage and search of all errors
"""

from owtf.db import models
from owtf.lib.exceptions import InvalidErrorReference
from owtf.utils.strings import str2bool


def add_error(session, message, trace):
    """Add an error to the DB

    :param message: Message to be added
    :type message: `str`
    :param trace: Traceback
    :type trace: `str`
    :return: None
    :rtype: None
    """
    error = models.Error(owtf_message=message, traceback=trace)
    session.add(error)
    session.commit()


def delete_error(session, error_id):
    """Deletes an error from the DB

    :param error_id: ID of the error to be deleted
    :type error_id: `int`
    :return: None
    :rtype: None
    """
    error = session.query(models.Error).get(error_id)
    if error:
        session.delete(error)
        session.commit()
    else:
        raise InvalidErrorReference("No error with id %s" % str(error_id))


def gen_query_error(session, criteria):
    """Generates the ORM query using the criteria

    :param criteria: Filter criteria
    :type criteria: `dict`
    :return:
    :rtype:
    """
    query = session.query(models.Error)
    if criteria.get('reported', None):
        if isinstance(criteria.get('reported'), list):
            criteria['reported'] = criteria['reported'][0]
        query = query.filter_by(reported=str2bool(criteria['reported']))
    return query


def update_error(session, error_id, user_message):
    """Update an error message in the DB

    :param error_id: ID of the error message
    :type error_id: `int`
    :param user_message: New message
    :type user_message: `str`
    :return: None
    :rtype: None
    """
    error = session.query(models.Error).get(error_id)
    if not error:  # If invalid error id, bail out
        raise InvalidErrorReference("No error with id %s" % str(error_id))
    error.user_message = user_message
    session.merge(error)
    session.commit()


def derive_error_dict(error_obj):
    """Get the error dict from an object

    :param error_obj: Error object
    :type error_obj:
    :return: Error dict
    :rtype: `dict`
    """
    tdict = dict(error_obj.__dict__)
    tdict.pop("_sa_instance_state", None)
    return tdict


def derive_error_dicts(error_obj_list):
    """Get error dicts for a list of error objs

    :param error_obj_list: List of error objects
    :type error_obj_list: `list`
    :return: List of error dicts
    :rtype: `list`
    """
    results = []
    for error_obj in error_obj_list:
        if error_obj:
            results.append(derive_error_dict(error_obj))
    return results


def get_all_errors(session, criteria=None):
    """Get all error dicts based on criteria

    :param criteria: Filter criteria
    :type criteria: `dict`
    :return: Error dicts
    :rtype: `list`
    """
    if not criteria:
        criteria = {}
    query = gen_query_error(session, criteria)
    results = query.all()
    return derive_error_dicts(results)


def get_error(session, error_id):
    """Get an error based on the id

    :param error_id: Error id
    :type error_id: `int`
    :return: Error dict
    :rtype: `dict`
    """
    error = session.query(models.Error).get(error_id)
    if not error:  # If invalid error id, bail out
        raise InvalidErrorReference("No error with id %s" % str(error_id))
    return derive_error_dict(error)
