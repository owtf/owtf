"""
owtf.api.ui_handlers
~~~~~~~~~~~~~~~~~~~~~~~~~~

.note::
    Not been refactored since this is being deprecated
"""

from tornado.escape import url_escape
from tornado.web import RequestHandler

from owtf.api.handlers.base import UIRequestHandler
from owtf.settings import FILE_SERVER_PORT, UI_SERVER_PORT


class Index(RequestHandler):
    def get(self, path):
        self.render('index.html')


class FileRedirectHandler(UIRequestHandler):
    SUPPORTED_METHODS = ['GET']

    def get(self, file_url):
        output_files_server = "{:d}://{:d}/".format(self.request.protocol, self.request.host.replace(str(UI_SERVER_PORT),
                                                                                                str(FILE_SERVER_PORT)))
        redirect_file_url = output_files_server + url_escape(file_url, plus=False)
        self.redirect(redirect_file_url, permanent=True)
