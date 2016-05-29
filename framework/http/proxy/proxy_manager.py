#!/usr/bin/env python
'''
Proxy Manager developed by Marios Kourtesis <name.surname@gmail.com>

Description:
This module provides functions for proxy managment.
'''
import tornado.curl_httpclient
from tornado.httpclient import HTTPRequest
import os
from tornado.ioloop import IOLoop
from tornado import gen
from framework.dependency_management.dependency_resolver import BaseComponent
import logging


class Proxy_manager(BaseComponent):

    COMPONENT_NAME = "proxy_manager"

    testing_url = "http://google.com"  # with this url is tested the proxy
    testing_url_patern = "<title>Google</title>"

    def __init__(self):
        self.register_in_service_locator()
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
        logging.info("ProxyList loaded")
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
    number_of_responses = 0
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
        if response.code == 200 and response.body.find(Proxy_manager.testing_url_patern) != -1:  # if proxy is alive
            Proxy_Checker.Proxies.append(proxy)
            Proxy_Checker.working_proxies += 1

        Proxy_Checker.number_of_responses += 1
        #
        logging.info("Checking [ " + str(Proxy_Checker.number_of_responses)+"/"+\
        str(Proxy_Checker.number_of_unchecked_proxies)+" ] Working Proxies: [ "+\
        str(Proxy_Checker.working_proxies)+" ]")
        # if all proxies has been checked stop IOLoop
        if Proxy_Checker.number_of_responses == Proxy_Checker.number_of_unchecked_proxies:
            IOLoop.instance().stop()
            logging.info("Proxy Check: Done")
