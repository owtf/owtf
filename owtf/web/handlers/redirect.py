"""
owtf.web.handlers.redirect
~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
from tornado.escape import url_escape

from owtf.web.handlers.base import UIRequestHandler
from owtf.settings import FILE_SERVER_PORT, UI_SERVER_PORT

__all__ = ['FileRedirectHandler']


class FileRedirectHandler(UIRequestHandler):
    SUPPORTED_METHODS = ['GET']

    def get(self, file_url):
        output_files_server = "{:d}://{:d}/".format(self.request.protocol,
                                                    self.request.host.replace(
                                                        str(UI_SERVER_PORT), str(FILE_SERVER_PORT)))
        redirect_file_url = output_files_server + url_escape(file_url, plus=False)
        self.redirect(redirect_file_url, permanent=True)
