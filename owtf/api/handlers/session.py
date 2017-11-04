"""
owtf.api.handlers.session
~~~~~~~~~~~~~~~~~~~~~~

"""

import tornado.gen
import tornado.web
import tornado.httpclient

from owtf.lib import exceptions
from owtf.api.base import APIRequestHandler


class OWTFSessionHandler(APIRequestHandler):
    SUPPORTED_METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']

    def get(self, session_id=None, action=None):
        if action is not None:  # Action must be there only for put
            raise tornado.web.HTTPError(400)
        if session_id is None:
            filter_data = dict(self.request.arguments)
            self.write(self.get_component("session_db").get_all(filter_data))
        else:
            try:
                self.write(self.get_component("session_db").get(session_id))
            except exceptions.InvalidSessionReference:
                raise tornado.web.HTTPError(400)

    def post(self, session_id=None, action=None):
        if (session_id is not None) or (self.get_argument("name", None) is None) or (action is not None):
            # Not supposed to post on specific session
            raise tornado.web.HTTPError(400)
        try:
            self.get_component("session_db").add_session(self.get_argument("name"))
            self.set_status(201)  # Stands for "201 Created"
        except exceptions.DBIntegrityException:
            raise tornado.web.HTTPError(409)

    def patch(self, session_id=None, action=None):
        target_id = self.get_argument("target_id", None)
        if (session_id is None) or (target_id is None and action in ["add", "remove"]):
            raise tornado.web.HTTPError(400)
        try:
            if action == "add":
                self.get_component("session_db").add_target_to_session(int(self.get_argument("target_id")),
                                                                       session_id=int(session_id))
            elif action == "remove":
                self.get_component("session_db").remove_target_from_session(int(self.get_argument("target_id")),
                                                                            session_id=int(session_id))
            elif action == "activate":
                self.get_component("session_db").set_session(int(session_id))
        except exceptions.InvalidTargetReference:
            raise tornado.web.HTTPError(400)
        except exceptions.InvalidSessionReference:
            raise tornado.web.HTTPError(400)

    def delete(self, session_id=None, action=None):
        if (session_id is None) or action is not None:
            raise tornado.web.HTTPError(400)
        try:
            self.get_component("session_db").delete_session(int(session_id))
        except exceptions.InvalidSessionReference:
            raise tornado.web.HTTPError(400)
