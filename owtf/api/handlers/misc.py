"""
owtf.api.handlers.misc
~~~~~~~~~~~~~~~~~~~

"""

import logging

import tornado.gen
import tornado.httpclient
import tornado.web

from owtf.api.handlers.base import APIRequestHandler
from owtf.lib import exceptions
from owtf.managers.error import get_all_errors, get_error, update_error, delete_error
from owtf.managers.poutput import get_severity_freq, plugin_count_output


class DashboardPanelHandler(APIRequestHandler):
    SUPPORTED_METHODS = ['GET']

    def get(self):
        try:
            self.write(get_severity_freq(self.session))
        except exceptions.InvalidParameterType:
            raise tornado.web.HTTPError(400)


class ProgressBarHandler(APIRequestHandler):
    SUPPORTED_METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']

    def set_default_headers(self):
        self.add_header("Access-Control-Allow-Origin", "*")
        self.add_header("Access-Control-Allow-Methods", "GET, POST, DELETE")

    def get(self):
        try:
            self.write(plugin_count_output(self.session))
        except exceptions.InvalidParameterType as e:
            logging.warn(e.parameter)
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
            self.write(get_all_errors(self.session, filter_data))
        else:
            try:
                self.write(get_error(self.session, error_id))
            except exceptions.InvalidErrorReference:
                raise tornado.web.HTTPError(400)

    def patch(self, error_id=None):
        if error_id is None:
            raise tornado.web.HTTPError(400)
        if self.request.arguments.get_argument("user_message", default=None):
            raise tornado.web.HTTPError(400)
        update_error(self.session, error_id, self.request.arguments.get_argument("user_message"))

    def delete(self, error_id=None):
        if error_id is None:
            raise tornado.web.HTTPError(400)
        try:
            delete_error(self.session, error_id)
        except exceptions.InvalidErrorReference:
            raise tornado.web.HTTPError(400)
