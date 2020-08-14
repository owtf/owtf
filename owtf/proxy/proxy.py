"""
owtf.proxy.proxy
~~~~~~~~~~~~~~~~

Inbound Proxy Module developed by Bharadwaj Machiraju (blog.tunnelshade.in) as a part of Google Summer of Code 2013.
"""
import datetime
import socket
import ssl

import pycurl
import tornado.curl_httpclient
import tornado.escape
import tornado.gen
import tornado.httpclient
import tornado.httpserver
import tornado.httputil
import tornado.ioloop
import tornado.iostream
import tornado.options
import tornado.template
import tornado.web
import tornado.websocket

from owtf.proxy.cache_handler import CacheHandler
from owtf.proxy.socket_wrapper import starttls
from owtf.utils.strings import utf8, to_str


def prepare_curl_callback(curl):
    curl.setopt(pycurl.PROXYTYPE, pycurl.PROXYTYPE_SOCKS5)


class ProxyHandler(tornado.web.RequestHandler):
    """This RequestHandler processes all the requests that the application received."""

    SUPPORTED_METHODS = [
        "GET",
        "POST",
        "CONNECT",
        "HEAD",
        "PUT",
        "DELETE",
        "OPTIONS",
        "TRACE",
    ]
    server = None
    restricted_request_headers = None
    restricted_response_headers = None

    def __new__(cls, application, request, **kwargs):
        """
        .. note::

            http://stackoverflow.com/questions/3209233/how-to-replace-an-instance-in-init-with-a-different-object
            Based on upgrade header, websocket request handler must be used
        """
        try:
            if request.headers["Upgrade"].lower() == "websocket":
                return CustomWebSocketHandler(application, request, **kwargs)
        except KeyError:
            pass
        return tornado.web.RequestHandler.__new__(cls)

    def set_default_headers(self):
        """Automatically called by Tornado, and is used to remove "Server" header set by tornado

        :return: None
        :rtype: None
        """
        del self._headers["Server"]

    def set_status(self, status_code, reason=None):
        """Sets the status code for our response. Overriding is done so as to handle unknown response codes gracefully.

        :param status_code: status code to set
        :type status_code: `int`
        :param reason: Status code reason
        :type reason: `str`
        :return: None
        :rtype: None
        """
        self._status_code = status_code
        if reason is not None:
            self._reason = tornado.escape.native_str(reason)
        else:
            try:
                self._reason = tornado.httputil.responses[status_code]
            except KeyError:
                self._reason = tornado.escape.native_str("Server Not Found")

    def finish_response(self, response):
        """Write a new response and cache it

        :param response:
        :type response:
        :return: None
        :rtype: None
        """
        self.set_status(response.code)
        for header, value in response.headers.get_all():
            if header == "Set-Cookie":
                self.add_header(header, value)
            else:
                if header not in self.restricted_response_headers:
                    self.set_header(header, value)
        self.finish()

    def handle_data_chunk(self, data):
        """Callback when a small chunk is received.

        :param data: Data to write
        :type data: `str`
        :return: None
        :rtype: None
        """
        if data:
            self.write(data)
            self.request.response_buffer += to_str(data)

    @tornado.gen.coroutine
    def get(self):
        """Handle all requests except the connect request. Once ssl stream is formed between browser and proxy,
        the requests are then processed by this function.

        :return: None
        :rtype: None
        """
        # The flow starts here
        self.request.local_timestamp = datetime.datetime.now()
        self.request.response_buffer = ""

        # The requests that come through ssl streams are relative requests, so transparent proxying is required. The
        # following snippet decides the url that should be passed to the async client
        if self.request.uri.startswith(
            self.request.protocol, 0
        ):  # Normal Proxy Request.
            self.request.url = self.request.uri
        else:  # Transparent Proxy Request.
            self.request.url = "{!s}://{!s}".format(
                self.request.protocol, self.request.host
            )
            if self.request.uri != "/":  # Add uri only if needed.
                self.request.url += self.request.uri

        # This block here checks for already cached response and if present returns one
        self.cache_handler = CacheHandler(
            self.application.cache_dir,
            self.request,
            self.application.cookie_regex,
            self.application.cookie_blacklist,
        )
        yield tornado.gen.Task(self.cache_handler.calculate_hash)
        self.cached_response = self.cache_handler.load()

        if self.cached_response:
            if self.cached_response.body:
                self.write(self.cached_response.body)
            self.finish_response(self.cached_response)
        else:
            # Request header cleaning
            for header in self.restricted_request_headers:
                try:
                    del self.request.headers[header]
                except BaseException:
                    continue
            # HTTP auth if exists
            http_auth_username = None
            http_auth_password = None
            http_auth_mode = None
            if self.application.http_auth:
                host = self.request.host
                # If default ports are not provided, they are added
                if ":" not in self.request.host:
                    default_ports = {"http": "80", "https": "443"}
                    if self.request.protocol in default_ports:
                        host = "{!s}:{!s}".format(
                            self.request.host, default_ports[self.request.protocol]
                        )
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
                # httprequest object is created and then passed to async client with a callback
                callback = None
                if self.application.outbound_proxy_type == "socks":
                    callback = prepare_curl_callback  # socks callback function.
                body = self.request.body or None
                request = tornado.httpclient.HTTPRequest(
                    url=self.request.url,
                    method=self.request.method,
                    body=body,
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
                    prepare_curl_callback=callback,
                    validate_cert=False,
                )
                try:
                    response = yield tornado.gen.Task(async_client.fetch, request)
                except Exception:
                    response = None
                    pass
                # Request retries
                for i in range(0, 3):
                    if response is None or response.code in [408, 599]:
                        self.request.response_buffer = ""
                        response = yield tornado.gen.Task(async_client.fetch, request)
                    else:
                        success_response = True
                        break

            self.finish_response(response)
            # Cache the response after finishing the response, so caching time is not included in response time
            self.cache_handler.dump(response)

    head = get
    post = get
    put = get
    delete = get
    options = get
    trace = get

    @tornado.gen.coroutine
    def connect(self):
        """Gets called when a connect request is received.

        * The host and port are obtained from the request uri
        * A socket is created, wrapped in ssl and then added to SSLIOStream
        * This stream is used to connect to speak to the remote host on given port
        * If the server speaks ssl on that port, callback start_tunnel is called
        * An OK response is written back to client
        * The client side socket is wrapped in ssl
        * If the wrapping is successful, a new SSLIOStream is made using that socket
        * The stream is added back to the server for monitoring

        :return: None
        :rtype: None
        """
        host, port = self.request.uri.split(":")

        def start_tunnel():
            """Init steps for a HTTPS tunnel

            :return:
            :rtype:
            """
            try:
                self.request.connection.stream.write(
                    b"HTTP/1.1 200 Connection established\r\n\r\n"
                )
                starttls(
                    self.request.connection.stream.socket,
                    host,
                    self.application.ca_cert,
                    self.application.ca_key,
                    self.application.ca_key_pass,
                    self.application.certs_folder,
                    success=ssl_success,
                )
            except tornado.iostream.StreamClosedError:
                pass

        def ssl_success(client_socket):
            """This is done on getting successful tunnel

            :param client_socket: Client socket
            :type client_socket:
            :return: None
            :rtype: None
            """
            client = tornado.iostream.SSLIOStream(client_socket)
            self.server.handle_stream(client, self.application.inbound_ip)

        def ssl_fail():
            """Tiny Hack to satisfy proxychains CONNECT request to HTTP port.

            #TODO: HTTPS fail check has to be improvised

            :return: None
            :rtype: None
            """
            try:
                self.request.connection.stream.write(
                    b"HTTP/1.1 200 Connection established\r\n\r\n"
                )
            except tornado.iostream.StreamClosedError:
                pass
            self.server.handle_stream(
                self.request.connection.stream, self.application.inbound_ip
            )

        # Hacking to be done here, so as to check for ssl using proxy and auth
        try:
            # Adds a fix for check_hostname errors in Tornado 4.3.0
            context = ssl.SSLContext(ssl.PROTOCOL_TLS)
            context.check_hostname = False
            context.load_default_certs()
            # When connecting through a new socket, no need to wrap the socket before passing to SSIOStream
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
            upstream = tornado.iostream.SSLIOStream(s, ssl_options=context)
            upstream.set_close_callback(ssl_fail)
            upstream.connect((host, int(port)), start_tunnel)
        except Exception:
            self.finish()


class CustomWebSocketHandler(tornado.websocket.WebSocketHandler):
    """Class is used for handling websocket traffic.

    * Object of this class replaces the main request handler for a request with header => "Upgrade: websocket"
    * wss:// - CONNECT request is handled by main handler
    """

    def upstream_connect(self, io_loop=None, callback=None):
        """Custom alternative to tornado.websocket.websocket_connect.

        .. note::
            Returns a future instance.

        :param io_loop:
        :type io_loop:
        :param callback:
        :type callback:
        :return:
        :rtype:
        """
        # io_loop is needed or it won't work with Tornado.
        if io_loop is None:
            io_loop = tornado.ioloop.IOLoop.current()

        # During secure communication, we get relative URI, so make them absolute
        if self.request.uri.startswith(
            self.request.protocol, 0
        ):  # Normal Proxy Request.
            self.request.url = self.request.uri
        # Transparent Proxy Request
        else:
            self.request.url = "{!s}://{!s}{!s}".format(
                self.request.protocol, self.request.host, self.request.uri
            )
        self.request.url = self.request.url.replace("http", "ws", 1)

        # Have to add cookies and stuff
        request_headers = tornado.httputil.HTTPHeaders()
        for name, value in list(self.request.headers.items()):
            if name not in ProxyHandler.restricted_request_headers:
                request_headers.add(name, value)
        # Build a custom request
        request = tornado.httpclient.HTTPRequest(
            url=self.request.url,
            headers=request_headers,
            proxy_host=self.application.outbound_ip,
            proxy_port=self.application.outbound_port,
            proxy_username=self.application.outbound_username,
            proxy_password=self.application.outbound_password,
        )
        self.upstream_connection = CustomWebSocketClientConnection(io_loop, request)
        if callback is not None:
            io_loop.add_future(self.upstream_connection.connect_future, callback)
        return self.upstream_connection.connect_future

    def _execute(self, transforms, *args, **kwargs):
        """Overriding of a method of WebSocketHandler

        :param transforms:
        :type transforms:
        :param args:
        :type args:
        :param kwargs:
        :type kwargs:
        :return:
        :rtype:
        """

        def start_tunnel(future):
            """A callback which is called when connection to url is successful."""
            # We need upstream to write further messages
            self.upstream = future.result()
            # HTTPRequest needed for caching
            self.handshake_request = self.upstream_connection.request
            # Needed for websocket data & compliance with cache_handler stuff
            self.handshake_request.response_buffer = ""
            # Tiny hack to protect caching (according to websocket standards)
            self.handshake_request.version = "HTTP/1.1"
            # XXX: I dont know why a None is coming
            self.handshake_request.body = self.handshake_request.body or ""
            # The regular procedures are to be done
            tornado.websocket.WebSocketHandler._execute(
                self, transforms, *args, **kwargs
            )

        # We try to connect to provided URL & then we proceed with connection on client side.
        self.upstream = self.upstream_connect(callback=start_tunnel)

    def store_upstream_data(self, message):
        """Save websocket data sent from client to server.
        i.e add it to HTTPRequest.response_buffer with direction (>>)

        :param message: Message to be stored
        :type message: `str`
        :return: None
        :rtype: None
        """
        try:  # Cannot write binary content as a string, so catch it
            self.handshake_request.response_buffer += ">>> {}\r\n".format(message)
        except TypeError:
            self.handshake_request.response_buffer += ">>> May be binary\r\n"

    def store_downstream_data(self, message):
        """Save websocket data sent from client to server.
        i.e add it to HTTPRequest.response_buffer with direction (<<)

        :param message: Downstream data
        :type message: `str`
        :return: None
        :rtype: None
        """
        try:  # Cannot write binary content as a string, so catch it.
            self.handshake_request.response_buffer += "<<< {}\r\n".format(message)
        except TypeError:
            self.handshake_request.response_buffer += "<<< May be binary\r\n"

    def on_message(self, message):
        """Everytime a message is received from client side, this instance method is called.

        :param message: Message to write or store
        :type message: `str`
        :return: None
        :rtype: None
        """
        self.upstream.write_message(
            message
        )  # The obtained message is written to upstream.
        self.store_upstream_data(message)
        # The following check ensures that if a callback is added for reading message from upstream, another one is not
        # added.
        if not self.upstream.read_future:
            # A callback is added to read the data when upstream responds.
            self.upstream.read_message(callback=self.on_response)

    def on_response(self, message):
        """A callback when a message is recieved from upstream.

        :param message:
        :type message:
        :return:
        :rtype:
        """
        # The following check ensures that if a callback is added for reading message from upstream, another one is not
        # added
        if not self.upstream.read_future:
            self.upstream.read_message(callback=self.on_response)
        if self.ws_connection:  # Check if connection still exists.
            if (
                message.result()
            ):  # Check if it is not NULL (indirect checking of upstream connection).
                self.write_message(
                    message.result()
                )  # Write obtained message to client.
                self.store_downstream_data(message.result())
            else:
                self.close()

    def on_close(self):
        """Called when websocket is closed.
        So handshake request-response pair along with websocket data as response body is saved

        :return: None
        :rtype: None
        """
        # Required for cache_handler
        self.handshake_response = tornado.httpclient.HTTPResponse(
            self.handshake_request,
            self.upstream_connection.code,
            headers=self.upstream_connection.headers,
            request_time=0,
        )
        # Procedure for dumping a tornado request-response
        self.cache_handler = CacheHandler(
            self.application.cache_dir,
            self.handshake_request,
            self.application.cookie_regex,
            self.application.cookie_blacklist,
        )
        self.cached_response = self.cache_handler.load()
        self.cache_handler.dump(self.handshake_response)


class CustomWebSocketClientConnection(tornado.websocket.WebSocketClientConnection):
    def _handle_1xx(self, code):
        """Had to extract response code, so it is necessary to override.

        :param code: status code
        :type code: `int`
        :return: None
        :rtype: None
        """
        self.code = code
        super(CustomWebSocketClientConnection, self)._handle_1xx(code)
