from time import sleep
from tornado import ioloop
from tornado.httpclient import AsyncHTTPClient, HTTPClient, HTTPError
from framework.http.wafbypasser.core.http_helper import HTTPHelper


class Fuzzer:
    def __init__(self, http_helper):
        self.req_num = 0
        self.resp_num = 0
        self.responses = []
        self.http_helper = http_helper

    def reset(self):
        self.req_num = 0
        self.resp_num = 0
        self.responses = []

    def async_fuzz(self, requests):
        ''' This is the asynchronous fuzzing engine.'''
        self.reset()
        http_client = AsyncHTTPClient()
        self.req_num = len(requests)  # number of sending requests
        self.resp_num = 0  # this is used for counting the responses
        for request in requests:
            http_client.fetch(request, self.handle_response)
        # print "Status: Asynchronous Fuzzing Started"
        ioloop.IOLoop.instance().start()
        return self.responses

    def handle_response(self, response):
        '''This a callback function which handles the http responses.
        Is called by the fuzz function.'''
        self.resp_num += 1
        self.responses.append(response)
        if self.resp_num == self.req_num:  # if is the last response
            ioloop.IOLoop.instance().stop()

    def sync_fuzz(self, requests, delay=0, follow_cookies=True):
        ''' This is the synchronous fuzzing engine. Useful for fuzzing with
        delays and fuzzing that follows cookies'''
        self.reset()
        http_client = HTTPClient()
        cookie = None
        for request in requests:
            try:
                if follow_cookies and cookie:
                    request.headers = HTTPHelper.add_header_param(
                        request.header,
                        "Cookie",
                        cookie)
                response = http_client.fetch(request)
            except HTTPError as e:
                if e.response:
                    response = e.response
            self.responses.append(response)
            if follow_cookies:
                if "Set-Cookie" in response.headers:
                    cookie = response.headers["Set-Cookie"]
            if delay:
                sleep(delay)
        return self.responses