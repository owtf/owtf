"""
owtf.requester.base
~~~~~~~~~~~~~~~~~~~
The Requester module is in charge of simplifying HTTP requests and
automatically log HTTP transactions by calling the DB module.
"""
import logging
import sys

try:
    import http.client as client
except ImportError:
    import httplib as client
try:
    from urllib.parse import urlparse, urlencode
    from urllib.request import urlopen, Request
    from urllib.error import HTTPError, URLError
    from urllib.request import (
        HTTPHandler,
        HTTPSHandler,
        HTTPRedirectHandler,
        ProxyHandler,
        build_opener,
        install_opener,
    )
except ImportError:
    from urlparse import urlparse
    from urllib import urlencode
    from urllib2 import (
        urlopen,
        Request,
        HTTPError,
        HTTPHandler,
        HTTPSHandler,
        HTTPRedirectHandler,
        ProxyHandler,
        build_opener,
        install_opener,
        URLError,
    )

from owtf.db.session import get_scoped_session
from owtf.transactions.base import HTTPTransaction
from owtf.managers.target import is_url_in_scope
from owtf.managers.transaction import get_first, is_transaction_already_added
from owtf.managers.url import is_url
from owtf.plugin.runner import runner
from owtf.settings import PROXY_CHECK_URL, USER_AGENT, INBOUND_PROXY_IP, INBOUND_PROXY_PORT
from owtf.utils.http import derive_http_method
from owtf.utils.strings import str_to_dict
from owtf.utils.timer import timer
from owtf.utils.error import abort_framework

__all__ = ["requester"]


# Intercept raw request trick from:
# http://stackoverflow.com/questions/6085709/get-headers-sent-in-urllib2-http-request
class _HTTPConnection(client.HTTPConnection):

    def send(self, s):
        global raw_request
        # Saving to global variable for Requester class to see.
        raw_request.append(s)
        client.HTTPConnection.send(self, s)


class _HTTPHandler(HTTPHandler):

    def http_open(self, req):
        try:
            return self.do_open(_HTTPConnection, req)
        except KeyboardInterrupt:
            raise KeyboardInterrupt  # Not handled here.
        except Exception:
            # Can't have OWTF crash due to a library exception -i.e. raise BadStatusLine(line)-
            return ""


class _HTTPSConnection(client.HTTPSConnection):

    def send(self, s):
        global raw_request
        # Saving to global variable for Requester class to see.
        raw_request.append(s)
        client.HTTPSConnection.send(self, s)


class _HTTPSHandler(HTTPSHandler):

    def https_open(self, req):
        try:
            return self.do_open(_HTTPSConnection, req)
        except KeyboardInterrupt:
            raise KeyboardInterrupt  # Not handled here.
        except Exception:
            # Can't have OWTF crash due to a library exception -i.e. raise BadStatusLine(line)-.
            return ""


# SmartRedirectHandler is courtesy of:
# http://www.diveintopython.net/http_web_services/redirects.html
class SmartRedirectHandler(HTTPRedirectHandler):

    def http_error_301(self, req, fp, code, msg, headers):
        result = HTTPRedirectHandler.http_error_301(self, req, fp, code, msg, headers)
        result.status = code
        return result

    def http_error_302(self, req, fp, code, msg, headers):
        result = HTTPRedirectHandler.http_error_302(self, req, fp, code, msg, headers)
        result.status = code
        return result


class Requester(object):

    def __init__(self, proxy):
        self.http_transaction = None
        self.headers = {"User-Agent": USER_AGENT}
        self.req_count_refused = 0
        self.req_count_total = 0
        self.log_transactions = False
        self.timer = timer
        self.session = get_scoped_session()
        self.proxy = proxy
        if proxy is None:
            logging.debug(
                "WARNING: No outbound proxy selected. It is recommended to "
                "use an outbound proxy for tactical fuzzing later"
            )
            self.opener = build_opener(_HTTPHandler, _HTTPSHandler, SmartRedirectHandler)
        else:  # All requests must use the outbound proxy.
            logging.debug("Setting up proxy(inbound) for OWTF requests..")
            ip, port = proxy
            proxy_conf = {"http": "http://{!s}:{!s}".format(ip, port), "https": "http://{!s}:{!s}".format(ip, port)}
            proxy_handler = ProxyHandler(proxy_conf)
            # FIXME: Works except no raw request on https.
            self.opener = build_opener(proxy_handler, _HTTPHandler, _HTTPSHandler, SmartRedirectHandler)
        install_opener(self.opener)

    def is_transaction_added(self, url):
        """Checks if the transaction has already been added

        :param url: URL of the transaction
        :type url: `str`
        :return: True/False
        :rtype: `bool`
        """
        return is_transaction_already_added(self.session, {"url": url.strip()})

    def is_request_possible(self):
        """Check if requests are possible

        :return: True if yes, else False
        :rtype: `bool`
        """
        return runner.requests_possible()

    def proxy_check(self):
        """Checks if the target URL can be accessed through proxy

        .. note::
            Verify proxy works! www.google.com might not work in a restricted network, try target URL :)

        :return: Result of the check
        :rtype: `list`
        """
        if self.proxy is not None and self.is_request_possible():
            url = PROXY_CHECK_URL
            refused_before = self.req_count_refused
            logging.info("Proxy Check: Avoid logging request again if already in DB..")
            log_setting_backup = False
            if self.is_transaction_added(url):
                log_setting_backup = not self.log_transactions
            if log_setting_backup:
                self.log_transactions = True
            refused_after = self.req_count_refused
            if refused_before < refused_after:  # Proxy is refusing connections.
                return [False, "ERROR: Proxy Check error: The proxy is not listening or is refusing connections"]
            else:
                return [True, "Proxy Check OK: The proxy appears to be working"]
        return [True, "Proxy Check OK: No proxy is setup or no HTTP requests will be made"]

    def get_headers(self):
        """Get headers

        :return: Headers
        :rtype: `dict`
        """
        return self.headers

    def set_headers(self, headers):
        """Set supplied headers

        :param headers: Headers to set
        :type headers: `dict`
        :return: None
        :rtype: None
        """
        self.headers = headers

    def set_header(self, header, value):
        """Set the value of header

        :param header: Header key
        :type header: `str`
        :param value: Value to be set
        :type value: `str`
        :return: None
        :rtype: None
        """
        self.headers[header] = value

    def get_post_to_str(self, post=None):
        """Convert POST req to str

        :param post: POST request
        :type post:
        :return: Resultant string
        :rtype: `str`
        """
        post = self.get_post(post)
        if post is None:
            return ""
        return post

    def get_post(self, post=None):
        """Get post request

        :param post: Post request
        :type post: `str`
        :return: Processed POST request
        :rtype: `str`
        """
        if "" == post:
            post = None
        if post:
            if isinstance(post, str) or isinstance(post, unicode):
                # Must be a dictionary prior to urlencode.
                post = str_to_dict(str(post))
            post = urlencode(post).encode("utf-8")
        return post

    def perform_request(self, request):
        """Send the request

        :param request: Request to send
        :type request:
        :return: None
        :rtype: None
        """
        return urlopen(request)

    def set_successful_transaction(self, raw_request, response):
        """Set a transaction from request and response

        :param raw_request: Raw request
        :type raw_request: `list`
        :param response: response
        :type response:
        :return: None
        :rtype: None
        """
        return self.http_transaction.set_transaction(True, raw_request[0], response)

    def log_transaction(self):
        """Log a transaction

        :return: None
        :rtype: None
        """
        self.http_transaction.log_transaction(self.http_transaction)

    def request(self, url, method=None, post=None):
        """Main request function

        :param url: Target URL
        :type url: `str`
        :param method: Method for the request
        :type method: `str`
        :param post: Post body
        :type post: `str` or None
        :return:
        :rtype:
        """
        # kludge: necessary to get around urllib2 limitations: Need this to get the exact request that was sent.
        global raw_request
        url = str(url)

        raw_request = []  # initialize raw request to blank list.
        post = self.get_post(post)
        method = derive_http_method(method, post)
        url = url.strip()  # Clean up URL.
        r = Request(url, post, self.headers)  # GET request.
        if method is not None:
            # kludge: necessary to do anything other that GET or POST with urllib2
            r.get_method = lambda: method
        # MUST create a new Transaction object each time so that lists of
        # transactions can be created and process at plugin-level
        # Pass the timer object to avoid instantiating each time.
        self.http_transaction = HTTPTransaction(self.timer)
        self.http_transaction.start(url, post, method, is_url_in_scope(url))
        self.req_count_total += 1
        try:
            response = self.perform_request(r)
            self.set_successful_transaction(raw_request, response)
        except HTTPError as error:  # page NOT found.
            # Error is really a response for anything other than 200 OK in urllib2 :)
            self.http_transaction.set_transaction(False, raw_request[0], error)
        except URLError as error:  # Connection refused?
            err_message = self.process_http_error_code(error, url)
            self.http_transaction.set_error(err_message)
        except IOError:
            err_message = "ERROR: Requester Object -> Unknown HTTP Request error: {!s}\n{!s}".format(
                url, str(sys.exc_info())
            )
            self.http_transaction.set_error(err_message)
        if self.log_transactions:
            # Log transaction in DB for analysis later and return modified Transaction with ID.
            self.log_transaction()
        return self.http_transaction

    def process_http_error_code(self, error, url):
        """Process HTTP error code
        :param error: Error
        :type error:
        :param url: Target URL
        :type url: `str`
        :return: Message
        :rtype: `str`
        """
        message = ""
        if str(error.reason).startswith("[Errno 111]"):
            message = "ERROR: The connection was refused!: {!s}".format(error)
            self.req_count_refused += 1
        elif str(error.reason).startswith("[Errno -2]"):
            abort_framework("ERROR: cannot resolve hostname!: {!s}".format(error))
        else:
            message = "ERROR: The connection was not refused, unknown error!"
        log = logging.getLogger("general")
        log.info(message)
        return "{!s} (Requester Object): {!s}\n{!s}".format(message, url, str(sys.exc_info()))

    def get(self, url):
        """Wrapper for get requests

        :param url: Target url
        :type url: `str`
        :return:
        :rtype:
        """
        return self.request(url)

    def post(self, url, data):
        """Wrapper for Post requests

        :param url: Target url
        :type url: `str`
        :param data: Post data
        :type data: `str`
        :return:
        :rtype:
        """
        return self.request(url, "POST", data)

    def trace(self, url):
        """Wrapper for trace requests

        :param url: Target url
        :type url: `str`
        :return:
        :rtype:
        """
        return self.request(url, "TRACE", None)

    def options(self, url):
        """Wrapper for options requests

        :param url: Target url
        :type url: `str`
        :return:
        :rtype:
        """
        return self.request(url, "OPTIONS", None)

    def head(self, url):
        """Wrapper for head requests

        :param url: Target url
        :type url: `str`
        :return:
        :rtype:
        """
        return self.request(url, "HEAD", None)

    def debug(self, url):
        """Debug request

        :param url: Target url
        :type url: `str`
        :return:
        :rtype:
        """
        self.backup_headers()
        self.headers["Command"] = "start-debug"
        result = self.request(url, "DEBUG", None)
        self.restore_headers()
        return result

    def put(self, url, content_type="text/plain"):
        """Wrapper for put requests

        :param url: Target url
        :type url: `str`
        :param content_type: Content Type
        :type content_type: `str`
        :return:
        :rtype:
        """
        self.backup_headers()
        self.headers["Content-Type"] = content_type
        self.headers["Content-Length"] = "0"
        result = self.request(url, "PUT", None)
        self.restore_headers()
        return result

    def backup_headers(self):
        """Backup headers

        :return: None
        :rtype: None
        """
        self.headers_backup = dict.copy(self.headers)

    def restore_headers(self):
        """Restore headers

        :return: None
        :rtype: None
        """
        self.headers = dict.copy(self.headers_backup)

    def get_transaction(self, use_cache, url, method=None, data=None):
        """Get transaction from request, response

        :param use_cache: Cache usage
        :type use_cache: `bool`
        :param url: Request URL
        :type url: `str`
        :param method: Request method
        :type method: `str`
        :param data: Request data
        :type data: `str`
        :return:
        :rtype:
        """
        criteria = {"url": url.strip()}
        if method is not None:
            criteria["method"] = method
        # Must clean-up data to ensure match is found.
        if data is not None:
            criteria["data"] = self.get_post_to_str(data)
        # Visit URL if not already visited.
        if not use_cache or not is_transaction_already_added(self.session, criteria):
            if method in ["", "GET", "POST", "HEAD", "TRACE", "OPTIONS"]:
                return self.request(url, method, data)
            elif method == "DEBUG":
                return self.debug(url)
            elif method == "PUT":
                return self.put(url, data)
        else:  # Retrieve from DB = faster.
            # Important since there is no transaction ID with transactions objects created by Requester.
            return get_first(self.session, criteria)

    def get_transactions(self, use_cache, url_list, method=None, data=None, unique=True):
        """Get transaction from request, response

        :param use_cache: Cache usage
        :type use_cache: `bool`
        :param url_list: List of request URLs
        :type url_list: `list`
        :param method: Request method
        :type method: `str`
        :param data: Request data
        :type data: `str`
        :param unique: Unique or not
        :type unique: `bool`
        :return: List of transactions
        :rtype: `list`
        """
        transactions = []
        if unique:
            url_list = set(url_list)
        for url in url_list:
            url = url.strip()  # Clean up the URL first.
            if not url:
                continue  # Skip blank lines.
            if not is_url(url):
                logging.info("Minor issue: %s is not a valid URL and has been ignored, processing continues", url)
                continue  # Skip garbage URLs.
            transaction = self.get_transaction(use_cache, url, method=method, data=data)
            if transaction is not None:
                transactions.append(transaction)
        return transactions


requester = Requester(proxy=[INBOUND_PROXY_IP, INBOUND_PROXY_PORT])
