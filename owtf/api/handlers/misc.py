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
from owtf.managers.poutput import get_severity_freq, plugin_count_output
from owtf.api.handlers.jwtauth import jwtauth


@jwtauth
class DashboardPanelHandler(APIRequestHandler):
    SUPPORTED_METHODS = ["GET"]

    def get(self):
        try:
            self.write(get_severity_freq(self.session))
        except exceptions.InvalidParameterType:
            raise tornado.web.HTTPError(400)


@jwtauth
class ProgressBarHandler(APIRequestHandler):
    SUPPORTED_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE"]

    def set_default_headers(self):
        self.add_header("Access-Control-Allow-Origin", "*")
        self.add_header("Access-Control-Allow-Methods", "GET, POST, DELETE")

    def get(self):
        try:
            self.write(plugin_count_output(self.session))
        except exceptions.InvalidParameterType as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)

    def post(self):
        raise tornado.web.HTTPError(405)

    def put(self):
        raise tornado.web.HTTPError(405)

    def patch(self):
        raise tornado.web.HTTPError(405)

    def delete(self):
        raise tornado.web.HTTPError(405)


@jwtauth
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

    def post(self, error_id=None):
        if error_id is None:
            filter_data = dict(self.request.arguments)
            message = filter_data["message"][0]
            trace = filter_data["trace"][0]
            err_obj = Error.add_error(self.session, message, trace)
            self.write(err_obj)
        else:
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
