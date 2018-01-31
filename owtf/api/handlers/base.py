"""
owtf.api.base
~~~~~~~~~~~~~

"""
import json

from tornado.escape import url_escape
from tornado.web import RequestHandler

from owtf.settings import FILE_SERVER_PORT, UI_SERVER_PORT


class APIRequestHandler(RequestHandler):

    def initialize(self):
        """
        - Set Content-type for JSON
        """
        self.session = self.application.session
        self.set_header("Content-Type", "application/json")

    def write(self, chunk):
        if isinstance(chunk, list):
            super(APIRequestHandler, self).write(json.dumps(chunk))
        else:
            super(APIRequestHandler, self).write(chunk)

    def write_error(self, status_code, **kwargs):
        """Override of RequestHandler.write_error
        Calls ``error()`` or ``fail()`` from JSendMixin depending on which
        exception was raised with provided reason and status code.
        :type  status_code: int
        :param status_code: HTTP status code
        """
        def get_exc_message(exception):
            return exception.log_message if \
                hasattr(exception, "log_message") else str(exception)

        self.clear()
        self.set_status(status_code)


class UIRequestHandler(RequestHandler):
    def reverse_url(self, name, *args):
        url = super(UIRequestHandler, self).reverse_url(name, *args)
        url = url.replace('?', '')
        return url.split('None')[0]


class FileRedirectHandler(RequestHandler):
    SUPPORTED_METHODS = ['GET']

    def get(self, file_url):
        output_files_server = "{}://{}/".format(self.request.protocol, self.request.host.replace(str(UI_SERVER_PORT),
                                                                                                 str(FILE_SERVER_PORT)))
        redirect_file_url = output_files_server + url_escape(file_url, plus=False)
        self.redirect(redirect_file_url, permanent=True)
