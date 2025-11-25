"""
owtf.proxy.proxy
~~~~~~~~~~~~~~~~

Inbound Proxy Module developed by Bharadwaj Machiraju (blog.tunnelshade.in) as a part of Google Summer of Code 2013.
"""
import datetime
import logging
import socket
import ssl
import threading
import time
import select
import os

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
from owtf.proxy.interceptor_manager import InterceptorManager
from owtf.proxy.live_interceptor import LiveInterceptor
from owtf.utils.strings import utf8, to_str

# Set up logger for proxy module
logger = logging.getLogger(__name__)

# Set up request/response logging
REQUEST_LOG_FILE = "/tmp/owtf/request_response.log"
ENABLE_REQUEST_LOGGING = True  # Set to False to disable logging entirely
# To disable logging entirely, change the line above to:
# ENABLE_REQUEST_LOGGING = False

MAX_LOG_ENTRIES_PER_MINUTE = 100  # Limit logging rate

# Live interception timeout configuration
LIVE_INTERCEPTION_TIMEOUT = 30  # Timeout in seconds for live interception decisions
LIVE_INTERCEPTION_DELAY = 0.1  # Delay in seconds between polling for live interception decisions

request_logger = logging.getLogger("owtf_requests")
request_logger.setLevel(logging.INFO)

# Track logging rate
log_entries_this_minute = 0
last_minute_reset = time.time()


def disable_request_logging():
    """Disable request logging to prevent disk space issues"""
    global ENABLE_REQUEST_LOGGING
    ENABLE_REQUEST_LOGGING = False
    logger.warning("Request logging has been disabled")


def enable_request_logging():
    """Re-enable request logging"""
    global ENABLE_REQUEST_LOGGING
    ENABLE_REQUEST_LOGGING = True
    logger.info("Request logging has been enabled")


def set_logging_rate_limit(entries_per_minute):
    """Set the maximum number of log entries per minute"""
    global MAX_LOG_ENTRIES_PER_MINUTE
    MAX_LOG_ENTRIES_PER_MINUTE = entries_per_minute
    logger.info(f"Logging rate limit set to {entries_per_minute} entries per minute")


def cleanup_large_log_file():
    """Clean up log file if it's too large"""
    try:
        if os.path.exists(REQUEST_LOG_FILE):
            file_size = os.path.getsize(REQUEST_LOG_FILE)
            if file_size > 50 * 1024 * 1024:  # If larger than 50MB
                logger.warning(f"Log file is {file_size / (1024*1024):.1f}MB, truncating to prevent disk space issues")
                # Truncate the file to keep only the last 1MB
                with open(REQUEST_LOG_FILE, "r+b") as f:
                    f.seek(-1024 * 1024, 2)  # Go to 1MB from end
                    f.truncate()
                    f.write(b"\n--- LOG FILE TRUNCATED DUE TO SIZE ---\n")
    except Exception as e:
        logger.error(f"Error cleaning up log file: {e}")


# Create log directory if it doesn't exist
try:
    os.makedirs(os.path.dirname(REQUEST_LOG_FILE), exist_ok=True)
except Exception as e:
    logger.error(f"Error creating log directory: {e}")

# Clean up large log file on startup
cleanup_large_log_file()

# Create file handler for request logging with rotation
if not request_logger.handlers:
    from logging.handlers import RotatingFileHandler

    file_handler = RotatingFileHandler(
        REQUEST_LOG_FILE, maxBytes=10 * 1024 * 1024, backupCount=5  # 10MB max file size  # Keep 5 backup files
    )
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(message)s")
    file_handler.setFormatter(formatter)
    request_logger.addHandler(file_handler)
    request_logger.propagate = False


def log_request(request, method, url, headers=None, body=None, is_https=False, is_response=False):
    """Log intercepted request/response details to file"""
    global log_entries_this_minute, last_minute_reset

    # Check if logging is disabled
    if not ENABLE_REQUEST_LOGGING:
        return

    # Rate limiting
    current_time = time.time()
    if current_time - last_minute_reset >= 60:
        log_entries_this_minute = 0
        last_minute_reset = current_time

    if log_entries_this_minute >= MAX_LOG_ENTRIES_PER_MINUTE:
        return  # Skip logging if rate limit exceeded

    log_entries_this_minute += 1

    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        protocol = "HTTPS" if is_https else "HTTP"
        direction = "RESPONSE" if is_response else "REQUEST"

        log_entry = f"[{timestamp}] {protocol} {direction} {method} {url}\n"

        if headers:
            # Limit header logging to avoid huge logs
            header_dict = dict(headers)
            if len(str(header_dict)) > 2000:
                log_entry += f"Headers: <{len(header_dict)} headers, truncated>\n"
            else:
                log_entry += f"Headers: {header_dict}\n"

        if body:
            # Limit body logging to prevent huge logs
            if isinstance(body, bytes):
                body_size = len(body)
                if body_size > 500:  # Reduced from 1000 to 500
                    log_entry += f"Body: <{body_size} bytes, first 500: {body[:500]}>\n"
                else:
                    log_entry += f"Body: {body}\n"
            else:
                body_str = str(body)
                if len(body_str) > 500:  # Reduced from 1000 to 500
                    log_entry += f"Body: <{len(body_str)} chars, first 500: {body_str[:500]}>\n"
                else:
                    log_entry += f"Body: {body_str}\n"

        log_entry += "-" * 80 + "\n"

        # Write to file
        with open(REQUEST_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_entry)

    except Exception as e:
        logger.error(f"Error logging request/response: {e}")


def log_response(status_code, url, headers=None, body=None, is_https=False):
    """Log HTTP response details"""
    log_request(None, f"HTTP/{status_code}", url, headers, body, is_https, True)


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

    def __init__(self, *args, **kwargs):
        """Initialize the proxy handler with interceptor support."""
        super().__init__(*args, **kwargs)
        # Initialize interceptor manager if not already done
        if not hasattr(self.application, "interceptor_manager"):
            self.application.interceptor_manager = InterceptorManager()
            logger.info("Initialized interceptor manager for proxy handler")

        # Initialize live interceptor if not already done
        if not hasattr(self.application, "live_interceptor"):
            self.application.live_interceptor = LiveInterceptor()
            logger.info("Initialized live interceptor for proxy handler")

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
        # Apply response interceptors
        try:
            if hasattr(self.application, "interceptor_manager"):
                response = self.application.interceptor_manager.intercept_response(response)
                logger.debug("Applied response interceptors")
        except Exception as e:
            logger.error(f"Error applying response interceptors: {e}")

        self.set_status(response.code)
        for header, value in response.headers.get_all():
            if header == "Set-Cookie":
                self.add_header(header, value)
            else:
                if header not in self.restricted_response_headers:
                    self.set_header(header, value)

        # Log the response with body
        response_body = getattr(self.request, "response_buffer", "") or getattr(response, "body", "") or ""
        log_response(
            response.code,
            getattr(self.request, "url", ""),
            response.headers,
            response_body,
            getattr(self.request, "protocol", "http") == "https",
        )

        self.finish()

    def handle_data_chunk(self, data):
        """Callback when a small chunk is received.

        :param data: Data to write
        :type data: `str`
        :return: None
        :rtype: None
        """
        if data and hasattr(self.request, "response_buffer"):
            self.write(data)
            if hasattr(self.request, "response_buffer"):
                self.request.response_buffer += to_str(data)

    @tornado.gen.coroutine
    def get(self):
        """Handle all requests except the connect request. Once ssl stream is formed between browser and proxy,
        the requests are then processed by this function.

        :return: None
        :rtype: None
        """
        # The flow starts here
        if not hasattr(self.request, "local_timestamp"):
            self.request.local_timestamp = datetime.datetime.now()
        if not hasattr(self.request, "response_buffer"):
            self.request.response_buffer = ""

        # The requests that come through ssl streams are relative requests, so transparent proxying is required. The
        # following snippet decides the url that should be passed to the async client
        if (
            hasattr(self.request, "uri")
            and self.request.uri
            and hasattr(self.request, "protocol")
            and self.request.uri.startswith(self.request.protocol, 0)
        ):  # Normal Proxy Request.
            if not hasattr(self.request, "url"):
                self.request.url = self.request.uri
        else:  # Transparent Proxy Request.
            if not hasattr(self.request, "url"):
                self.request.url = "{!s}://{!s}".format(
                    getattr(self.request, "protocol", "http"), getattr(self.request, "host", "")
                )
                if (
                    hasattr(self.request, "uri") and self.request.uri and self.request.uri != "/"
                ):  # Add uri only if needed.
                    self.request.url += self.request.uri

        # Log the intercepted request
        is_https = getattr(self.request, "protocol", "http") == "https"
        log_request(
            self.request,
            getattr(self.request, "method", "GET"),
            getattr(self.request, "url", ""),
            getattr(self.request, "headers", {}),
            getattr(self.request, "body", ""),
            is_https,
        )

        # Apply request interceptors
        try:
            if hasattr(self.application, "interceptor_manager"):
                self.request = self.application.interceptor_manager.intercept_request(self.request)
                logger.debug("Applied request interceptors")
        except Exception as e:
            logger.error(f"Error applying request interceptors: {e}")

        # Check for live interception
        try:
            if hasattr(self.application, "live_interceptor"):
                # Check if this request should be intercepted
                method = getattr(self.request, "method", "GET")
                url = getattr(self.request, "url", "")
                protocol = getattr(self.request, "protocol", "http")
                headers = dict(self.request.headers)
                body = getattr(self.request, "body", "") or ""

                request_id, should_wait = self.application.live_interceptor.intercept_request(
                    method, url, headers, body, protocol
                )

                if should_wait:
                    # Store the request ID for later decision
                    self.request.intercept_id = request_id
                    logger.info(f"Request intercepted for live modification: {request_id}")

                    # Wait for user decision (with timeout)
                    start_time = time.time()
                    while time.time() - start_time < LIVE_INTERCEPTION_TIMEOUT:  # Timeout for live interception decisions
                        decision = self.application.live_interceptor.get_decision(request_id)
                        if decision:
                            if decision.value == "drop":
                                logger.info(f"Request {request_id} dropped by user")
                                return  # Drop the request
                            elif decision.value == "modify":
                                # Apply modifications
                                req = self.application.live_interceptor.pending_requests.get(request_id)
                                if req and req.modified_headers:
                                    for key, value in req.modified_headers.items():
                                        self.request.headers[key] = value
                                if req and req.modified_body is not None:
                                    self.request.body = req.modified_body
                                logger.info(f"Request {request_id} modified by user")
                            # Clean up
                            self.application.live_interceptor.cleanup_request(request_id)
                            break
                        time.sleep(LIVE_INTERCEPTION_DELAY)  # Small delay to avoid busy waiting
                    else:
                        # Timeout - auto-forward
                        logger.info(f"Request {request_id} timed out, auto-forwarding")
                        self.application.live_interceptor.cleanup_request(request_id)

        except Exception as e:
            logger.error(f"Error in live interception: {e}")

        # This block here checks for already cached response and if present returns one
        self.cache_handler = CacheHandler(
            self.application.cache_dir,
            self.request,
            self.application.cookie_regex,
            self.application.cookie_blacklist,
        )
        # Fix for tornado.gen.Task compatibility
        try:
            # For newer Tornado versions, use the callback directly
            self.cache_handler.calculate_hash()
        except TypeError:
            # For older Tornado versions, use Task
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
                        host = "{!s}:{!s}".format(self.request.host, default_ports[self.request.protocol])
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
                    # Fix for tornado.gen.Task compatibility
                    try:
                        response = yield async_client.fetch(request)
                    except AttributeError:
                        # For older Tornado versions, use Task
                        response = yield tornado.gen.Task(async_client.fetch, request)
                except Exception:
                    response = None
                    pass
                # Request retries
                for i in range(0, 3):
                    if response is None or response.code in [408, 599]:
                        self.request.response_buffer = ""
                        try:
                            response = yield async_client.fetch(request)
                        except AttributeError:
                            # For older Tornado versions, use Task
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
        * SSL interception is performed by terminating client SSL and establishing upstream SSL
        * An OK response is written back to client
        * Decrypted data is forwarded bidirectionally between client and server

        :return: None
        :rtype: None
        """
        host, port = self.request.uri.split(":")
        port = int(port)

        # Log the CONNECT request (HTTPS interception)
        log_request(self.request, "CONNECT", f"{host}:{port}", self.request.headers, None, True)  # This is HTTPS

        try:
            # Get the client stream
            client_stream = self.request.connection.stream
            logger.info("[MITM] Received CONNECT for %s:%d", host, port)

            # Send success response to establish the tunnel
            client_stream.write(b"HTTP/1.1 200 Connection established\r\n\r\n")
            self._finished = True
            logger.info("[MITM] Sent 200 Connection established to client for %s:%d", host, port)

            # Set up SSL termination for client connection
            def ssl_client_success(ssl_client_socket):
                try:
                    logger.info("[MITM] SSL handshake with client successful for %s:%d", host, port)

                    # Now establish SSL connection to upstream server
                    def ssl_upstream_success(ssl_upstream_socket):
                        """Callback when SSL handshake with upstream is successful"""
                        logger.info("[MITM] SSL handshake with upstream %s:%d successful", host, port)

                        # Set up bidirectional forwarding between SSL sockets
                        client_closed = False
                        upstream_closed = False

                        def bidirectional_forward():
                            """Handle bidirectional forwarding in a single thread"""
                            nonlocal client_closed, upstream_closed

                            # Set sockets to non-blocking mode
                            try:
                                ssl_client_socket.setblocking(False)
                                ssl_upstream_socket.setblocking(False)
                            except:
                                pass

                            client_buffer = b""
                            upstream_buffer = b""

                            # HTTP request parsing buffers - no longer needed with simplified approach
                            # client_http_buffer = b""
                            # upstream_http_buffer = b""

                            def parse_http_requests(data_buffer, direction):
                                """Parse HTTP requests/responses from buffer and log them"""
                                # Simple approach: just log the first line if it looks like HTTP
                                try:
                                    lines = data_buffer.split(b"\r\n")
                                    if lines and lines[0]:
                                        first_line = lines[0].decode("utf-8", errors="ignore").strip()
                                        if first_line and " " in first_line:
                                            parts = first_line.split(" ")

                                            # Check if it's an HTTP response (starts with HTTP/)
                                            if first_line.startswith("HTTP/"):
                                                if len(parts) >= 2:
                                                    status_code = parts[1]
                                                    # Extract headers (simplified)
                                                    headers = {}
                                                    for line in lines[1:]:
                                                        if b": " in line:
                                                            header_line = line.decode("utf-8", errors="ignore")
                                                            if ": " in header_line:
                                                                key, value = header_line.split(": ", 1)
                                                                headers[key] = value

                                                    # Log the HTTP response
                                                    log_response(
                                                        status_code,
                                                        f"https://{host}",
                                                        headers,
                                                        None,  # Don't try to parse body
                                                        True,  # This is HTTPS
                                                    )

                                            # Check if it's an HTTP request (starts with method)
                                            elif len(parts) >= 2:
                                                method = parts[0]
                                                path = parts[1]

                                                # Check if it's a valid HTTP method
                                                if method in [
                                                    "GET",
                                                    "POST",
                                                    "PUT",
                                                    "DELETE",
                                                    "HEAD",
                                                    "OPTIONS",
                                                    "PATCH",
                                                ]:
                                                    # Construct full URL
                                                    if path.startswith("/"):
                                                        url = f"https://{host}{path}"
                                                    else:
                                                        url = f"https://{host}/{path}"

                                                    # Extract headers (simplified)
                                                    headers = {}
                                                    for line in lines[1:]:
                                                        if b": " in line:
                                                            header_line = line.decode("utf-8", errors="ignore")
                                                            if ": " in header_line:
                                                                key, value = header_line.split(": ", 1)
                                                                headers[key] = value

                                                    # Log the HTTP request
                                                    log_request(
                                                        None,
                                                        method,
                                                        url,
                                                        headers,
                                                        None,  # Don't try to parse body
                                                        True,  # This is HTTPS
                                                    )
                                except Exception as e:
                                    logger.debug(f"[MITM] Error parsing HTTP data ({direction}): {e}")

                            while not client_closed and not upstream_closed:
                                try:
                                    # Use select to check which socket has data
                                    readable, writable, _ = select.select(
                                        [ssl_client_socket, ssl_upstream_socket]
                                        if not client_closed and not upstream_closed
                                        else [],
                                        [ssl_client_socket, ssl_upstream_socket]
                                        if (client_buffer or upstream_buffer)
                                        else [],
                                        [],
                                        0.1,
                                    )

                                    # Handle readable sockets
                                    for sock in readable:
                                        try:
                                            if sock == ssl_client_socket and not client_closed:
                                                try:
                                                    data = sock.recv(4096)
                                                    if data:
                                                        logger.debug(
                                                            "[MITM] client->upstream received %d bytes", len(data)
                                                        )
                                                        upstream_buffer += data

                                                        # Parse HTTP requests from client data
                                                        parse_http_requests(data, "client")
                                                    else:
                                                        logger.debug("[MITM] client connection closed gracefully")
                                                        client_closed = True
                                                except ssl.SSLWantReadError:
                                                    continue
                                                except ssl.SSLWantWriteError:
                                                    continue
                                                except Exception as e:
                                                    logger.error("[MITM] Client read error: %s", e)
                                                    client_closed = True

                                            elif sock == ssl_upstream_socket and not upstream_closed:
                                                try:
                                                    data = sock.recv(4096)
                                                    if data:
                                                        logger.debug(
                                                            "[MITM] upstream->client received %d bytes", len(data)
                                                        )
                                                        client_buffer += data

                                                        # Parse HTTP requests from upstream data (responses)
                                                        parse_http_requests(data, "upstream")
                                                    else:
                                                        logger.debug("[MITM] upstream connection closed gracefully")
                                                        upstream_closed = True
                                                except ssl.SSLWantReadError:
                                                    continue
                                                except ssl.SSLWantWriteError:
                                                    continue
                                                except Exception as e:
                                                    logger.error("[MITM] Upstream read error: %s", e)
                                                    upstream_closed = True

                                        except Exception as e:
                                            logger.error("[MITM] Socket read exception: %s", e)
                                            if sock == ssl_client_socket:
                                                client_closed = True
                                            else:
                                                upstream_closed = True

                                    # Handle writable sockets
                                    for sock in writable:
                                        try:
                                            if sock == ssl_upstream_socket and upstream_buffer:
                                                try:
                                                    sent = sock.send(upstream_buffer)
                                                    if sent > 0:
                                                        logger.debug("[MITM] client->upstream forwarded %d bytes", sent)
                                                        upstream_buffer = upstream_buffer[sent:]
                                                except ssl.SSLWantReadError:
                                                    continue
                                                except ssl.SSLWantWriteError:
                                                    continue
                                                except Exception as e:
                                                    logger.error("[MITM] Upstream write error: %s", e)
                                                    upstream_closed = True

                                            elif sock == ssl_client_socket and client_buffer:
                                                try:
                                                    sent = sock.send(client_buffer)
                                                    if sent > 0:
                                                        logger.debug("[MITM] upstream->client forwarded %d bytes", sent)
                                                        client_buffer = client_buffer[sent:]
                                                except ssl.SSLWantReadError:
                                                    continue
                                                except ssl.SSLWantWriteError:
                                                    continue
                                                except Exception as e:
                                                    logger.error("[MITM] Client write error: %s", e)
                                                    upstream_closed = True

                                        except Exception as e:
                                            logger.error("[MITM] Socket write exception: %s", e)
                                            if sock == ssl_client_socket:
                                                client_closed = True
                                            else:
                                                upstream_closed = True

                                except Exception as e:
                                    logger.error("[MITM] General forwarding exception: %s", e)
                                    break

                            # Clean up both sockets
                            try:
                                if not client_closed:
                                    ssl_client_socket.shutdown(socket.SHUT_RDWR)
                                    ssl_client_socket.close()
                            except:
                                pass

                            try:
                                if not upstream_closed:
                                    ssl_upstream_socket.shutdown(socket.SHUT_RDWR)
                                    ssl_upstream_socket.close()
                            except:
                                pass

                        # Start bidirectional forwarding in a single thread
                        logger.info("[MITM] Starting bidirectional forwarding for %s:%d", host, port)
                        forwarding_thread = threading.Thread(target=bidirectional_forward, daemon=True)
                        forwarding_thread.start()

                    def ssl_upstream_failure(ssl_upstream_socket):
                        """Callback when SSL handshake with upstream fails"""
                        logger.error("[MITM] SSL handshake with upstream %s:%d failed", host, port)
                        try:
                            ssl_client_socket.close()
                        except Exception as e:
                            logger.error("[MITM] Exception closing client socket after upstream failure: %s", e)

                    def connect_upstream():
                        """Connect to upstream server and establish SSL"""
                        try:
                            logger.info("[MITM] Connecting to upstream %s:%d", host, port)
                            upstream_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

                            # Use blocking connection for simplicity
                            upstream_socket.connect((host, port))
                            logger.info("[MITM] Connected to upstream %s:%d, starting SSL handshake", host, port)

                            # Set up SSL connection to upstream server
                            starttls(
                                upstream_socket,
                                host,
                                self.application.ca_cert,
                                self.application.ca_key,
                                self.application.ca_key_pass,
                                self.application.certs_folder,
                                success=ssl_upstream_success,
                                failure=ssl_upstream_failure,
                                io_loop=tornado.ioloop.IOLoop.current(),
                                do_handshake_on_connect=False,
                                ssl_version=ssl.PROTOCOL_TLS,
                                server_side=False,
                                validate_cert=False,
                            )
                        except Exception as e:
                            logger.error("[MITM] Error creating upstream connection: %s", e)
                            try:
                                ssl_client_socket.close()
                            except Exception as e2:
                                logger.error(
                                    "[MITM] Exception closing client socket after upstream connect error: %s", e2
                                )

                    # Start the upstream connection process
                    connect_upstream()

                except Exception as e:
                    logger.error("[MITM] Exception in ssl_client_success callback: %s", e)

            def ssl_client_failure(ssl_client_socket):
                logger.error("[MITM] SSL handshake with client failed for %s:%d", host, port)
                try:
                    client_stream.close()
                except Exception as e:
                    logger.error("[MITM] Exception closing client stream after handshake failure: %s", e)

            logger.info("[MITM] Starting SSL handshake with client for %s:%d", host, port)
            starttls(
                client_stream.socket,
                host,
                self.application.ca_cert,
                self.application.ca_key,
                self.application.ca_key_pass,
                self.application.certs_folder,
                success=ssl_client_success,
                failure=ssl_client_failure,
                io_loop=tornado.ioloop.IOLoop.current(),
                do_handshake_on_connect=False,
                ssl_version=ssl.PROTOCOL_TLS,
                server_side=True,
            )

        except Exception as e:
            logger.error("[MITM] Error in connect method: %s", e)
            self._finished = True
            try:
                self.request.connection.stream.write(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
            except Exception as send_error:
                logger.error("[MITM] Error sending 502 response: %s", send_error)
            try:
                self.request.connection.stream.close()
            except Exception as close_error:
                logger.error("[MITM] Error closing connection after error: %s", close_error)


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
        if self.request.uri.startswith(self.request.protocol, 0):  # Normal Proxy Request.
            self.request.url = self.request.uri
        # Transparent Proxy Request
        else:
            self.request.url = "{!s}://{!s}{!s}".format(self.request.protocol, self.request.host, self.request.uri)
        self.request.url = self.request.url.replace("http", "ws", 1)

        # Log WebSocket connection
        is_https = self.request.protocol == "https"
        log_request(self.request, "WEBSOCKET", self.request.url, self.request.headers, None, is_https)

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
            tornado.websocket.WebSocketHandler._execute(self, transforms, *args, **kwargs)

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
        self.upstream.write_message(message)  # The obtained message is written to upstream.
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
            if message.result():  # Check if it is not NULL (indirect checking of upstream connection).
                self.write_message(message.result())  # Write obtained message to client.
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
