#!/usr/bin/env python
"""
HTTP_Transaction is a container of useful HTTP Transaction information to
simplify code both in the framework and the plugins.
"""

import cgi
import logging
import StringIO
import gzip
import zlib
from httplib import responses as response_messages
import json

from framework.lib.general import *
from cookies import Cookie


class HTTPTransaction(object):
    def __init__(self, timer):
        self.timer = timer
        self.new = False

    def str_scope(self):
        return str(self.is_in_scope)[0]

    def in_scope(self):
        return self.is_in_scope

    def start(self, url, data, method, is_in_scope):
        self.is_in_scope = is_in_scope
        self.start_request()
        self.url = url
        self.init_data(data)
        self.method = derive_http_method(method, data)
        self.found = None
        self.raw_request = ''
        self.response_headers = []
        self.response_size = ''
        self.status = ''
        self.id = ''
        self.link_to_id = ''
        self.new = True  # Flag new transaction.

    def init_data(self, data):
        self.data = data
        if self.data is None:
            # This simplifies other code later, no need to cast to str if None, etc.
            self.data = ''

    def start_request(self):
        self.timer.start_timer('Request')
        self.time = self.time_human = ''

    def end_request(self):
        self.time = self.timer.get_elapsed_time_as_str('Request')
        self.time_human = self.time
        self.local_timestamp = self.timer.get_current_date_time()

    def set_transaction(self, found, request, response):
        # Response can be "Response" for 200 OK or "Error" for everything else, we don't care here.
        if self.url != response.url:
            if response.code not in [302, 301]:  # No way, error in hook.
                # Mark as a redirect, dirty but more accurate than 200 :P
                self.status = "%s Found" % str(302)
                self.status += " --Redirect--> %s " % str(response.code)
                self.status += response.msg
            # Redirect differs in schema (i.e. https instead of http).
            if self.url.split(':')[0] != response.url.split(':')[0]:
                pass
            self.url = response.url
        else:
            self.status = "%s %s" % (str(response.code), response.msg)
        self.raw_request = request
        self.found = found
        self.response_headers = response.headers
        self.response_contents = response.read()
        # a new self.Decodedcontent is added if the received response is in compressed format
        self.check_compressed(response, self.response_contents)
        self.end_request()

    def set_transaction_from_db(self, id, url, method, status, time, time_human, local_timestamp, request_data,
                                raw_request, response_headers, response_size, response_body):
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
        cookies = []
        try:  # parsing may sometimes fail
            for cookie in self.cookies_list:
                cookies.append(Cookie.from_string(cookie).to_dict())
        except:
            pass
        return json.dumps(cookies)

    def set_error(self, error_message):
        # Only called for unknown errors, 404 and other HTTP stuff handled on self.SetResponse.
        self.response_contents = error_message
        self.end_request()

    def get_id(self):
        return (self.id)

    def set_id(self, id, html_link_to_id):
        self.id = id
        self.link_to_id = html_link_to_id
        # Only for new transactions, not when retrieved from DB, etc.
        if self.new:
            log = logging.getLogger('general')
            log.info("New owtf HTTP Transaction: %s",
                     " - ".join([self.id, self.time_human, self.status, self.method, self.url]))

    def get_html_link(self, link_name=''):
        if '' == link_name:
            link_name = "Transaction %s" % self.id
        return self.link_to_id.replace('@@@PLACE_HOLDER@@@', link_name)

    def get_link_with_time(self, link_name=''):
        return "%s (%s)" % (self.get_html_link(link_name), self.time_human)

    def get_raw_escaped(self):
        return "<pre>%s</pre>" % cgi.escape(self.get_raw())

    def get_raw(self):
        return "%s\n\n%s" % (self.get_raw_request(), self.get_raw_response())

    def get_raw_request(self):
        return self.raw_request

    def get_status(self):
        return self.status

    def get_response_headers(self):
        return self.response_headers

    def get_raw_response(self, with_status=True):
        try:
            return "%s\r\n%s\n\n%s" % (self.get_status(), str(self.response_headers), self.response_contents)
        except UnicodeDecodeError:
            return "%s\r\n%s\n\n[Binary Content]" % (self.get_status(), str(self.response_headers))

    def get_raw_response_headers(self, with_status=True):
        return "%s\r\n%s" % (self.get_status(), str(self.response_headers))

    def get_raw_response_body(self):
        return self.response_contents

    def import_proxy_req_response(self, request, response):
        self.is_in_scope = request.in_scope
        self.url = request.url
        self.init_data(request.body)
        self.method = request.method
        try:
            self.status = "%s %s" % (str(response.code), response_messages[int(response.code)])
        except KeyError:
            self.status = "%s Unknown Error" % str(response.code)
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
        self.id = ''
        self.link_to_id = ''

    def check_compressed(self, response, content):
        if response.info().get('Content-Encoding') == 'gzip':  # check for gzip compression
            compressed_file = StringIO.StringIO()
            compressed_file.write(content)
            compressed_file.seek(0)
            f = gzip.GzipFile(fileobj=compressed_file, mode='rb')
            self.decoded_content = f.read()
        elif response.info().get('Content-Encoding') == 'deflate':  # check for deflate compression
            self.decoded_content = zlib.decompress(content)
        else:
            self.decoded_content = content  # else the no compression
