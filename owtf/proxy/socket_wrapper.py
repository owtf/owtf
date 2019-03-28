"""
owtf.proxy.socket_wrapper
~~~~~~~~~~~~~~~~~~~~~~~~~
"""
import ssl

from tornado import ioloop

from owtf.proxy.gen_cert import gen_signed_cert


def starttls(
    socket,
    domain,
    ca_crt,
    ca_key,
    ca_pass,
    certs_folder,
    success=None,
    failure=None,
    io=None,
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
    :param io:
    :type io:
    :param options:
    :type options:
    :return:
    :rtype:
    """

    # # Default Options
    options.setdefault("do_handshake_on_connect", False)
    options.setdefault("ssl_version", ssl.PROTOCOL_SSLv23)
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
        """Handshake finished successfully."""

        io.remove_handler(wrapped.fileno())
        success and success(wrapped)

    def error():
        """The handshake failed."""
        if failure:
            return failure(wrapped)
        # # By default, just close the socket.
        io.remove_handler(wrapped.fileno())
        wrapped.close()

    def handshake(fd, events):
        """Handshake sequence with Tornado

        :param fd:
        :type fd:
        :param events:
        :type events:
        :return:
        :rtype:
        """
        if events & io.ERROR:
            error()
            return
        try:
            new_state = io.ERROR
            wrapped.do_handshake()
            return done()
        except ssl.SSLError or ssl.SSLEOFError as exc:
            if exc.args[0] == ssl.SSL_ERROR_WANT_READ:
                new_state |= io.READ
            elif exc.args[0] == ssl.SSL_ERROR_WANT_WRITE:
                new_state |= io.WRITE
            else:
                raise

        if new_state != state[0]:
            state[0] = new_state
            io.update_handler(fd, new_state)

    # set up handshake state; use a list as a mutable cell.
    io = io or ioloop.IOLoop.current()
    state = [io.ERROR]
    # Wrap the socket; swap out handlers.
    io.remove_handler(socket.fileno())
    wrapped = ssl.SSLSocket(socket, **options)
    wrapped.setblocking(0)
    io.add_handler(wrapped.fileno(), handshake, state[0])
    # Begin the handshake.
    handshake(wrapped.fileno(), 0)
    return wrapped
