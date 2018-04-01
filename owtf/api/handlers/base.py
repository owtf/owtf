"""
owtf.api.handlers.base
~~~~~~~~~~~~~~~~~~~~~~

"""
import json

from tornado.escape import url_escape
from tornado.web import RequestHandler

from owtf.lib.exceptions import APIError
from owtf.settings import SERVER_PORT, FILE_SERVER_PORT

__all__ = ['APIRequestHandler', 'FileRedirectHandler', 'UIRequestHandler']


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

    def success(self, data):
        """When an API call is successful, the JSend object is used as a simple
        envelope for the results, using the data key.

        :type  data: A JSON-serializable object
        :param data: Acts as the wrapper for any data returned by the API
            call. If the call returns no data, data should be set to null.
        """
        self.write({'status': 'success', 'data': data})
        self.finish()

    def fail(self, data):
        """There was a problem with the data submitted, or some pre-condition
        of the API call wasn't satisfied.

        :type  data: A JSON-serializable object
        :param data: Provides the wrapper for the details of why the request
            failed. If the reasons for failure correspond to POST values,
            the response object's keys SHOULD correspond to those POST values.
        """
        self.write({'status': 'fail', 'data': data})
        self.finish()

    def error(self, message, data=None, code=None):
        """An error occurred in processing the request, i.e. an exception was
        thrown.

        :type  data: A JSON-serializable object
        :param data: A generic container for any other information about the
            error, i.e. the conditions that caused the error,
            stack traces, etc.
        :type  message: A JSON-serializable object
        :param message: A meaningful, end-user-readable (or at the least
            log-worthy) message, explaining what went wrong
        :type  code: int
        :param code: A numeric code corresponding to the error, if applicable
        """
        result = {'status': 'error', 'message': message}
        if data:
            result['data'] = data
        if code:
            result['code'] = code
        self.write(result)
        self.finish()

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

        # Any APIError exceptions raised will result in a JSend fail written
        # back with the log_message as data. Hence, log_message should NEVER
        # expose internals. Since log_message is proprietary to HTTPError
        # class exceptions, all exceptions without it will return their
        # __str__ representation.
        # All other exceptions result in a JSend error being written back,
        # with log_message only written if debug mode is enabled
        exception = kwargs["exc_info"][1]
        if any(isinstance(exception, c) for c in [APIError]):
            self.fail(get_exc_message(exception))
        else:
            self.error(
                message=self._reason,
                data=get_exc_message(exception) if self.settings.get("debug") else None,
                code=status_code)


class UIRequestHandler(RequestHandler):

    def reverse_url(self, name, *args):
        url = super(UIRequestHandler, self).reverse_url(name, *args)
        url = url.replace('?', '')
        return url.split('None')[0]


class FileRedirectHandler(RequestHandler):
    SUPPORTED_METHODS = ['GET']

    def get(self, file_url):
        output_files_server = "{}://{}/".format(self.request.protocol,
                                                self.request.host.replace(str(SERVER_PORT), str(FILE_SERVER_PORT)))
        redirect_file_url = output_files_server + url_escape(file_url, plus=False)
        self.redirect(redirect_file_url, permanent=True)
