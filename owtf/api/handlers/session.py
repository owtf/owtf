"""
owtf.api.handlers.session
~~~~~~~~~~~~~~~~~~~~~~

"""

import tornado.gen
import tornado.httpclient
import tornado.web

from owtf.api.handlers.base import APIRequestHandler
from owtf.lib import exceptions
from owtf.managers.session import get_all_session_dicts, get_session_dict, add_session, add_target_to_session, \
    remove_target_from_session, set_session, delete_session


class OWTFSessionHandler(APIRequestHandler):
    SUPPORTED_METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']

    def get(self, session_id=None, action=None):
        if action is not None:  # Action must be there only for put
            raise tornado.web.HTTPError(400)
        if session_id is None:
            filter_data = dict(self.request.arguments)
            self.write(get_all_session_dicts(self.session, filter_data))
        else:
            try:
                self.write(get_session_dict(self.session, session_id))
            except exceptions.InvalidSessionReference:
                raise tornado.web.HTTPError(400)

    def post(self, session_id=None, action=None):
        if (session_id is not None) or (self.get_argument("name", None) is None) or (action is not None):
            # Not supposed to post on specific session
            raise tornado.web.HTTPError(400)
        try:
            add_session(self.session, self.get_argument("name"))
            self.set_status(201)  # Stands for "201 Created"
        except exceptions.DBIntegrityException:
            raise tornado.web.HTTPError(409)

    def patch(self, session_id=None, action=None):
        target_id = self.get_argument("target_id", None)
        if (session_id is None) or (target_id is None and action in ["add", "remove"]):
            raise tornado.web.HTTPError(400)
        try:
            if action == "add":
                add_target_to_session(self.session, int(self.get_argument("target_id")), session_id=int(session_id))
            elif action == "remove":
                remove_target_from_session(self.session, int(self.get_argument("target_id")), session_id=int(session_id))
            elif action == "activate":
                set_session(self.session, int(session_id))
        except exceptions.InvalidTargetReference:
            raise tornado.web.HTTPError(400)
        except exceptions.InvalidSessionReference:
            raise tornado.web.HTTPError(400)

    def delete(self, session_id=None, action=None):
        if (session_id is None) or action is not None:
            raise tornado.web.HTTPError(400)
        try:
            delete_session(self.session, int(session_id))
        except exceptions.InvalidSessionReference:
            raise tornado.web.HTTPError(400)
