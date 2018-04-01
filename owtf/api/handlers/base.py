"""
owtf.api.base
~~~~~~~~~~~~~

"""
import json

from tornado.web import RequestHandler

__all__ = ['APIRequestHandler', 'UIRequestHandler']


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
