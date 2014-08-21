import re
import urllib
import ast

from tornado.httputil import HTTPHeaders
from framework.http.wafbypasser.core.template_parser import TemplateParser


class PlaceholderManager:
    def __init__(self, fuzzing_signature):
        self.sig = fuzzing_signature
        self.lsig = self.sig + "length" + self.sig  # Length Signature
        self.fsig = self.sig + "fuzzhere" + self.sig  # fuzzing signature
        # template signature regular expression
        self.template_signature_re = self.sig
        self.template_signature_re += "[^" + self.sig + "]+" + self.sig

    def template_signature(self, string):
        ret = re.search(self.template_signature_re, string)
        if ret:
            return ret.group(0)
        return False

    @staticmethod
    def get_placeholder_number(template_signature_re, string):
        ret = re.compile(template_signature_re)
        if ret:
            return len(ret.findall(string))
        return 0

    def replace_url(self, url, payload):
        if self.fsig in url:
            return url.replace(self.fsig, urllib.quote_plus(payload))
        template_sig = self.template_signature(url)
        if template_sig:
            tp = TemplateParser()
            tp.set_payload(payload)
            new_payload = repr(
                tp.transform(self.template_signature(url),
                             self.sig))[1:-1]  # removing extra " "
            return url.replace(template_sig, new_payload)
        return url

    def replace_header(self, headers, payload):
        raw_headers = str(headers)
        if self.fsig in raw_headers:
            raw_headers = raw_headers.replace(self.fsig, payload)
            return HTTPHeaders(ast.literal_eval(raw_headers))
        template_sig = self.template_signature(raw_headers)
        if template_sig:
            tp = TemplateParser()
            tp.set_payload(payload)
            header_template = self.template_signature(raw_headers)
            new_payload = repr(
                tp.transform(header_template,
                             self.sig))[1:-1]  # removing extra " "
            raw_headers = raw_headers.replace(header_template, new_payload)
            new_headers = HTTPHeaders(ast.literal_eval(raw_headers))
            return new_headers
        return headers

    def replace_body(self, body, payload):
        if body is None:
            return body
        if self.fsig in body:
            return body.replace(self.fsig, urllib.quote_plus(payload))
        template_sig = self.template_signature(body)
        if template_sig:
            tp = TemplateParser()
            tp.set_payload(payload)
            new_payload = repr(
                tp.transform(self.template_signature(body),
                             self.sig))[1:-1]  # removing extra " "
            return body.replace(template_sig, new_payload)
        return body

    def transformed_http_requests(self, http_helper, methods, url, payloads,
                                  headers=None, body=None):
        """This constructs a list of HTTP transformed requests which contain
        the payloads"""
        requests = []
        for method in methods:
            for payload in payloads:
                new_url = self.replace_url(url, payload)
                new_headers = self.replace_header(headers, payload)
                new_body = self.replace_body(body, payload)
                request = http_helper.create_http_request(method,
                                                          new_url,
                                                          new_body,
                                                          new_headers,
                                                          payload)
                requests.append(request)
        return requests