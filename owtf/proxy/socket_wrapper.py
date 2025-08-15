"""
owtf.proxy.socket_wrapper
~~~~~~~~~~~~~~~~~~~~~~~~~
"""
import logging
import ssl
from typing import Optional

from tornado import ioloop

from owtf.proxy.gen_cert import gen_signed_cert

# Set up logger for socket wrapper module
logger = logging.getLogger(__name__)


def starttls(
    socket,
    domain,
    ca_crt,
    ca_key,
    ca_pass,
    certs_folder,
    success=None,
    failure=None,
    io_loop: Optional[ioloop.IOLoop] = None,
    **options
):
    """Wrap an active socket in an SSL socket.

    Taken from https://gist.github.com/weaver/293449/4d9f64652583611d267604531a1d5f8c32ac6b16.

    :param socket:
    :type socket:
    :param domain:
    :type domain:
    :param ca_crt:
    :type ca_crt:
    :param ca_key:
    :type ca_key:
    :param ca_pass:
    :type ca_pass:
    :param certs_folder:
    :type certs_folder:
    :param success:
    :type success:
    :param failure:
    :type failure:
    :param io_loop:
    :type io_loop:
    :param options:
    :type options:
    :return:
    :rtype:
    """

    # Default Options
    options.setdefault("do_handshake_on_connect", False)
    options.setdefault("ssl_version", ssl.PROTOCOL_TLS)
    options.setdefault("server_side", True)

    # The idea is to handle domains with greater than 3 dots using wildcard certs
    if domain.count(".") >= 3:
        key, cert = gen_signed_cert(
            "*." + ".".join(domain.split(".")[-3:]),
            ca_crt,
            ca_key,
            ca_pass,
            certs_folder,
        )
    else:
        key, cert = gen_signed_cert(domain, ca_crt, ca_key, ca_pass, certs_folder)
    options.setdefault("certfile", cert)
    options.setdefault("keyfile", key)

    # Handlers
    def done():
        logger.info("[MITM] [starttls] Handshake finished successfully for %s", domain)
        if io_loop:
            try:
                io_loop.remove_handler(wrapped.fileno())
            except (OSError, ValueError):
                # Socket might already be closed
                pass
        logger.info("[MITM] [starttls] About to call success callback for %s", domain)
        if success:
            logger.info("[MITM] [starttls] Calling success callback for %s", domain)
            success(wrapped)
        else:
            logger.info("[MITM] [starttls] No success callback provided for %s", domain)

    def error():
        logger.error("[MITM] [starttls] Handshake failed for %s", domain)
        if io_loop:
            try:
                io_loop.remove_handler(wrapped.fileno())
            except (OSError, ValueError):
                # Socket might already be closed
                pass
        try:
            wrapped.close()
        except (OSError, ValueError):
            # Socket might already be closed
            pass
        if failure:
            return failure(wrapped)

    def handshake(fd, events):
        logger.debug("[MITM] [starttls] Handshake event %s for %s", events, domain)
        if not io_loop:
            logger.error("[MITM] [starttls] No IOLoop available for %s", domain)
            error()
            return
        if events & io_loop.ERROR:
            logger.error("[MITM] [starttls] Handshake error event for %s", domain)
            error()
            return
        try:
            new_state = io_loop.ERROR
            wrapped.do_handshake()
            logger.info("[MITM] [starttls] do_handshake() succeeded for %s", domain)
            return done()
        except ssl.SSLWantReadError:
            logger.debug("[MITM] [starttls] SSL want read for %s", domain)
            new_state = io_loop.READ
        except ssl.SSLWantWriteError:
            logger.debug("[MITM] [starttls] SSL want write for %s", domain)
            new_state = io_loop.WRITE
        except ssl.SSLEOFError as exc:
            logger.error("[MITM] [starttls] SSL EOF error for %s: %s", domain, exc)
            error()
            return
        except ssl.SSLError as exc:
            logger.error("[MITM] [starttls] SSL error for %s: %s", domain, exc)
            if exc.args[0] == ssl.SSL_ERROR_WANT_READ:
                new_state = io_loop.READ
            elif exc.args[0] == ssl.SSL_ERROR_WANT_WRITE:
                new_state = io_loop.WRITE
            else:
                logger.error("[MITM] [starttls] Unhandled SSL error for %s: %s", domain, exc)
                error()
                return
        except Exception as exc:
            logger.error("[MITM] [starttls] Unexpected error in handshake for %s: %s", domain, exc)
            error()
            return

        if new_state != state[0]:
            state[0] = new_state
            if io_loop:
                try:
                    io_loop.update_handler(fd, new_state)
                except (OSError, ValueError):
                    # Socket might be closed
                    error()
                    return

    # set up handshake state; use a list as a mutable cell.
    if io_loop is None:
        io_loop = ioloop.IOLoop.current()
    assert isinstance(io_loop, ioloop.IOLoop)
    state = [io_loop.ERROR]

    # Wrap the socket; swap out handlers.
    try:
        io_loop.remove_handler(socket.fileno())
    except (OSError, ValueError):
        # Socket might not be registered yet
        pass

    try:
        # Determine SSL version and context
        if not options.get("server_side", True):
            # Upstream (client-side)
            options["server_hostname"] = domain
            if hasattr(ssl, "PROTOCOL_TLS_CLIENT"):
                ssl_version = ssl.PROTOCOL_TLS_CLIENT
            else:
                ssl_version = ssl.PROTOCOL_TLS
            context = ssl.SSLContext(ssl_version)
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            # Set minimum TLS version
            if hasattr(context, "minimum_version"):
                context.minimum_version = ssl.TLSVersion.TLSv1_2
            # Remove options not accepted by wrap_socket
            options.pop("certfile", None)
            options.pop("keyfile", None)
            wrapped = context.wrap_socket(socket, server_hostname=domain, do_handshake_on_connect=False)
        else:
            # Client connection (server-side)
            if hasattr(ssl, "PROTOCOL_TLS_SERVER"):
                ssl_version = ssl.PROTOCOL_TLS_SERVER
            else:
                ssl_version = ssl.PROTOCOL_TLS
            context = ssl.SSLContext(ssl_version)
            certfile = options.get("certfile")
            keyfile = options.get("keyfile")
            if not certfile or not keyfile:
                raise ValueError("certfile and keyfile must be provided for server-side SSL context")
            context.load_cert_chain(certfile=certfile, keyfile=keyfile)
            # Set minimum TLS version
            if hasattr(context, "minimum_version"):
                context.minimum_version = ssl.TLSVersion.TLSv1_2
            wrapped = context.wrap_socket(socket, server_side=True, do_handshake_on_connect=False)
    except TypeError:
        # if python version less than 3.7
        wrapped = ssl.SSLSocket(socket, **options)
    except Exception as e:
        logger.error("[MITM] [starttls] Error creating SSL context for %s: %s", domain, e)
        if failure:
            failure(socket)
        return socket

    try:
        wrapped.setblocking(False)
        io_loop.add_handler(wrapped.fileno(), handshake, state[0])
        # Begin the handshake.
        handshake(wrapped.fileno(), 0)
    except Exception as e:
        logger.error("[MITM] [starttls] Error setting up handshake for %s: %s", domain, e)
        try:
            wrapped.close()
        except:
            pass
        if failure:
            failure(socket)
        return socket

    return wrapped
