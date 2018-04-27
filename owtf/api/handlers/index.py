"""
owtf.api.handlers.index
~~~~~~~~~~~~~~~~~~~~~~~

"""
from owtf.api.handlers.base import UIRequestHandler


class IndexHandler(UIRequestHandler):
    """Serves the main webapp"""

    SUPPORTED_METHODS = ["GET"]

    def get(self, path):
        """Render the homepage with all JavaScript and context.

        **Example request**:

        .. sourcecode:: http

            GET / HTTP/1.1
            Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8


        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Encoding: gzip
            Vary: Accept-Encoding
            Server: TornadoServer/5.0.1
            Content-Type: text/html; charset=UTF-8
        """
        self.render("index.html")
