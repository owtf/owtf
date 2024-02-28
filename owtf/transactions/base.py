"""
owtf.transactions.base
~~~~~~~~~~~~~~~~~~~~~~
HTTP_Transaction is a container of useful HTTP Transaction information to
simplify code both in the framework and the plugins.
"""
import gzip
import io
import logging
import zlib

try:
    from http.client import responses as response_messages
except ImportError:
    from httplib import responses as response_messages

from owtf.utils.http import derive_http_method

__all__ = ["HTTPTransaction"]


class HTTPTransaction(object):

    def __init__(self, timer):
        self.timer = timer
        self.new = False

    @property
    def in_scope(self):
        """Check if the transaction is in scope

        :return: True if in scope, else False
        :rtype: `bool`
        """
        return self.is_in_scope

    def start(self, url, data, method, is_in_scope):
        """Get attributes for a new transaction

        :param url: transaction url
        :type url: `str`
        :param data: transaction data
        :type data:
        :param method:
        :type method:
        :param is_in_scope:
        :type is_in_scope:
        :return:
        :rtype:
        """
        self.is_in_scope = is_in_scope
        self.timer.start_timer("Request")
        self.time = self.time_human = ""
        self.url = url
        self.data = data if data is not None else ""
        self.method = derive_http_method(method, data)
        self.found = None
        self.raw_request = ""
        self.response_headers = []
        self.response_size = ""
        self.status = ""
        self.id = ""
        self.html_link_id = ""
        self.new = True  # Flag new transaction.

    def end_request(self):
        """End timer for the request

        :return: None
        :rtype: None
        """
        self.time = self.timer.get_elapsed_time_as_str("Request")
        self.time_human = self.time
        self.local_timestamp = self.timer.get_current_date_time()

    def set_transaction(self, found, request, response):
        """Response can be "Response" for 200 OK or "Error" for everything else, we don't care here.

        :param found:
        :type found:
        :param request:
        :type request:
        :param response:
        :type response:
        :return:
        :rtype:
        """
        if self.url != response.url:
            if response.code not in [302, 301]:  # No way, error in hook.
                # Mark as a redirect, dirty but more accurate than 200 :P
                self.status = "302 Found"
                self.status += " --Redirect--> {!s} ".format(response.code)
                self.status += response.msg
            # Redirect differs in schema (i.e. https instead of http).
            if self.url.split(":")[0] != response.url.split(":")[0]:
                pass
            self.url = response.url
        else:
            self.status = "{!s} {!s}".format(str(response.code), response.msg)
        self.raw_request = request
        self.found = found
        self.response_headers = response.headers
        self.response_contents = response.read()
        self.check_if_compressed(response, self.response_contents)
        self.end_request()

    def set_transaction_from_db(
        self,
        id,
        url,
        method,
        status,
        time,
        time_human,
        local_timestamp,
        request_data,
        raw_request,
        response_headers,
        response_size,
        response_body,
    ):
        """Set the transaction from the DB

        :param id:
        :type id:
        :param url:
        :type url:
        :param method:
        :type method:
        :param status:
        :type status:
        :param time:
        :type time:
        :param time_human:
        :type time_human:
        :param local_timestamp:
        :type local_timestamp:
        :param request_data:
        :type request_data:
        :param raw_request:
        :type raw_request:
        :param response_headers:
        :type response_headers:
        :param response_size:
        :type response_size:
        :param response_body:
        :type response_body:
        :return:
        :rtype:
        """
        self.id = id
        self.new = False  # Flag NOT new transaction.
        self.url = url
        self.method = method
        self.status = status
        self.found = (self.status == "200 OK")
        self.time = time
        self.time_human = time_human
        self.local_timestamp = local_timestamp
        self.data = request_data
        self.raw_request = raw_request
        self.response_headers = response_headers
        self.response_size = response_size
        self.response_contents = response_body

    def get_session_tokens(self):
        """Get a JSON blob of all captured cookies

        :return:
        :rtype:
        """
        cookies = []
        try:  # parsing may sometimes fail
            for cookie in self.cookies_list:
                cookies.append({'name':cookie.split('=')[0],'value':cookie.split('=')[1]})
        except:
            logging.debug("Cannot not parse the cookies")
        return cookies

    def set_error(self, error_message):
        """Set the error message for a transaction

        :param error_message: Message to set
        :type error_message: `str`
        :return: None
        :rtype: None
        """
        # Only called for unknown errors, 404 and other HTTP stuff handled on self.SetResponse.
        self.response_contents = error_message
        self.end_request()

    @property
    def get_id(self):
        """Get transaction ID

        :return: transaction id
        :rtype: `int`
        """
        return self.id

    def set_id(self, id, html_link_to_id):
        """Sets the transaction id and format an HTML link

        :param id: transaction id
        :type id: `int`
        :param html_link_to_id: HTML link for the id
        :type html_link_to_id: `str`
        :return: None
        :rtype: None
        """
        self.id = id
        self.html_link_id = html_link_to_id
        # Only for new transactions, not when retrieved from DB, etc.
        if self.new:
            logging.info(
                "New OWTF HTTP Transaction: %s",
                " - ".join([self.id, self.time_human, self.status, self.method, self.url]),
            )

    def get_html_link(self, link_name=""):
        """Get the HTML link to the transaction ID

        :param link_name: Name of the link
        :type link_name: `str`
        :return: Formatted HTML link
        :rtype: `str`
        """
        if "" == link_name:
            link_name = "Transaction {}".format(self.id)
        return self.html_link_id.replace("@@@PLACE_HOLDER@@@", link_name)

    def get_raw(self):
        """Get raw transaction request and response

        :return: Raw string with response and request
        :rtype: `str`
        """
        return "{}\n\n{}".format(self.get_raw_request, self.get_raw_response())

    @property
    def get_raw_request(self):
        """Return raw request

        :return: Raw request
        :rtype: `str`
        """
        return self.raw_request

    @property
    def get_status(self):
        """Get status for transaction response

        :return: Status
        :rtype: `str`
        """
        return self.status

    @property
    def get_response_headers(self):
        """Get response headers for the transaction

        :return:
        :rtype:
        """
        return self.response_headers

    def get_raw_response(self, with_status=True):
        """Get the complete raw response

        :param with_status: Want status?
        :type with_status: `bool`
        :return: Raw reponse
        :rtype: `str`
        """
        try:
            return "{}\r\n{}\n\n{}".format(self.get_status, str(self.response_headers), self.response_contents)
        except UnicodeDecodeError:
            return "{}\r\n{}\n\n[Binary Content]".format(self.get_status, str(self.response_headers))

    @property
    def get_raw_response_body(self):
        """Return raw response content

        :return: Raw response body
        :rtype: `str`
        """
        return self.response_contents

    def import_proxy_req_resp(self, request, response):
        """Import proxy request and response

        :param request:
        :type request:
        :param response:
        :type response:
        :return:
        :rtype:
        """
        self.is_in_scope = request.in_scope
        self.url = request.url
        self.data = request.body if request.body is not None else ""
        self.method = request.method
        try:
            self.status = "{!s} {!s}".format(str(response.code), response_messages[int(response.code)])
        except KeyError:
            self.status = "{!s} Unknown Error".format(response.code)
        self.raw_request = request.raw_request
        self.response_headers = response.header_string
        self.response_contents = response.body
        self.response_size = len(self.response_contents)
        self.time = str(response.request_time)
        self.time_human = self.timer.get_time_human(self.time)
        self.local_timestamp = request.local_timestamp
        self.found = (self.status == "200 OK")
        self.cookies_list = response.cookies
        self.new = True
        self.id = ""
        self.html_link_id = ""

    @property
    def get_decode_response(self):
        return self.decoded_content

    def check_if_compressed(self, response, content):
        if response.info().get("Content-Encoding", "") == "gzip":  # check for gzip compression
            compressed_file = io.StringIO()
            compressed_file.write(content)
            compressed_file.seek(0)
            f = gzip.GzipFile(fileobj=compressed_file, mode="rb")
            self.decoded_content = f.read()
            f.close()
        elif response.info().get("Content-Encoding") == "deflate":  # check for deflate compression
            self.decoded_content = zlib.decompress(content)
        else:
            self.decoded_content = content  # else the no compression
