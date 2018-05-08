"""
owtf.api.handlers.base
~~~~~~~~~~~~~~~~~~~~~~

"""
import json
import re
import uuid

from tornado.escape import url_escape
from tornado.web import RequestHandler

from owtf import __version__
from owtf.db.session import Session, get_db_engine
from owtf.lib.exceptions import APIError
from owtf.settings import SERVER_PORT, FILE_SERVER_PORT, USE_SENTRY, SERVER_ADDR, SESSION_COOKIE_NAME
from owtf.utils.strings import utf8

# if Sentry raven library around, pull in SentryMixin
try:
    from raven.contrib.tornado import SentryMixin
except ImportError:
    pass
else:

    class SentryHandler(SentryMixin, RequestHandler):
        pass

    if USE_SENTRY:
        RequestHandler = SentryHandler

__all__ = ["APIRequestHandler", "FileRedirectHandler", "UIRequestHandler"]

# pattern for the authentication token header
auth_header_pat = re.compile(r"^(?:token|bearer)\s+([^\s]+)$", flags=re.IGNORECASE)


class BaseRequestHandler(RequestHandler):

    def set_default_headers(self):
        self.add_header("X-OWTF-Version", __version__)


class APIRequestHandler(BaseRequestHandler):

    def initialize(self):
        """
        - Set Content-type for JSON
        """
        Session.configure(bind=get_db_engine())
        self.session = Session()
        self.set_header("Content-Type", "application/json")

    def on_finish(self):
        self.session.close()

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
        self.write({"status": "success", "data": data})
        self.finish()

    def fail(self, data):
        """There was a problem with the data submitted, or some pre-condition
        of the API call wasn't satisfied.

        :type  data: A JSON-serializable object
        :param data: Provides the wrapper for the details of why the request
            failed. If the reasons for failure correspond to POST values,
            the response object's keys SHOULD correspond to those POST values.
        """
        self.write({"status": "fail", "data": data})
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
        result = {"status": "error", "message": message}
        if data:
            result["data"] = data
        if code:
            result["code"] = code
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
            return exception.log_message if hasattr(exception, "log_message") else str(exception)

        self.clear()
        self.set_status(status_code)

        try:
            exception = utf8(kwargs["exc_info"][1])
        except:
            exception = b""
        if any(isinstance(exception, c) for c in [APIError]):
            # ValidationError is always due to a malformed request
            if not isinstance(exception, APIError):
                self.set_status(400)
            self.write({"status": "fail", "data": get_exc_message(exception)})
            self.finish()
        else:
            self.write(
                {"status": "fail", "message": self._reason, "data": get_exc_message(exception), "code": status_code}
            )
            self.finish()

    def get_auth_token(self):
        """Get the authorization token from Authorization header"""
        auth_header = self.request.headers.get("Authorization", "")
        match = auth_header_pat.match(auth_header)
        if not match:
            return None
        return match.group(1)


class UIRequestHandler(BaseRequestHandler):

    def reverse_url(self, name, *args):
        url = super(UIRequestHandler, self).reverse_url(name, *args)
        url = url.replace("?", "")
        return url.split("None")[0]

    def _set_cookie(self, key, value, encrypted=True, **overrides):
        """Setting any cookie should go through here
        if encrypted use tornado's set_secure_cookie,
        otherwise set plaintext cookies.
        """
        # tornado <4.2 have a bug that consider secure==True as soon as
        # 'secure' kwarg is passed to set_secure_cookie
        kwargs = {"httponly": True}
        if self.request.protocol == "https":
            kwargs["secure"] = True
        kwargs["domain"] = SERVER_ADDR
        kwargs.update(overrides)

        if encrypted:
            set_cookie = self.set_secure_cookie
        else:
            set_cookie = self.set_cookie

        self.application.log.debug("Setting cookie %s: %s", key, kwargs)
        set_cookie(key, value, **kwargs)

    def _set_user_cookie(self, user, server):
        self.application.log.debug("Setting cookie for %s: %s", user.name, server.cookie_name)
        self._set_cookie(server.cookie_name, user.cookie_id, encrypted=True, path=server.base_url)

    def get_session_cookie(self):
        """Get the session id from a cookie
        Returns None if no session id is stored
        """
        return self.get_cookie(SESSION_COOKIE_NAME, None)

    def set_session_cookie(self):
        """Set a new session id cookie
        new session id is returned
        Session id cookie is *not* encrypted,
        so other services on this domain can read it.
        """
        session_id = uuid.uuid4().hex
        self._set_cookie(SESSION_COOKIE_NAME, session_id, encrypted=False)
        return session_id

    @property
    def template_context(self):
        user = self.get_current_user()
        return dict(user=user)


class FileRedirectHandler(BaseRequestHandler):
    SUPPORTED_METHODS = ["GET"]

    def get(self, file_url):
        output_files_server = "{}://{}/".format(
            self.request.protocol, self.request.host.replace(str(SERVER_PORT), str(FILE_SERVER_PORT))
        )
        redirect_file_url = output_files_server + url_escape(file_url, plus=False)
        self.redirect(redirect_file_url, permanent=True)
