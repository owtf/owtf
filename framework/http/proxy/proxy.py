#!/usr/bin/env python
'''
owtf is an OWASP+PTES-focused try to unite great tools & facilitate pentesting
Copyright (c) 2013, Abraham Aranguren <name.surname@gmail.com>  http://7-a.org
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
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# Inbound Proxy Module developed by Bharadwaj Machiraju (blog.tunnelshade.in)
#                     as a part of Google Summer of Code 2013
'''
import tornado.httpserver
import tornado.ioloop
import tornado.iostream
import tornado.web
import tornado.curl_httpclient
import tornado.escape
import tornado.httputil
import tornado.options
import tornado.template
import socket
import ssl
import os
import datetime
from multiprocessing import Process
from socket_wrapper import wrap_socket
from cache_handler import CacheHandler


class ProxyHandler(tornado.web.RequestHandler):
    """
    This RequestHandler processes all the requests that the application received
    """
    SUPPORTED_METHODS = ['GET', 'POST', 'CONNECT', 'HEAD', 'PUT', 'DELETE', 'OPTIONS', 'TRACE']

    # Data for handling headers through a streaming callback
    # Need to work around for something
    global restricted_response_headers
    restricted_response_headers = [
                                    'Content-Length',
                                    'Content-Encoding',
                                    'Etag',
                                    'Transfer-Encoding',
                                    'Connection',
                                    'Vary',
                                    'Accept-Ranges',
                                    'Pragma'
                                   ]
    global restricted_request_headers
    restricted_request_headers = ['Connection', 'Pragma', 'Cache-Control', 'If-Modified-Since']

    def set_status(self, status_code, reason=None):
        """
        Sets the status code for our response.
        Overriding is done so as to handle unknown
        response codes gracefully.
        """
        self._status_code = status_code
        if reason is not None:
            self._reason = tornado.escape.native_str(reason)
        else:
            try:
                self._reason = tornado.httputil.responses[status_code]
            except KeyError:
                self._reason = tornado.escape.native_str("Server Not Found")

    def calculate_delay(self, response):
        self.application.throttle_variables["hosts"][self.request.host]["request_times"].append(response.request_time)

        if len(self.application.throttle_variables["hosts"][self.request.host]) > 20:
            self.application.throttle_variables["hosts"][self.request.host]["request_times"].pop(0)
            response_times = self.application.throttle_variables["hosts"][self.request.host]["request_times"]
            last_ten = sum(response_times[:int(len(response_times)/2)])/int(len(response_times)/2)
            second_last_ten = sum(response_times[int(len(response_times)/2):])/(len(response_times)-int(len(response_times)/2))
            if round(last_ten - second_last_ten, 3) > self.application.throttle_variables["threshold"]:
                self.application.throttle_variables["hosts"][self.request.host]["delay"] = round(last_ten - second_last_ten, 3)
            else:
                self.application.throttle_variables["hosts"][self.request.host]["delay"] = 0

    # This function is a callback after the async client gets the full response
    # This method will be improvised with more headers from original responses
    def handle_response(self, response):
        if self.application.throttle_variables:
            self.calculate_delay(response)
        if response.code in [408, 599, 404]:
            try:
                old_count = self.request.retries
                self.request.retries = old_count + 1
            except AttributeError:
                self.request.retries = 1
            finally:
                if self.request.retries < 3:
                    self.request.response_buffer = ''
                    self.clear()
                    self.process_request()
                else:
                    self.write_response(response)
        else:
            self.write_response(response)

    # This function writes a new response & caches it
    def write_response(self, response):
        self.set_status(response.code)
        del self._headers['Server']
        for header, value in list(response.headers.items()):
            if header == "Set-Cookie":
                self.add_header(header, value)
            else:
                if header not in restricted_response_headers:
                    self.set_header(header, value)
        if self.request.response_buffer:
            self.cache_handler.dump(response)
        self.finish()

    # This function handles a dummy response object which is created from cache
    def write_cached_response(self, response):
        self.set_status(response.code)
        for header, value in list(response.headers.items()):
            if header == "Set-Cookie":
                self.add_header(header, value)
            else:
                if header not in restricted_response_headers:
                    self.set_header(header, value)
        self.write(response.body)
        self.finish()

    # This function is a callback when a small chunk is received
    def handle_data_chunk(self, data):
        if data:
            self.write(data)
            self.request.response_buffer += data

    # This function creates and makes the request to upstream server
    def process_request(self):
        if self.cached_response:
            self.write_cached_response(self.cached_response)
        else:
            # pycurl is needed for curl client
            async_client = tornado.curl_httpclient.CurlAsyncHTTPClient()
            # httprequest object is created and then passed to async client with a callback
            request = tornado.httpclient.HTTPRequest(
                    url=self.request.url,
                    method=self.request.method,
                    body=self.request.body,
                    headers=self.request.headers,
                    follow_redirects=False,
                    use_gzip=True,
                    streaming_callback=self.handle_data_chunk,
                    header_callback=None,
                    proxy_host=self.application.outbound_ip,
                    proxy_port=self.application.outbound_port,
                    proxy_username=self.application.outbound_username,
                    proxy_password=self.application.outbound_password,
                    allow_nonstandard_methods=True,
                    validate_cert=False)

            try:
                async_client.fetch(request, callback=self.handle_response)
            except Exception:
                pass

    def cache_check(self):
        # This block here checks for already cached response and if present returns one
        self.cache_handler = CacheHandler(
                                            self.application.cache_dir,
                                            self.request,
                                            self.application.cookie_regex,
                                            self.application.cookie_blacklist
                                          )
        self.cached_response = self.cache_handler.load()
        self.process_request()

    @tornado.web.asynchronous
    def get(self):
        """
        * This function handles all requests except the connect request.
        * Once ssl stream is formed between browser and proxy, the requests are
          then processed by this function
        """
        # The flow starts here 
        self.request.response_buffer = ''
        # Request header cleaning
        for header in restricted_request_headers:
            try:
                del self.request.headers[header]
            except:
                continue

        # The requests that come through ssl streams are relative requests, so transparent
        # proxying is required. The following snippet decides the url that should be passed
        # to the async client
        if self.request.uri.startswith(self.request.protocol,0): # Normal Proxy Request
            self.request.url = self.request.uri
        else:  # Transparent Proxy Request
            self.request.url = self.request.protocol + "://" + self.request.host + self.request.uri

        if self.application.throttle_variables:
            try:
                throttle_delay = self.application.throttle_variables["hosts"][self.request.host]["delay"]
            except KeyError:
                self.application.throttle_variables["hosts"][self.request.host] = {"request_times":[], "delay":0}
                throttle_delay = 0
            finally:
                if throttle_delay == 0:
                    self.cache_check()
                else:
                    tornado.ioloop.IOLoop.instance().add_timeout(datetime.timedelta(seconds=throttle_delay), self.cache_check)
        else:
            self.cache_check()

    # The following 5 methods can be handled through the above implementation
    @tornado.web.asynchronous
    def post(self):
        return self.get()

    @tornado.web.asynchronous
    def head(self):
        return self.get()

    @tornado.web.asynchronous
    def put(self):
        return self.get()

    @tornado.web.asynchronous
    def delete(self):
        return self.get()

    @tornado.web.asynchronous
    def options(self):
        return self.get()

    @tornado.web.asynchronous
    def trace(self):
        return self.get()

    @tornado.web.asynchronous
    def connect(self):
        """
        This function gets called when a connect request is received.
        * The host and port are obtained from the request uri
        * A socket is created, wrapped in ssl and then added to SSLIOStream
        * This stream is used to connect to speak to the remote host on given port
        * If the server speaks ssl on that port, callback start_tunnel is called
        * An OK response is written back to client
        * The client side socket is wrapped in ssl
        * If the wrapping is successful, a new SSLIOStream is made using that socket
        * The stream is added back to the server for monitoring
        """
        host, port = self.request.uri.split(':')
        def start_tunnel():
            try:
                self.request.connection.stream.write(b"HTTP/1.1 200 Connection established\r\n\r\n")
                wrap_socket(
                            self.request.connection.stream.socket,
                            host,
                            self.application.ca_cert,
                            self.application.ca_key,
                            self.application.certs_folder,
                            success=ssl_success
                           )
            except tornado.iostream.StreamClosedError:
                pass

        def ssl_success(client_socket):
            client = tornado.iostream.SSLIOStream(client_socket)
            server.handle_stream(client, self.application.inbound_ip)

        # Tiny Hack to satisfy proxychains CONNECT request to HTTP port.
        # HTTPS fail check has to be improvised
        #def ssl_fail():
        #    self.request.connection.stream.write(b"HTTP/1.1 200 Connection established\r\n\r\n")
        #    server.handle_stream(self.request.connection.stream, self.application.inbound_ip)
        
        # Hacking to be done here, so as to check for ssl using proxy and auth    
        try:
            s = ssl.wrap_socket(socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0))
            upstream = tornado.iostream.SSLIOStream(s)
            #start_tunnel()
            #upstream.set_close_callback(ssl_fail)
            upstream.connect((host, int(port)), start_tunnel)
        except Exception:
            self.finish()

class PlugnHackHandler(tornado.web.RequestHandler):
    """
    This handles the requests which are used for firefox configuration 
    https://blog.mozilla.org/security/2013/08/22/plug-n-hack/
    """
    @tornado.web.asynchronous
    def get(self, ext):
        """
        Root URL (in default case) = http://127.0.0.1:8008/proxy
        Templates folder is framework/http/proxy/templates
        For PnH, following files (all stored as templates) are used :-
        
        File Name       ( Relative path )
        =========       =================
        * Provider file ( /proxy )
        * Tool Manifest ( /proxy.json )
        * Commands      ( /proxy-service.json )
        * PAC file      ( /proxy.pac )
        * CA Cert       ( /proxy.crt )
        """
        # Rebuilding the root url
        root_url = self.request.protocol + "://" + self.request.host
        proxy_url = root_url + "/proxy"
        # Absolute path of templates folder using location of this script (proxy.py)
        templates_folder = os.path.join(os.path.dirname(os.path.realpath(__file__)), "templates")
        loader = tornado.template.Loader(templates_folder) # This loads all the templates in the folder
        if ext == "":
            manifest_url = proxy_url + ".json"
            self.write(loader.load("welcome.html").generate(manifest_url=manifest_url))
        elif ext == ".json":
            self.write(loader.load("manifest.json").generate(proxy_url=proxy_url))
            self.set_header("Content-Type", "application/json")
        elif ext == "-service.json":
            self.write(loader.load("service.json").generate(root_url=root_url))
            self.set_header("Content-Type", "application/json")
        elif ext == ".pac":
            self.write(loader.load("proxy.pac").generate(proxy_details=self.request.host))
            self.set_header('Content-Type','text/plain')
        elif ext == ".crt":
            self.write(open(self.application.ca_cert, 'r').read())
            self.set_header('Content-Type','application/pkix-cert')
        self.finish()

class CommandHandler(tornado.web.RequestHandler):
    """
    This handles the python function calls issued with relative url "/JSON/?cmd="
    Responses are in JSON
    """
    @tornado.web.asynchronous
    def get(self, relative_url):
        # Currently only get requests are sufficient for providing PnH service commands
        command_list = self.get_arguments("cmd")
        info = {}
        for command in command_list:
            command = "self.application." + command
            info[command] = eval(command)
        self.write(info)
        self.finish()
                        
class ProxyProcess(Process):

    def __init__(self, core, instances, inbound_options, cache_dir, ssl_options, cookie_filter, outbound_options=[], outbound_auth=""):
        Process.__init__(self)
        self.application = tornado.web.Application(handlers=[
                                                            (r'/proxy(.*)', PlugnHackHandler),
                                                            (r'/JSON/(.*)', CommandHandler),
                                                            (r'.*', ProxyHandler)
                                                            ], 
                                                    debug=False,
                                                    gzip=True,
                                                   )
        self.application.inbound_ip = inbound_options[0]
        self.application.inbound_port = int(inbound_options[1])
        self.application.cache_dir = cache_dir
        self.application.ca_cert = ssl_options['CA_CERT']
        self.application.ca_key = ssl_options['CA_KEY']
        self.application.proxy_folder = os.path.dirname(ssl_options['CA_CERT'])
        self.application.certs_folder = ssl_options['CERTS_FOLDER']
        self.application.cookie_blacklist = cookie_filter['BLACKLIST']
        self.application.cookie_regex = cookie_filter['REGEX']
        if outbound_options:
            self.application.outbound_ip = outbound_options[0]
            self.application.outbound_port = int(outbound_options[1])
        else:
            self.application.outbound_ip, self.application.outbound_port = None, None
        if outbound_auth:
            self.application.outbound_username, self.application.outbound_password = outbound_auth.split(":")
        else:
            self.application.outbound_username, self.application.outbound_password = None, None
        global server
        server = tornado.httpserver.HTTPServer(self.application)
        self.server = server
        self.instances = instances
        self.application.Core = core
        if self.application.Core.Config.Get("PROXY_THROTTLING") == 'false':
            self.application.throttle_variables = None
        else:
            self.application.throttle_variables = {
                                                    "hosts": {},
                                                    "threshold": self.application.Core.Config.Get("THROTTLING_THRESHOLD"),
                                                  }

    # "0" equals the number of cores present in a machine
    def run(self):
        try:
            self.server.bind(self.application.inbound_port, address=self.application.inbound_ip)
            # Useful for using custom loggers because of relative paths in secure requests
            # http://www.joet3ch.com/blog/2011/09/08/alternative-tornado-logging/
            tornado.options.parse_command_line(args=["dummy_arg","--log_file_prefix=/tmp/owtf-proxy.log","--logging=info"])
            # To run any number of instances
            self.server.start(int(self.instances))
            tornado.ioloop.IOLoop.instance().start()
        except:
            # Cleanup code
            pass
