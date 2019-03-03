"""
owtf.api.handlers.session
~~~~~~~~~~~~~~~~~~~~~~~~~

"""
from owtf.api.handlers.base import APIRequestHandler
from owtf.models.session import Session
from owtf.lib import exceptions
from owtf.lib.exceptions import APIError
from owtf.managers.session import (
    add_session,
    add_target_to_session,
    delete_session,
    get_all_session_dicts,
    remove_target_from_session,
)

__all__ = ["OWTFSessionHandler"]


class OWTFSessionHandler(APIRequestHandler):
    """Handles OWTF sessions."""

    SUPPORTED_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE"]

    def get(self, session_id=None, action=None):
        """Get all registered sessions.

        **Example request**:

        .. sourcecode:: http

                GET /api/v1/sessions/ HTTP/1.1
                Accept: application/json, text/javascript, */*; q=0.01
                X-Requested-With: XMLHttpRequest

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
                "status": "success",
                "data": [
                    {
                        "active": true,
                        "name": "default session",
                        "id": 1
                    }
                ]
            }
        """
        if action is not None:
            raise APIError(422, "Action must be None")
        if session_id is None:
            filter_data = dict(self.request.arguments)
            self.success(get_all_session_dicts(self.session, filter_data))
        else:
            try:
                self.success(Session.get_by_id(self.session, session_id))
            except exceptions.InvalidSessionReference:
                raise APIError(400, "Invalid session id provided")

    def post(self, session_id=None, action=None):
        """Create a new session.

        **Example request**:

        .. sourcecode:: http

            POST /api/v1/sessions/ HTTP/1.1
            Content-Type: application/x-www-form-urlencoded; charset=UTF-8
            X-Requested-With: XMLHttpRequest


            name=google-vrp

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 201 Created
            Content-Type: application/json

            {
                "status": "success",
                "data": null
            }
        """
        if (session_id is not None) or (self.get_argument("name", None) is None) or (action is not None):
            # Not supposed to post on specific session
            raise APIError(400, "Incorrect query parameters")
        try:
            add_session(self.session, self.get_argument("name"))
            self.set_status(201)  # Stands for "201 Created"
            self.success(None)
        except exceptions.DBIntegrityException:
            raise APIError(400, "An unknown exception occurred when performing a DB operation")

    def patch(self, session_id=None, action=None):
        """Change session.

        **Example request**:

        .. sourcecode:: http

            PATCH /api/v1/sessions/1/activate HTTP/1.1
            X-Requested-With: XMLHttpRequest

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
                "status": "success",
                "data": null
            }
        """
        target_id = self.get_argument("target_id", None)
        if (session_id is None) or (target_id is None and action in ["add", "remove"]):
            raise APIError(400, "Incorrect query parameters")
        try:
            if action == "add":
                add_target_to_session(self.session, int(self.get_argument("target_id")), session_id=int(session_id))
            elif action == "remove":
                remove_target_from_session(
                    self.session, int(self.get_argument("target_id")), session_id=int(session_id)
                )
            elif action == "activate":
                Session.set_by_id(self.session, int(session_id))
            self.success(None)
        except exceptions.InvalidTargetReference:
            raise APIError(400, "Invalid target reference provided")
        except exceptions.InvalidSessionReference:
            raise APIError(400, "Invalid parameter type provided")

    def delete(self, session_id=None, action=None):
        """Delete a session.

        **Example request**:

        .. sourcecode:: http

            DELETE /api/v1/sessions/2 HTTP/1.1
            X-Requested-With: XMLHttpRequest

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
                "status": "success",
                "data": null
            }
        """
        if session_id is None or action is not None:
            raise APIError(400, "Incorrect query parameters")
        try:
            delete_session(self.session, int(session_id))
            self.success(None)
        except exceptions.InvalidSessionReference:
            raise APIError(400, "Invalid session id provided")
