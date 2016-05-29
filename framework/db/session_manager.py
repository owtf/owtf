import os
import sqlalchemy.exc
from framework.db import models
from framework.dependency_management.dependency_resolver import BaseComponent, ServiceLocator
from framework.lib import exceptions


def session_required(func):
    """
    Inorder to use this decorator on a `method` there is one requirements
    + target_id must be a kwarg of the function

    All this decorator does is check if a valid value is passed for target_id
    if not get the target_id from target manager and pass it
    """
    def wrapped_function(*args, **kwargs):
        if (kwargs.get("session_id", "None") == "None") or (kwargs.get("session_id", True) is None):  # True if target_id doesnt exist
            kwargs["session_id"] = ServiceLocator.get_component("session_db").get_session_id()
        return func(*args, **kwargs)
    return wrapped_function


class OWTFSessionDB(BaseComponent):

    COMPONENT_NAME = "session_db"

    def __init__(self):
        self.register_in_service_locator()
        self.db = self.get_component("db")
        self.config = self.get_component("config")
        self._ensure_default_session()

    def _ensure_default_session(self):
        """
        If there are no sessions, it will be deadly, so if
        number of sessions is zero then add a default session
        """
        if self.db.session.query(models.Session).count() == 0:
            self.add_session("default session")

    def set_session(self, session_id):
        query = self.db.session.query(models.Session)
        session_obj = query.get(session_id)
        if session_obj is None:
            raise exceptions.InvalidSessionReference(
                "No session with session_id: " + str(session_id))
        query.update({'active': False})
        session_obj.active = True
        self.db.session.commit()

    def get_session_id(self):
        session_id = self.db.session.query(
            models.Session.id).filter_by(active=True).first()
        return session_id

    def add_session(self, session_name):
        existing_obj = self.db.session.query(
            models.Session).filter_by(name=session_name).first()
        if existing_obj is None:
            session_obj = models.Session(name=session_name[:50])
            self.db.session.add(session_obj)
            self.db.session.commit()
            self.set_session(session_obj.id)
        else:
            raise exceptions.DBIntegrityException(
                "Session already exists with session name: " + session_name)

    @session_required
    def add_target_to_session(self, target_id, session_id=None):
        session_obj = self.db.session.query(models.Session).get(session_id)
        target_obj = self.db.session.query(models.Target).get(target_id)
        if session_obj is None:
            raise exceptions.InvalidSessionReference(
                "No session with id: " + str(session_id))
        if target_obj is None:
            raise exceptions.InvalidTargetReference(
                "No target with id: " + str(target_id))
        if session_obj not in target_obj.sessions:
            session_obj.targets.append(target_obj)
            self.db.session.commit()

    @session_required
    def remove_target_from_session(self, target_id, session_id=None):
        session_obj = self.db.session.query(models.Session).get(session_id)
        target_obj = self.db.session.query(models.Target).get(target_id)
        if session_obj is None:
            raise exceptions.InvalidSessionReference(
                "No session with id: " + str(session_id))
        if target_obj is None:
            raise exceptions.InvalidTargetReference(
                "No target with id: " + str(target_id))
        session_obj.targets.remove(target_obj)
        # Delete target whole together if present in this session alone
        if len(target_obj.sessions) == 0:
            self.db.Target.DeleteTarget(ID=target_obj.id)
        self.db.session.commit()

    def delete_session(self, session_id):
        session_obj = self.db.session.query(
            models.Session).get(session_id)
        if session_obj is None:
            raise exceptions.InvalidSessionReference(
                "No session with id: " + str(session_id))
        for target in session_obj.targets:
            # Means attached to only this session obj
            if len(target.sessions) == 1:
                self.db.Target.DeleteTarget(ID=target.id)
        self.db.session.delete(session_obj)
        self._ensure_default_session()  # i.e if there are no sessions, add one
        self.db.session.commit()

    def derive_session_dict(self, session_obj):
        sdict = dict(session_obj.__dict__)
        sdict.pop("_sa_instance_state")
        return(sdict)

    def derive_session_dicts(self, session_objs):
        results = []
        for session_obj in session_objs:
            if session_obj:
                results.append(self.derive_session_dict(session_obj))
        return results

    def generate_query(self, filter_data=None):
        if filter_data is None:
            filter_data = {}
        query = self.db.session.query(models.Session)
        # it doesn't make sense to search in a boolean column :P
        if filter_data.get('active', None):
            if isinstance(filter_data.get('active'), list):
                filter_data['active'] = filter_data['active'][0]
            query = query.filter_by(
                active=self.config.ConvertStrToBool(filter_data['active']))
        return query.order_by(models.Session.id)

    def get_all(self, filter_data):
        session_objs = self.generate_query(filter_data).all()
        return(self.derive_session_dicts(session_objs))

    def get(self, session_id):
        session_obj = self.db.session.query(models.Session).get(session_id)
        if session_obj is None:
            raise exceptions.InvalidSessionReference(
                "No session with id: " + str(session_id))
        return(self.derive_session_dict(session_obj))
