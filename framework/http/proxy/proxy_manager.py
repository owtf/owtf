#!/usr/bin/env python
'''
owtf is an OWASP+PTES-focused try to unite great tools and facilitate pen testing
Copyright (c) 2011, Abraham Aranguren <name.surname@gmail.com> Twitter: @7a_ http://7-a.org
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.
    * Neither the name of the copyright owner nor the
      names of its contributors may be used to endorse or promote products
      derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


Proxy Manager developed by Marios Kourtesis <name.surname@gmail.com>

Description:
This module provides functions for proxy managment.
'''
import tornado.curl_httpclient
from tornado.httpclient import HTTPRequest
import os
from tornado.ioloop import IOLoop
from tornado import gen



class Proxy_manager():

    testing_url = "http://google.com"  # with this url is tested the proxy
    testing_url_patern = "<title>Google</title>"

    def __init__(self):
        self.testing_url = "http://google.com"
        self.proxies = []
        self.number_of_proxies = 0
        self.proxy_pointer = 0
        #self.requests = 1  #default 1 requests per proxy
        #self.request_counter = 0
        self.number_of_responses = 0

    def load_proxy_list(self, proxylist_path):
        file_handle = open(os.path.expanduser(proxylist_path), "r")
        proxies = []
        file_buf = file_handle.read()
        lines = file_buf.split("\n")
        for line in lines:
            if str(line).strip() != "":
                proxies.append(line.split(":"))
        print "ProxyList loaded"
        return proxies

    def get_next_available_proxy(self):  #  returns the next proxy 
        if self.proxy_pointer == (self.number_of_proxies - 1):
            self.proxy_pointer = 0
        else:
            self.proxy_pointer = self.proxy_pointer + 1
        proxy = self.proxies[self.proxy_pointer]
        return {"proxy": proxy, "index": self.proxy_pointer}

    def remove_current_proxy(self, index):
        del self.proxies[index]
        self.number_of_proxies -= 1



class Proxy_Checker():  # This class is responsible for proxy checking
    Proxies = []
    number_of_responces = 0
    working_proxies = 0

    @staticmethod
    def check_proxies(q, proxies):  # check's a list of proxies asynchronous
        #proxies = Proxy_Checker.load_proxy_list(proxylist_path)
        Proxy_Checker.number_of_responses = 0
        Proxy_Checker.number_of_unchecked_proxies = len(proxies)

        for i in range(0, Proxy_Checker.number_of_unchecked_proxies):
            IOLoop.instance().add_callback(Proxy_Checker.handle_proxy_status, proxies[i], i)
        IOLoop.instance().start()
        q.put(Proxy_Checker.Proxies)

    @staticmethod
    @gen.engine
    def handle_proxy_status(proxy, i):
        #callback function
        #Is called by check_proxies

        request = HTTPRequest(url=Proxy_manager.testing_url,
                          proxy_host=proxy[0],
                          proxy_port=int(proxy[1]),
                          validate_cert=False
                          )
        http_client = tornado.curl_httpclient.CurlAsyncHTTPClient()
        response = yield gen.Task(http_client.fetch, request)
        if response.code == 200 and response.body.find(Proxy_manager.testing_url_patern) != -1: #if proxy is good
            Proxy_Checker.Proxies.append(proxy)
            Proxy_Checker.working_proxies += 1

        Proxy_Checker.number_of_responses += 1
        #
        print "Checking [ " + str(Proxy_Checker.number_of_responses)+"/"+\
        str(Proxy_Checker.number_of_unchecked_proxies)+" ] Working Proxies: [ "+\
        str(Proxy_Checker.working_proxies)+" ]"
        #if all proxies has been checked stop IOLoop
        if Proxy_Checker.number_of_responses == Proxy_Checker.number_of_unchecked_proxies:
            IOLoop.instance().stop()
            print "Proxy Check: Done"
