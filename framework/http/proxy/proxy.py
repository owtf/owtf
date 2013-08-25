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
import socket
import ssl
import os
from multiprocessing import Process
from socket_wrapper import wrap_socket
from cache_handler import CacheHandler

class ProxyHandler(tornado.web.RequestHandler):
    """
    This RequestHandler processes all the requests that the application received
    """
    SUPPORTED_METHODS = ['GET', 'POST', 'CONNECT', 'HEAD', 'PUT', 'DELETE', 'OPTIONS']

    def set_status(self, status_code, reason=None):
        """Sets the status code for our response.
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

    @tornado.web.asynchronous
    def get(self):
        """
        * This function handles all requests except the connect request.
        * Once ssl stream is formed between browser and proxy, the requests are
          then processed by this function
        """
        self.request.response_buffer = ''
        # Data for handling headers through a streaming callback
        # Need to work around for something
        restricted_response_headers = ['Content-Length',
                            'Content-Encoding',
                            'Etag',
                            'Transfer-Encoding',
                            'Connection',
                            'Vary',
                            'Accept-Ranges',
                            'Pragma']

        # This function is a callback after the async client gets the full response
        # This method will be improvised with more headers from original responses
        def handle_response(response):
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
            
        def handle_cached_response(response):
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
        def handle_data_chunk(data):
            if data:
                self.write(data)
                self.request.response_buffer += data

        # More headers are to be removed
        for header in ('Connection', 'Pragma', 'Cache-Control', 'If-Modified-Since'):
            try:
                del self.request.headers[header]
            except:
                continue

        # The requests that come through ssl streams are relative requests, so transparent
        # proxying is required. The following snippet decides the url that should be passed
        # to the async client
        if self.request.host in self.request.uri.split('/'):  # Normal Proxy Request
            self.request.url = self.request.uri
        else:  # Transparent Proxy Request
            self.request.url = self.request.protocol + "://" + self.request.host + self.request.uri

        # This block here checks for already cached response and if present returns one
        self.cache_handler = CacheHandler(
                                            self.application.cache_dir,
                                            self.request,
                                            self.application.cookie_regex,
                                            self.application.cookie_blacklist
                                         )
        cached_response = self.cache_handler.load()
        
        if cached_response:
            handle_cached_response(cached_response)
        else:
            # httprequest object is created and then passed to async client with a callback
            # pycurl is needed for curl client
            async_client = tornado.curl_httpclient.CurlAsyncHTTPClient()
            request = tornado.httpclient.HTTPRequest(
                    url=self.request.url,
                    method=self.request.method,
                    body=self.request.body,
                    headers=self.request.headers,
                    follow_redirects=False,
                    use_gzip=True,
                    streaming_callback=handle_data_chunk,
                    header_callback=None,
                    proxy_host=self.application.outbound_ip,
                    proxy_port=self.application.outbound_port,
                    proxy_username=self.application.outbound_username,
                    proxy_password=self.application.outbound_password,
                    allow_nonstandard_methods=True,
                    validate_cert=False)

            try:
                async_client.fetch(request, callback=handle_response)
            except Exception:
                pass

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
    """
    @tornado.web.asynchronous
    def get(self, ext):
        base_url = self.request.protocol + "://" + self.request.host + "/proxy"
        if ext == "":
            manifest_url = base_url + ".json"
            html = """
<html>
<head>
<title>OWASP OWTF PnH</title>
</head>
<body>
<h1> OWASP OWTF Simple browser configuration </h1>
<p>
The purpose of OWASP OWTF is to automate the manual, uncreative part of pen testing: For example, spending time trying to remember how to call "tool X", parsing results of "tool X" manually to feed "tool Y", etc.
</p>
<button id="btn">Click to Setup! :P</button>
<script>
  var manifest = {"detail":{"url":"http://127.0.0.1:8008/proxy.json"}};

  var click = function(event) {
    var evt = new CustomEvent('ConfigureSecTool', manifest);
    document.dispatchEvent(evt);
    setTimeout(function() {
      if (!detected) {
        console.log('No response');
     }
    },1000);
  };

  var started = function(event) {
    console.log('configuration has started');
  };
  // event listener for configuration failed event
  // use this to let the user know something has gone wrong
  var failed = function(event) {
    console.log('configuration has failed');
  };
  // event listener for configuration succeeded
  // use this to show a success message to a user in your welcome doc
  var succeeded = function(event) {
    console.log('configuration has succeeded');
  };
  // event listener for browser support activated
  var activated = function(event) {
    console.log('activation has occurred');
  };
  // Hook configuration event listeners into the document
  var btn = document.getElementById('btn');
  btn.addEventListener('click',click,false);
  document.addEventListener('ConfigureSecProxyStarted',started,false);
  document.addEventListener('ConfigureSecProxyFailed',failed,false);
  document.addEventListener('ConfigureSecProxyActivated',activated,false);
  document.addEventListener('ConfigureSecProxySucceeded',succeeded,false);

</script>
</body>
</html>
"""
            self.write(html)
        elif ext == ".json":
            manifest =  {
                          "toolName":"OWASP OWTF",
                          "protocolVersion":"0.2",
                          "features":{
                            "proxy":{
                              "PAC":base_url + ".pac",
                              "CACert":base_url + ".crt"
                            },
                            "commands":{
                              "prefix":"owtf",
                              "manifest":base_url + "-service.json"
                            }
                          }
                        }
            self.write(manifest)
            self.set_header("Content-Type", "application/json")
        elif ext == "-service.json":
            commands =  {
                          "commands":[{
                            "description":"OWASP OWTF Commands"
                          }
                          ]
                        }
            self.write(commands)
            self.set_header("Content-Type", "application/json")
        elif ext == ".pac":
            self.write("function FindProxyForURL(url,host) {return \"PROXY "+self.application.inbound_ip+":"+str(self.application.inbound_port)+"\"; }")
            self.set_header('Content-Type','text/plain')
        elif ext == ".crt":
            self.write(open(self.application.ca_cert, 'r').read())
            self.set_header('Content-Type','application/pkix-cert')
        self.finish()

class ProxyProcess(Process):

    def __init__(self, instances, inbound_options, cache_dir, ssl_options, cookie_filter, outbound_options=[], outbound_auth=""):
        Process.__init__(self)
        self.application = tornado.web.Application(handlers=[
                                                            (r'/proxy(.*)', PnHandler),
                                                            (r".*", ProxyHandler)
                                                            ], debug=False, gzip=True)
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
        
    # "0" equals the number of cores present in a machine
    def run(self):
        try:
            self.server.bind(self.application.inbound_port, address=self.application.inbound_ip)
            # Useful for using custom loggers because of relative paths in secure requests
            # http://www.joet3ch.com/blog/2011/09/08/alternative-tornado-logging/
            #tornado.options.parse_command_line(args=["dummy_arg","--log_file_prefix=/tmp/fix.log","--logging=info"])
            # To run any number of instances
            self.server.start(int(self.instances))
            tornado.ioloop.IOLoop.instance().start()
        except:
            # Cleanup code
            pass
