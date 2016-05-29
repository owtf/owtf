import urlparse
from copy import copy
from time import time


class HTTPHelper:

    def __init__(self, init_request):
        # Links a payload with an http request. Needed for async fuzzing.
        # variable schema payload_table[id(request)] = payload
        self.payload_table = {}
        self.init_request = init_request

    def create_http_request(self, method, url, body=None, headers={},
                            payload=None):
        """This function creates an HTTP request with some additional
         initializations"""

        request = copy(self.init_request)
        request.method = method
        request.url = url
        request.headers = headers
        if body:
            request.body = body
            if headers and not "Content-Length" in request.headers:
                #request.headers["Content-Length"] = len(body)
                pass
            if method.upper() not in "POST":
                if "Content-Length" in headers:
                    headers.pop("Content-Length")

        request.start_time = time()
        if payload:
            self.payload_table[id(request)] = payload
        return request

    def get_payload_table(self):
        return self.payload_table

    def get_payload(self, response):
        try:
            return self.payload_table[id(response.request)]
        except KeyError:
            return "->Payload not Loaded from File"

    @staticmethod
    def add_url_param(url, param_name, param_value):
        if urlparse.urlparse(url)[4] == '':
            sep = "?"
        else:
            sep = '&'
        url += sep + param_name + "=" + param_value
        return url

    @staticmethod
    def add_body_param(body, param_name, param_value):
        if body is None or body == '':
            sep = ""
        else:
            sep = '&'
        body += sep + param_name + "=" + param_value
        return body

    @staticmethod
    def add_cookie_param(headers, param_name, param_value):
        new_headers = headers.copy()
        try:
            cookie_value = new_headers.pop('Cookie')
            sep = "&"
        except KeyError:
            cookie_value = ""
            sep = ""
        cookie_value += sep + param_name + "=" + param_value
        new_headers.add("Cookie", cookie_value)
        return new_headers

    @staticmethod
    def add_header_param(headers, param_name, param_value):
        new_headers = headers.copy()
        if param_name in new_headers:
            new_headers.pop(param_name)
        new_headers.add(param_name, param_value)
        return new_headers