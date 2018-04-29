"""
owtf.api.handlers.misc
~~~~~~~~~~~~~~~~~~~~~~

To be deprecated.
"""
import tornado.gen
import tornado.httpclient
import tornado.web

from owtf.api.handlers.base import APIRequestHandler
from owtf.lib import exceptions
from owtf.models.error import Error


class ErrorDataHandler(APIRequestHandler):
    SUPPORTED_METHODS = ["GET", "POST", "DELETE", "PATCH"]

    def get(self, error_id=None):
        if error_id is None:
            error_objs = Error.get_all_dict(self.session)
            self.write(error_objs)
        else:
            try:
                err_obj = Error.get_error(self.session, error_id)
                self.write(err_obj)
            except exceptions.InvalidErrorReference:
                raise tornado.web.HTTPError(400)

    def patch(self, error_id=None):
        if error_id is None:
            raise tornado.web.HTTPError(400)
        if self.request.arguments.get_argument("user_message", default=None):
            raise tornado.web.HTTPError(400)
        err_obj = Error.update_error(self.session, error_id, self.request.arguments.get_argument("user_message"))
        self.finish()

    def delete(self, error_id=None):
        if error_id is None:
            raise tornado.web.HTTPError(400)
        try:
            Error.delete_error(self.session, error_id)
            self.finish()
        except exceptions.InvalidErrorReference:
            raise tornado.web.HTTPError(400)
