"""
owtf.api.handlers.misc
~~~~~~~~~~~~~~~~~~~

"""

import tornado.gen
import tornado.web
import tornado.httpclient

from owtf.lib import exceptions
from owtf.lib.general import cprint
from owtf.api.base import APIRequestHandler


class DashboardPanelHandler(APIRequestHandler):
    SUPPORTED_METHODS = ['GET']

    def get(self):
        try:
            self.write(self.get_component("plugin_output").get_severity_freq())
        except exceptions.InvalidParameterType:
            raise tornado.web.HTTPError(400)


class ProgressBarHandler(APIRequestHandler):
    SUPPORTED_METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']

    def set_default_headers(self):
        self.add_header("Access-Control-Allow-Origin", "*")
        self.add_header("Access-Control-Allow-Methods", "GET, POST, DELETE")

    def get(self):
        try:
            self.write(self.get_component("plugin_output").plugin_count_output())
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
            self.write(self.get_component("db_error").get_all(filter_data))
        else:
            try:
                self.write(self.get_component("db_error").get(error_id))
            except exceptions.InvalidErrorReference:
                raise tornado.web.HTTPError(400)

    def post(self, error_id=None):
        if error_id is None:
            try:
                filter_data = dict(self.request.arguments)
                username = filter_data['username'][0]
                title = filter_data['title'][0]
                body = filter_data['body'][0]
                id = int(filter_data['id'][0])
                self.write(self.get_component("error_handler").add_github_issue(username, title, body, id))
            except:
                raise tornado.web.HTTPError(400)
        else:
            raise tornado.web.HTTPError(400)

    def patch(self, error_id=None):
        if error_id is None:
            raise tornado.web.HTTPError(400)
        if self.request.arguments.get_argument("user_message", default=None):
            raise tornado.web.HTTPError(400)
        self.get_component("db_error").update(error_id, self.request.arguments.get_argument("user_message"))

    def delete(self, error_id=None):
        if error_id is None:
            raise tornado.web.HTTPError(400)
        try:
            self.get_component("db_error").delete(error_id)
        except exceptions.InvalidErrorReference:
            raise tornado.web.HTTPError(400)
