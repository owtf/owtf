"""
owtf.files.main
~~~~~~~~~~~~~~~
"""
import logging

import tornado
import tornado.httpserver
import tornado.ioloop
import tornado.options

from owtf.files.routes import HANDLERS
from owtf.settings import FILE_SERVER_LOG, FILE_SERVER_PORT, SERVER_ADDR, TEMPLATES
from owtf.utils.app import Application

__all__ = ["start_file_server"]


class FileServer():

    def start(self):
        try:
            self.application = Application(handlers=HANDLERS, template_path=TEMPLATES, debug=False, gzip=True)
            self.server = tornado.httpserver.HTTPServer(self.application)
            self.server.bind(int(FILE_SERVER_PORT), address=SERVER_ADDR)
            tornado.options.parse_command_line(
                args=["dummy_arg", "--log_file_prefix={}".format(FILE_SERVER_LOG), "--logging=info"]
            )
            self.server.start()
        except Exception as e:
            logging.error(e)


def start_file_server():
    file_server = FileServer()
    file_server.start()
