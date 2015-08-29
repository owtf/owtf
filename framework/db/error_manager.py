#!/usr/bin/env python
'''
Component to handle data storage and search of all errors
'''

from framework.db import models
from framework.dependency_management.dependency_resolver import BaseComponent
from framework.dependency_management.interfaces import DBErrorInterface
from framework.lib.exceptions import InvalidErrorReference


class ErrorDB(BaseComponent, DBErrorInterface):

    COMPONENT_NAME = "db_error"

    def __init__(self):
        self.register_in_service_locator()
        self.db = self.get_component("db")
        self.config = self.get_component("config")

    def Add(self, Message, Trace):
        error = models.Error(
            owtf_message=Message,
            traceback=Trace)
        self.db.session.add(error)
        self.db.session.commit()

    def Delete(self, error_id):
        error = self.db.session.query(models.Error).get(error_id)
        if error:
            self.db.session.delete(error)
            self.db.session.commit()
        else:
            raise InvalidErrorReference(
                "No error with id " + str(error_id))

    def GenerateQueryUsingSession(self, criteria):
        query = self.db.session.query(models.Error)
        if criteria.get('reported', None):
            if isinstance(criteria.get('reported'), list):
                criteria['reported'] = criteria['reported'][0]
            query = query.filter_by(
                reported=self.config.ConvertStrToBool(
                    criteria['reported']))
        return(query)

    def Update(self, error_id, user_message):
        error = self.db.session.query(models.Error).get(error_id)
        if not error:  # If invalid error id, bail out
            raise InvalidErrorReference(
                "No error with id " + str(error_id))
        error.user_message = patch_data["user_message"]
        self.db.session.merge(error)
        self.db.session.commit()

    def DeriveErrorDict(self, error_obj):
        tdict = dict(error_obj.__dict__)
        tdict.pop("_sa_instance_state", None)
        return(tdict)

    def DeriveErrorDicts(self, error_obj_list):
        results = []
        for error_obj in error_obj_list:
            if error_obj:
                results.append(self.DeriveErrorDict(error_obj))
        return results

    def GetAll(self, criteria=None):
        if not criteria:
            criteria = {}
        query = self.GenerateQueryUsingSession(criteria)
        results = query.all()
        return(self.DeriveErrorDicts(results))

    def Get(self, error_id):
        error = self.db.session.query(models.Error).get(error_id)
        if not error:  # If invalid error id, bail out
            raise InvalidErrorReference(
                "No error with id " + str(error_id))
        return(self.DeriveErrorDict(error))
