"""
owtf.proxy.https_interceptor
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Enhanced HTTPS interception module for OWTF proxy with live interceptor support.
This module provides full SSL/TLS interception capabilities for HTTPS traffic.
"""

import logging
import socket
import ssl
import threading
import time
from typing import Optional, Dict, Any, Tuple
from urllib.parse import urlparse
import tornado.ioloop
import select

logger = logging.getLogger(__name__)


class HTTPSInterceptor:
    """
    Enhanced HTTPS interceptor that provides full SSL/TLS interception
    with request/response parsing and live interceptor integration.
    """

    def __init__(self, live_interceptor=None):
        self.live_interceptor = live_interceptor
        self.active_connections = {}
        self.connection_lock = threading.Lock()

    def intercept_https_connection(self, client_stream, host, port, ca_cert, ca_key, ca_key_pass, certs_folder):
        """
        Intercept HTTPS connection and establish MITM proxy.

        Args:
            client_stream: Client connection stream
            host: Target host
            port: Target port
            ca_cert: CA certificate path
            ca_key: CA private key path
            ca_key_pass: CA key password
            certs_folder: Folder to store generated certificates

        Returns:
            bool: True if interception successful, False otherwise
        """
        try:
            logger.info(f"[HTTPS] Starting interception for {host}:{port}")

            # Send success response to establish the tunnel
            client_stream.write(b"HTTP/1.1 200 Connection established\r\n\r\n")
            client_stream.flush()

            # Get the underlying socket
            client_socket = client_stream.socket

            # Use the working starttls approach from the original code
            from owtf.proxy.socket_wrapper import starttls

            # Set up SSL termination for client connection
            def ssl_client_success(ssl_client_socket):
                try:
                    logger.info(f"[HTTPS] SSL handshake with client successful for {host}:{port}")

                    # Now establish SSL connection to upstream server
                    def ssl_upstream_success(ssl_upstream_socket):
                        """Callback when SSL handshake with upstream is successful"""
                        logger.info(f"[HTTPS] SSL handshake with upstream {host}:{port} successful")

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

                            def parse_http_requests(data_buffer, direction):
                                """Parse HTTP requests/responses from buffer and log them"""
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
                                                    from owtf.proxy.proxy import log_response

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
                                                    from owtf.proxy.proxy import log_request

                                                    log_request(
                                                        None,
                                                        method,
                                                        url,
                                                        headers,
                                                        None,  # Don't try to parse body
                                                        True,  # This is HTTPS
                                                    )
                                except Exception as e:
                                    logger.debug(f"[HTTPS] Error parsing HTTP data ({direction}): {e}")

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
                                                            "[HTTPS] client->upstream received %d bytes", len(data)
                                                        )
                                                        upstream_buffer += data

                                                        # Parse HTTP requests from client data
                                                        parse_http_requests(data, "client")
                                                    else:
                                                        logger.debug("[HTTPS] client connection closed gracefully")
                                                        client_closed = True
                                                except ssl.SSLWantReadError:
                                                    continue
                                                except ssl.SSLWantWriteError:
                                                    continue
                                                except Exception as e:
                                                    logger.error("[HTTPS] Client read error: %s", e)
                                                    client_closed = True

                                            elif sock == ssl_upstream_socket and not upstream_closed:
                                                try:
                                                    data = sock.recv(4096)
                                                    if data:
                                                        logger.debug(
                                                            "[HTTPS] upstream->client received %d bytes", len(data)
                                                        )
                                                        client_buffer += data

                                                        # Parse HTTP requests from upstream data (responses)
                                                        parse_http_requests(data, "upstream")
                                                    else:
                                                        logger.debug("[HTTPS] upstream connection closed gracefully")
                                                        upstream_closed = True
                                                except ssl.SSLWantReadError:
                                                    continue
                                                except ssl.SSLWantWriteError:
                                                    continue
                                                except Exception as e:
                                                    logger.error("[HTTPS] Upstream read error: %s", e)
                                                    upstream_closed = True

                                        except Exception as e:
                                            logger.error("[HTTPS] Socket read exception: %s", e)
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
                                                        logger.debug(
                                                            "[HTTPS] client->upstream forwarded %d bytes", sent
                                                        )
                                                        upstream_buffer = upstream_buffer[sent:]
                                                except ssl.SSLWantReadError:
                                                    continue
                                                except ssl.SSLWantWriteError:
                                                    continue
                                                except Exception as e:
                                                    logger.error("[HTTPS] Upstream write error: %s", e)
                                                    upstream_closed = True

                                            elif sock == ssl_client_socket and client_buffer:
                                                try:
                                                    sent = sock.send(client_buffer)
                                                    if sent > 0:
                                                        logger.debug(
                                                            "[HTTPS] upstream->client forwarded %d bytes", sent
                                                        )
                                                        client_buffer = client_buffer[sent:]
                                                except ssl.SSLWantReadError:
                                                    continue
                                                except ssl.SSLWantWriteError:
                                                    continue
                                                except Exception as e:
                                                    logger.error("[HTTPS] Client write error: %s", e)
                                                    upstream_closed = True

                                        except Exception as e:
                                            logger.error("[HTTPS] Socket write exception: %s", e)
                                            if sock == ssl_client_socket:
                                                client_closed = True
                                            else:
                                                upstream_closed = True

                                except Exception as e:
                                    logger.error("[HTTPS] General forwarding exception: %s", e)
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
                        logger.info("[HTTPS] Starting bidirectional forwarding for %s:%d", host, port)
                        forwarding_thread = threading.Thread(target=bidirectional_forward, daemon=True)
                        forwarding_thread.start()

                    def ssl_upstream_failure(ssl_upstream_socket):
                        """Callback when SSL handshake with upstream fails"""
                        logger.error("[HTTPS] SSL handshake with upstream %s:%d failed", host, port)
                        try:
                            ssl_client_socket.close()
                        except Exception as e:
                            logger.error("[HTTPS] Exception closing client socket after upstream failure: %s", e)

                    def connect_upstream():
                        """Connect to upstream server and establish SSL"""
                        try:
                            logger.info("[HTTPS] Connecting to upstream %s:%d", host, port)
                            upstream_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

                            # Use blocking connection for simplicity
                            upstream_socket.connect((host, port))
                            logger.info("[HTTPS] Connected to upstream %s:%d, starting SSL handshake", host, port)

                            # Set up SSL connection to upstream server
                            starttls(
                                upstream_socket,
                                host,
                                ca_cert,
                                ca_key,
                                ca_key_pass,
                                certs_folder,
                                success=ssl_upstream_success,
                                failure=ssl_upstream_failure,
                                io_loop=tornado.ioloop.IOLoop.current(),
                                do_handshake_on_connect=False,
                                ssl_version=ssl.PROTOCOL_TLS,
                                server_side=False,
                                validate_cert=False,
                            )
                        except Exception as e:
                            logger.error("[HTTPS] Error creating upstream connection: %s", e)
                            try:
                                ssl_client_socket.close()
                            except Exception as e2:
                                logger.error(
                                    "[HTTPS] Exception closing client socket after upstream connect error: %s", e2
                                )

                    # Start the upstream connection process
                    connect_upstream()

                except Exception as e:
                    logger.error("[HTTPS] Exception in ssl_client_success callback: %s", e)

            def ssl_client_failure(ssl_client_socket):
                logger.error("[HTTPS] SSL handshake with client failed for %s:%d", host, port)
                try:
                    client_stream.close()
                except Exception as e:
                    logger.error("[HTTPS] Exception closing client stream after handshake failure: %s", e)

            logger.info("[HTTPS] Starting SSL handshake with client for %s:%d", host, port)
            starttls(
                client_socket,
                host,
                ca_cert,
                ca_key,
                ca_key_pass,
                certs_folder,
                success=ssl_client_success,
                failure=ssl_client_failure,
                io_loop=tornado.ioloop.IOLoop.current(),
                do_handshake_on_connect=False,
                ssl_version=ssl.PROTOCOL_TLS,
                server_side=True,
            )

            return True

        except Exception as e:
            logger.error(f"[HTTPS] Error in HTTPS interception for {host}:{port}: {e}")
            return False

    def get_active_connections(self):
        """Get information about active HTTPS connections."""
        with self.connection_lock:
            return {
                conn_id: {"host": info["host"], "port": info["port"], "duration": time.time() - info["start_time"]}
                for conn_id, info in self.active_connections.items()
            }

    def close_all_connections(self):
        """Close all active HTTPS connections."""
        with self.connection_lock:
            for conn_id in list(self.active_connections.keys()):
                self._cleanup_connection(conn_id)

    def _cleanup_connection(self, connection_id):
        """Clean up connection resources."""
        try:
            with self.connection_lock:
                if connection_id in self.active_connections:
                    conn_info = self.active_connections[connection_id]

                    # Close sockets
                    try:
                        conn_info["client_socket"].close()
                    except:
                        pass

                    try:
                        conn_info["upstream_socket"].close()
                    except:
                        pass

                    # Remove from active connections
                    del self.active_connections[connection_id]

                    logger.info(f"[HTTPS] Cleaned up connection {connection_id}")

        except Exception as e:
            logger.error(f"[HTTPS] Error cleaning up connection {connection_id}: {e}")
