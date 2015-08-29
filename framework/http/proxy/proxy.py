#!/usr/bin/env python
'''
# Inbound Proxy Module developed by Bharadwaj Machiraju (blog.tunnelshade.in)
#                     as a part of Google Summer of Code 2013
'''
import tornado.httpserver
import tornado.ioloop
import tornado.iostream
import tornado.web
import tornado.httpclient
import tornado.curl_httpclient
import tornado.escape
import tornado.httputil
import tornado.options
import tornado.template
import tornado.websocket
import tornado.gen
import socket
import ssl
import os
import datetime
import uuid
import re
from multiprocessing import Process, Value, Lock
from framework.dependency_management.dependency_resolver import BaseComponent, ComponentNotFoundException
from framework.utils import FileOperations
from socket_wrapper import wrap_socket
from cache_handler import CacheHandler
from framework.lib.owtf_process import OWTFProcess
import pycurl


def prepare_curl_callback(curl):
    curl.setopt(pycurl.PROXYTYPE, pycurl.PROXYTYPE_SOCKS5)


class ProxyHandler(tornado.web.RequestHandler):
    """
    This RequestHandler processes all the requests that the application received
    """
    SUPPORTED_METHODS = ['GET', 'POST', 'CONNECT', 'HEAD', 'PUT', 'DELETE', 'OPTIONS', 'TRACE']

    def __new__(cls, application, request, **kwargs):
        # http://stackoverflow.com/questions/3209233/how-to-replace-an-instance-in-init-with-a-different-object
        # Based on upgrade header, websocket request handler must be used
        try:
            if request.headers['Upgrade'].lower() == 'websocket':
                return CustomWebSocketHandler(application, request, **kwargs)
        except KeyError:
            pass
        return tornado.web.RequestHandler.__new__(cls, application, request, **kwargs)

    def set_default_headers(self):
        # This is automatically called by Tornado :P
        # XD Using this to remove "Server" header set by tornado
        del self._headers["Server"]

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

    def extract_session(self, response):
        """
        # Watches the response for `Set-Cookie` header and extracts session tokens from it
        """
        # this solution should work for both cases; single session cookies and multiple ones
        for header, value in list(response.headers.items()):
            if header == 'Set-Cookie':
                try:
                    tokens = value.split(',')
                except:
                    tokens = value
                return tokens

    # This function writes a new response & caches it
    def finish_response(self, response):
        self.set_status(response.code)
        for header, value in list(response.headers.items()):
            if header == "Set-Cookie":
                self.add_header(header, value)
            else:
                if header not in restricted_response_headers:
                    self.set_header(header, value)
        self.finish()

    # This function is a callback when a small chunk is received
    def handle_data_chunk(self, data):
        if data:
            self.write(data)
            self.request.response_buffer += data

    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        """
        * This function handles all requests except the connect request.
        * Once ssl stream is formed between browser and proxy, the requests are
          then processed by this function
        """
        # The flow starts here
        self.request.local_timestamp = datetime.datetime.now()
        self.request.response_buffer = ''

        # The requests that come through ssl streams are relative requests, so transparent
        # proxying is required. The following snippet decides the url that should be passed
        # to the async client
        if self.request.uri.startswith(self.request.protocol,0): # Normal Proxy Request
            self.request.url = self.request.uri
        else:  # Transparent Proxy Request
            self.request.url = self.request.protocol + "://" + self.request.host
            if self.request.uri != '/':  # Add uri only if needed
                self.request.url += self.request.uri

        # This block here checks for already cached response and if present returns one
        self.cache_handler = CacheHandler(
                                            self.application.cache_dir,
                                            self.request,
                                            self.application.cookie_regex,
                                            self.application.cookie_blacklist
                                          )
        request_hash = yield tornado.gen.Task(self.cache_handler.calculate_hash)
        self.cached_response = self.cache_handler.load()

        if self.cached_response:

            if self.cached_response.body:
                self.write(self.cached_response.body)
            self.finish_response(self.cached_response)

        else:

            # Request header cleaning
            for header in restricted_request_headers:
                try:
                    del self.request.headers[header]
                except:
                    continue

            # HTTP auth if exists
            http_auth_username = None
            http_auth_password = None
            http_auth_mode = None
            if self.application.http_auth:
                # HTTP AUTH settings
                host = self.request.host
                # If default ports are not provided, they are added
                try:
                    test = self.request.host.index(':')
                except ValueError:
                    default_ports = {'http':'80', 'https':'443'}
                    try:
                        host = self.request.host + ':' + default_ports[self.request.protocol]
                    except KeyError:
                        pass
                # Check if auth is provided for that host
                try:
                    index = self.application.http_auth_hosts.index(host)
                    http_auth_username = self.application.http_auth_usernames[index]
                    http_auth_password = self.application.http_auth_passwords[index]
                    http_auth_mode = self.application.http_auth_modes[index]
                except ValueError:
                    pass

            # pycurl is needed for curl client
            async_client = tornado.curl_httpclient.CurlAsyncHTTPClient()
            # httprequest object is created and then passed to async client with a callback
            success_response = False  # is used to check the response in the botnet mode

            while not success_response:
                #Proxy Switching (botnet_mode) code
                if self.application.proxy_manager:
                    proxy = self.application.proxy_manager.get_next_available_proxy()
                    #print proxy
                    self.application.outbound_ip = proxy["proxy"][0]
                    self.application.outbound_port = int(proxy["proxy"][1])

                #  httprequest object is created and then passed to async client with a callback
                request = tornado.httpclient.HTTPRequest(
                        url=self.request.url,
                        method=self.request.method,
                        body=self.request.body if self.request.body else None,
                        headers=self.request.headers,
                        auth_username=http_auth_username,
                        auth_password=http_auth_password,
                        auth_mode=http_auth_mode,
                        follow_redirects=False,
                        use_gzip=True,
                        streaming_callback=self.handle_data_chunk,
                        header_callback=None,
                        proxy_host=self.application.outbound_ip,
                        proxy_port=self.application.outbound_port,
                        proxy_username=self.application.outbound_username,
                        proxy_password=self.application.outbound_password,
                        allow_nonstandard_methods=True,
                        prepare_curl_callback=prepare_curl_callback if self.application.outbound_proxy_type == "socks"\
                                                                    else None, # socks callback function
                        validate_cert=False)
                try:
                    response = yield tornado.gen.Task(async_client.fetch, request)
                except Exception:
                    pass
                # Request retries
                for i in range(0, 3):
                    if response.code in [408, 599]:
                        self.request.response_buffer = ''
                        response = yield tornado.gen.Task(async_client.fetch, request)
                    else:
                        success_response = True
                        break

                #botnet mode code (proxy switching)
                #checking the status of the proxy (asynchronous)
                if self.application.proxy_manager and not success_response:
                    proxy_check_req = tornado.httpclient.HTTPRequest(
                    url=self.application.proxy_manager.testing_url, #testing url is google.com
                        use_gzip=True,
                        proxy_host=self.application.outbound_ip,
                        proxy_port=self.application.outbound_port,
                        proxy_username=self.application.outbound_username,
                        proxy_password=self.application.outbound_password,
                        prepare_curl_callback=prepare_curl_callback if self.application.outbound_proxy_type == "socks"\
                        else None, # socks callback function
                        validate_cert=False)
                    try:
                        proxy_check_resp = yield tornado.gen.Task(async_client.fetch, proxy_check_req)
                    except Exception:
                        pass

                    if proxy_check_resp.code != 200:
                        #self.application.proxy_manager.remove_proxy(proxy)
                        self.application.proxy_manager.remove_proxy(proxy["index"])
                    else:
                        success_response = True
                else:
                    success_response = True

            self.finish_response(response)
            # Cache the response after finishing the response, so caching time is not included in response time
            self.cache_handler.dump(response)

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
                            self.application.ca_key_pass,
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
        def ssl_fail():
            self.request.connection.stream.write(b"HTTP/1.1 200 Connection established\r\n\r\n")
            server.handle_stream(self.request.connection.stream, self.application.inbound_ip)

        # Hacking to be done here, so as to check for ssl using proxy and auth
        try:
            s = ssl.wrap_socket(socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0))
            upstream = tornado.iostream.SSLIOStream(s)
            #start_tunnel()
            upstream.set_close_callback(ssl_fail)
            upstream.connect((host, int(port)), start_tunnel)
        except Exception:
            self.finish()

class CustomWebSocketHandler(tornado.websocket.WebSocketHandler):
    """
    * See docs XD
    * This class is used for handling websocket traffic.
    * Object of this class replaces the main request handler for a request with
      header => "Upgrade: websocket"
    * wss:// - CONNECT request is handled by main handler
    """
    def upstream_connect(self, io_loop=None, callback=None):
        """
        Implemented as a custom alternative to tornado.websocket.websocket_connect
        """
        # io_loop is needed, how else will it work with tornado :P
        if io_loop is None:
            io_loop = tornado.ioloop.IOLoop.current()

        # During secure communication, we get relative URI, so make them absolute
        if self.request.uri.startswith(self.request.protocol,0): # Normal Proxy Request
            self.request.url = self.request.uri
        else:  # Transparent Proxy Request
            self.request.url = self.request.protocol + "://" + self.request.host + self.request.uri
        # WebSocketClientConnection expects ws:// & wss://
        self.request.url = self.request.url.replace("http", "ws", 1)

        # Have to add cookies and stuff
        request_headers = tornado.httputil.HTTPHeaders()
        for name, value in self.request.headers.iteritems():
            if name not in restricted_request_headers:
                request_headers.add(name, value)
        # Build a custom request
        request = tornado.httpclient.HTTPRequest(
                                                    url=self.request.url,
                                                    headers=request_headers,
                                                    proxy_host=self.application.outbound_ip,
                                                    proxy_port=self.application.outbound_port,
                                                    proxy_username=self.application.outbound_username,
                                                    proxy_password=self.application.outbound_password
                                                )
        self.upstream_connection = CustomWebSocketClientConnection(io_loop, request)
        if callback is not None:
            io_loop.add_future(self.upstream_connection.connect_future, callback)
        return self.upstream_connection.connect_future # This returns a future

    def _execute(self, transforms, *args, **kwargs):
        """
        Overriding of a method of WebSocketHandler
        """
        def start_tunnel(future):
            """
            A callback which is called when connection to url is successful
            """
            self.upstream = future.result() # We need upstream to write further messages
            self.handshake_request = self.upstream_connection.request # HTTPRequest needed for caching :P
            self.handshake_request.response_buffer = "" # Needed for websocket data & compliance with cache_handler stuff
            self.handshake_request.version = "HTTP/1.1" # Tiny hack to protect caching (But according to websocket standards)
            self.handshake_request.body = self.handshake_request.body or "" # I dont know why a None is coming :P
            tornado.websocket.WebSocketHandler._execute(self, transforms, *args, **kwargs) # The regular procedures are to be done

        # We try to connect to provided URL & then we proceed with connection on client side.
        self.upstream = self.upstream_connect(callback=start_tunnel)

    def store_upstream_data(self, message):
        """
        Save websocket data sent from client to server, i.e add it to HTTPRequest.response_buffer with direction (>>)
        """
        try: # Cannot write binary content as a string, so catch it
            self.handshake_request.response_buffer += (">>> %s\r\n"%(message))
        except TypeError:
            self.handshake_request.response_buffer += (">>> May be binary\r\n")

    def store_downstream_data(self, message):
        """
        Save websocket data sent from client to server, i.e add it to HTTPRequest.response_buffer with direction (<<)
        """
        try: # Cannot write binary content as a string, so catch it
            self.handshake_request.response_buffer += ("<<< %s\r\n"%(message))
        except TypeError:
            self.handshake_request.response_buffer += ("<<< May be binary\r\n")

    def on_message(self, message):
        """
        Everytime a message is received from client side, this instance method is called
        """
        self.upstream.write_message(message) # The obtained message is written to upstream
        self.store_upstream_data(message)

        # The following check ensures that if a callback is added for reading message from upstream, another one is not added
        if not self.upstream.read_future:
            self.upstream.read_message(callback=self.on_response) # A callback is added to read the data when upstream responds

    def on_response(self, message):
        """
        A callback when a message is recieved from upstream
        *** Here message is a future
        """
        # The following check ensures that if a callback is added for reading message from upstream, another one is not added
        if not self.upstream.read_future:
            self.upstream.read_message(callback=self.on_response)
        if self.ws_connection: # Check if connection still exists
            if message.result(): # Check if it is not NULL ( Indirect checking of upstream connection )
                self.write_message(message.result()) # Write obtained message to client
                self.store_downstream_data(message.result())
            else:
                self.close()

    def on_close(self):
        """
        Called when websocket is closed. So handshake request-response pair along with websocket data as response body is saved
        """
        # Required for cache_handler
        self.handshake_response = tornado.httpclient.HTTPResponse(
                                                                    self.handshake_request,
                                                                    self.upstream_connection.code,
                                                                    headers=self.upstream_connection.headers,
                                                                    request_time=0
                                                                 )
        # Procedure for dumping a tornado request-response
        self.cache_handler = CacheHandler(
                                            self.application.cache_dir,
                                            self.handshake_request,
                                            self.application.cookie_regex,
                                            self.application.cookie_blacklist
                                          )
        self.cached_response = self.cache_handler.load()
        self.cache_handler.dump(self.handshake_response)

class CustomWebSocketClientConnection(tornado.websocket.WebSocketClientConnection):
    # Had to extract response code, so it is necessary to override
    def _handle_1xx(self, code):
        self.code = code
        super(CustomWebSocketClientConnection, self)._handle_1xx(code)


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
            if command.startswith("Core"):
                command = "self.application." + command
                info[command] = eval(command)
            if command.startswith("setattr"):
                info[command] = eval(command)
        self.write(info)
        self.finish()


class ProxyProcess(OWTFProcess, BaseComponent):

    def initialize(self, outbound_options=[], outbound_auth=""):
        # The tornado application, which is used to pass variables to request handler
        self.application = tornado.web.Application(handlers=[
                                                            (r'.*', ProxyHandler)
                                                            ],
                                                    debug=False,
                                                    gzip=True,
                                                   )
        self.config = self.get_component("config")
        self.db_config = self.get_component("db_config")
        # All required variables in request handler
        # Required variables are added as attributes to application, so that request handler can access these
        self.application.Core = self.get_component("core")
        try:
            self.proxy_manager = self.get_component("proxy_manager")
        except ComponentNotFoundException:
            self.proxy_manager = None
        self.application.proxy_manager = self.proxy_manager
        # ctypes object allocated from shared memory to verify if proxy must inject probe code or not
        # 'i' means ctypes type is integer, initialization value is 0
        # if lock is True then a new recursive lock object is created to
        # synchronize access to the value
        self.application.Core.pnh_inject = Value('i',0,lock=True)
        self.application.inbound_ip = self.db_config.Get('INBOUND_PROXY_IP')
        self.application.inbound_port = int(self.db_config.Get('INBOUND_PROXY_PORT'))

        if self.proxy_manager: #Botnet mode needs only one proxy process
            self.instances = "1"
        else:
            self.instances = self.db_config.Get("INBOUND_PROXY_PROCESSES")

        # Proxy CACHE
        # Cache related settings, including creating required folders according to cache folder structure
        self.application.cache_dir = self.db_config.Get("INBOUND_PROXY_CACHE_DIR")
        # Clean possible older cache directory.
        if os.path.exists(self.application.cache_dir):
            FileOperations.rm_tree(self.application.cache_dir)
        FileOperations.make_dirs(self.application.cache_dir)

        # SSL MiTM
        # SSL certs, keys and other settings (os.path.expanduser because they are stored in users home directory ~/.owtf/proxy )
        self.application.ca_cert = os.path.expanduser(self.db_config.Get('CA_CERT'))
        self.application.ca_key = os.path.expanduser(self.db_config.Get('CA_KEY'))
        try: # To stop owtf from breaking for our beloved users :P
            self.application.ca_key_pass = FileOperations.open(
                os.path.expanduser(self.db_config.Get('CA_PASS_FILE')),
                'r',
                owtf_clean=False).read().strip()
        except IOError:
            self.application.ca_key_pass = "owtf"
        self.application.proxy_folder = os.path.dirname(self.application.ca_cert)
        self.application.certs_folder = os.path.expanduser(self.db_config.Get('CERTS_FOLDER'))

        try: # Ensure CA.crt and Key exist
            assert os.path.exists(self.application.ca_cert)
            assert os.path.exists(self.application.ca_key)
        except AssertionError:
            self.get_component("error_handler").FrameworkAbort("Files required for SSL MiTM are missing. Please run the install script")

        try: # If certs folder missing, create that
            assert os.path.exists(self.application.certs_folder)
        except AssertionError:
            FileOperations.make_dirs(self.application.certs_folder)

        # Blacklist (or) Whitelist Cookies
        # Building cookie regex to be used for cookie filtering for caching
        if self.db_config.Get('WHITELIST_COOKIES') == 'None':
            cookies_list = self.db_config.Get('BLACKLIST_COOKIES').split(',')
            self.application.cookie_blacklist = True
        else:
            cookies_list = self.db_config.Get('WHITELIST_COOKIES').split(',')
            self.application.cookie_blacklist = False
        if self.application.cookie_blacklist:
            regex_cookies_list = [ cookie + "=([^;]+;?)" for cookie in cookies_list ]
        else:
            regex_cookies_list = [ "(" + cookie + "=[^;]+;?)" for cookie in self.db_config.Get('COOKIES_LIST') ]
        regex_string = '|'.join(regex_cookies_list)
        self.application.cookie_regex = re.compile(regex_string)

        # Outbound Proxy
        # Outbound proxy settings to be used inside request handler
        if outbound_options:
            if len(outbound_options) == 3:
                self.application.outbound_proxy_type = outbound_options[0]
                self.application.outbound_ip = outbound_options[1]
                self.application.outbound_port = int(outbound_options[2])
            else:
                self.application.outbound_proxy_type = "http"
                self.application.outbound_ip = outbound_options[0]
                self.application.outbound_port = int(outbound_options[1])
        else:
            self.application.outbound_ip, self.application.outbound_port, self.application.outbound_proxy_type = None, None, None
        if outbound_auth:
            self.application.outbound_username, self.application.outbound_password = outbound_auth.split(":")
        else:
            self.application.outbound_username, self.application.outbound_password = None, None

        # Server has to be global, because it is used inside request handler to attach sockets for monitoring
        global server
        server = tornado.httpserver.HTTPServer(self.application)
        self.server = server

        # Header filters
        # Restricted headers are picked from framework/config/framework_config.cfg
        # These headers are removed from the response obtained from webserver, before sending it to browser
        global restricted_response_headers
        restricted_response_headers = self.config.FrameworkConfigGet("PROXY_RESTRICTED_RESPONSE_HEADERS").split(",")
        # These headers are removed from request obtained from browser, before sending it to webserver
        global restricted_request_headers
        restricted_request_headers = self.config.FrameworkConfigGet("PROXY_RESTRICTED_REQUEST_HEADERS").split(",")

        # HTTP Auth options
        if self.db_config.Get("HTTP_AUTH_HOST") != "None":
            self.application.http_auth = True
            # All the variables are lists
            self.application.http_auth_hosts = self.db_config.Get("HTTP_AUTH_HOST").strip().split(',')
            self.application.http_auth_usernames = self.db_config.Get("HTTP_AUTH_USERNAME").strip().split(',')
            self.application.http_auth_passwords = self.db_config.Get("HTTP_AUTH_PASSWORD").strip().split(',')
            self.application.http_auth_modes = self.db_config.Get("HTTP_AUTH_MODE").strip().split(',')
        else:
            self.application.http_auth = False

    # "0" equals the number of cores present in a machine
    def pseudo_run(self):
        self.application.Core.disable_console_logging()
        try:
            self.server.bind(self.application.inbound_port, address=self.application.inbound_ip)
            # Useful for using custom loggers because of relative paths in secure requests
            # http://www.joet3ch.com/blog/2011/09/08/alternative-tornado-logging/
            tornado.options.parse_command_line(args=["dummy_arg","--log_file_prefix="+self.db_config.Get("PROXY_LOG"),"--logging=info"])
            # tornado.options.parse_command_line(args=["dummy_arg","--log_file_prefix=/tmp/proxy.log","--logging=info"])
            # To run any number of instances
            self.server.start(int(self.instances))
            tornado.ioloop.IOLoop.instance().start()
        except:
            # Cleanup code
            pass

    def clean_up(self):
        self.server.stop()
        global server
        del server
        global restricted_response_headers
        del restricted_response_headers
        global restricted_request_headers
        del restricted_request_headers
