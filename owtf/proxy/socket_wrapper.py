"""
owtf.http.proxy.socket_wrapper
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Inbound Proxy Module developed by Bharadwaj Machiraju (blog.tunnelshade.in) as a part of Google Summer of Code 2013
"""

import ssl

from tornado import ioloop

from owtf.proxy.gen_cert import gen_signed_cert


def wrap_socket(socket, domain, ca_crt, ca_key, ca_pass, certs_folder, success=None, failure=None, io=None, **options):
    """Wrap an active socket in an SSL socket.

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
    options.setdefault('do_handshake_on_connect', False)
    options.setdefault('ssl_version', ssl.PROTOCOL_SSLv23)
    options.setdefault('server_side', True)

    # The idea is to handle domains with greater than 3 dots using wildcard certs
    if domain.count(".") >= 3:
        key, cert = gen_signed_cert("*." + ".".join(domain.split(".")[-3:]), ca_crt, ca_key, ca_pass, certs_folder)
    else:
        key, cert = gen_signed_cert(domain, ca_crt, ca_key, ca_pass, certs_folder)
    options.setdefault('certfile', cert)
    options.setdefault('keyfile', key)

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
        """Handler fGetting the same error here... also looking for answers....
        TheHippo Dec 19 '12 at 20:29or SSL handshake negotiation.
        See Python docs for ssl.do_handshake().


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
        except ssl.SSLError as exc:
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
    io = io or ioloop.IOLoop.instance()
    state = [io.ERROR]
    # Wrap the socket; swap out handlers.
    io.remove_handler(socket.fileno())
    wrapped = ssl.SSLSocket(socket, **options)
    wrapped.setblocking(0)
    io.add_handler(wrapped.fileno(), handshake, state[0])
    # Begin the handshake.
    handshake(wrapped.fileno(), 0)
    return wrapped
