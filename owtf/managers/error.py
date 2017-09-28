"""
owtf.db.error_manager
~~~~~~~~~~~~~~~~~~~~~

Component to handle data storage and search of all errors
"""

from owtf.db import models
from owtf.dependency_management.dependency_resolver import BaseComponent
from owtf.dependency_management.interfaces import DBErrorInterface
from owtf.lib.exceptions import InvalidErrorReference


class ErrorDB(BaseComponent, DBErrorInterface):

    COMPONENT_NAME = "db_error"

    def __init__(self):
        self.register_in_service_locator()
        self.db = self.get_component("db")
        self.config = self.get_component("config")

    def add(self, message, trace):
        """Add an error to the DB

        :param message: Message to be added
        :type message: `str`
        :param trace: Traceback
        :type trace: `str`
        :return: None
        :rtype: None
        """
        error = models.Error(owtf_message=message, traceback=trace)
        self.db.session.add(error)
        self.db.session.commit()

    def delete(self, error_id):
        """Deletes an error from the DB

        :param error_id: ID of the error to be deleted
        :type error_id: `int`
        :return: None
        :rtype: None
        """
        error = self.db.session.query(models.Error).get(error_id)
        if error:
            self.db.session.delete(error)
            self.db.session.commit()
        else:
            raise InvalidErrorReference("No error with id %s" % str(error_id))

    def gen_query_session(self, criteria):
        """Generates the ORM query using the criteria

        :param criteria: Filter criteria
        :type criteria: `dict`
        :return:
        :rtype:
        """
        query = self.db.session.query(models.Error)
        if criteria.get('reported', None):
            if isinstance(criteria.get('reported'), list):
                criteria['reported'] = criteria['reported'][0]
            query = query.filter_by(reported=self.config.ConvertStrToBool(criteria['reported']))
        return query

    def update(self, error_id, user_message):
        """Update an error message in the DB

        :param error_id: ID of the error message
        :type error_id: `int`
        :param user_message: New message
        :type user_message: `str`
        :return: None
        :rtype: None
        """
        error = self.db.session.query(models.Error).get(error_id)
        if not error:  # If invalid error id, bail out
            raise InvalidErrorReference("No error with id %s" % str(error_id))
        error.user_message = user_message
        self.db.session.merge(error)
        self.db.session.commit()

    def update_after_github_report(self, error_id, traceback, reported, github_issue_url):
        """Store back the Github issue URL in the DB

        :param error_id: Id of the reported error message
        :type error_id: `int`
        :param traceback: Traceback
        :type traceback: `str`
        :param reported: Reported or not
        :type reported: `bool`
        :param github_issue_url: Github issue url
        :type github_issue_url: `str`
        :return: None
        :rtype: None
        """
        error = self.db.session.query(models.Error).get(error_id)
        if not error:  # If invalid error id, bail out
            raise InvalidErrorReference("No error with id %s" % str(error_id))

        # Save the reported issue in database
        error.traceback = traceback
        error.reported = reported
        error.github_issue_url = github_issue_url
        self.db.session.merge(error)
        self.db.session.commit()

    def derive_error_dict(self, error_obj):
        """Get the error dict from an object

        :param error_obj: Error object
        :type error_obj:
        :return: Error dict
        :rtype: `dict`
        """
        tdict = dict(error_obj.__dict__)
        tdict.pop("_sa_instance_state", None)
        return tdict

    def derive_error_dicts(self, error_obj_list):
        """Get error dicts for a list of error objs

        :param error_obj_list: List of error objects
        :type error_obj_list: `list`
        :return: List of error dicts
        :rtype: `list`
        """
        results = []
        for error_obj in error_obj_list:
            if error_obj:
                results.append(self.derive_error_dict(error_obj))
        return results

    def get_all(self, criteria=None):
        """Get all error dicts based on criteria

        :param criteria: Filter criteria
        :type criteria: `dict`
        :return: Error dicts
        :rtype: `list`
        """
        if not criteria:
            criteria = {}
        query = self.gen_query_session(criteria)
        results = query.all()
        return self.derive_error_dicts(results)

    def get(self, error_id):
        """Get an error based on the id

        :param error_id: Error id
        :type error_id: `int`
        :return: Error dict
        :rtype: `dict`
        """
        error = self.db.session.query(models.Error).get(error_id)
        if not error:  # If invalid error id, bail out
            raise InvalidErrorReference("No error with id %s" % str(error_id))
        return self.derive_error_dict(error)
