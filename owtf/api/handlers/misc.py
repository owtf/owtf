"""
owtf.api.handlers.misc
~~~~~~~~~~~~~~~~~~~

"""

import tornado.gen
import tornado.web
import tornado.httpclient

from owtf.lib import exceptions
from owtf.api.base import APIRequestHandler
from owtf.managers.error import get_all_errors, get_error, update_error, delete_error
from owtf.managers.poutput import get_severity_freq, plugin_count_output
from owtf.utils.strings import cprint


class DashboardPanelHandler(APIRequestHandler):
    SUPPORTED_METHODS = ['GET']

    def get(self):
        try:
            self.write(get_severity_freq())
        except exceptions.InvalidParameterType:
            raise tornado.web.HTTPError(400)


class ProgressBarHandler(APIRequestHandler):
    SUPPORTED_METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']

    def set_default_headers(self):
        self.add_header("Access-Control-Allow-Origin", "*")
        self.add_header("Access-Control-Allow-Methods", "GET, POST, DELETE")

    def get(self):
        try:
            self.write(plugin_count_output())
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



class ErrorDataHandler(APIRequestHandler):
    SUPPORTED_METHODS = ['GET', 'POST', 'DELETE', 'PATCH']

    def get(self, error_id=None):
        if error_id is None:
            filter_data = dict(self.request.arguments)
            self.write(get_all_errors(filter_data))
        else:
            try:
                self.write(get_error(error_id))
            except exceptions.InvalidErrorReference:
                raise tornado.web.HTTPError(400)

    def patch(self, error_id=None):
        if error_id is None:
            raise tornado.web.HTTPError(400)
        if self.request.arguments.get_argument("user_message", default=None):
            raise tornado.web.HTTPError(400)
        update_error(error_id, self.request.arguments.get_argument("user_message"))

    def delete(self, error_id=None):
        if error_id is None:
            raise tornado.web.HTTPError(400)
        try:
            delete_error(error_id)
        except exceptions.InvalidErrorReference:
            raise tornado.web.HTTPError(400)
