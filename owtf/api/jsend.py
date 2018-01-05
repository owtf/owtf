import tornado.web


class JSendMixin(tornado.web.RequestHandler):
    """http://labs.omniti.com/labs/jsend

    JSend is a specification that lays down some rules for how JSON
    responses from web servers should be formatted.

    JSend focuses on application-level (as opposed to protocol- or
    transport-level) messaging which makes it ideal for use in
    REST-style applications and APIs.
    """

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
