"""
owtf.api.main
~~~~~~~~~~~~~
"""
import logging

import tornado
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web

from owtf.api.routes import HANDLERS
from owtf.lib.owtf_process import OWTFProcess
from owtf.settings import DEBUG, SERVER_ADDR, STATIC_ROOT, TEMPLATES, UI_SERVER_LOG, UI_SERVER_PORT
from owtf.utils.app import Application

__all__ = ['start_api_server']


class APIServer(OWTFProcess):

    def pseudo_run(self):
        application = Application(
            handlers=HANDLERS,
            template_path=TEMPLATES,
            debug=DEBUG,
            autoreload=False,
            gzip=True,
            static_path=STATIC_ROOT,
            compiled_template_cache=True)
        self.server = tornado.httpserver.HTTPServer(application)
        try:
            ui_port = int(UI_SERVER_PORT)
            ui_address = SERVER_ADDR
            self.server.bind(ui_port, address=ui_address)
            logging.warning("Starting web server at http://{}:{}".format(SERVER_ADDR, str(UI_SERVER_PORT)))
            self.logger.disable_console_logging()
            tornado.options.parse_command_line(
                args=['dummy_arg', '--log_file_prefix={}'.format(UI_SERVER_LOG), '--logging=info'])
            self.server.start()
            tornado.ioloop.IOLoop.instance().start()
        except KeyboardInterrupt:
            pass


def start_api_server():
    """This method starts the interface server"""
    api_server = APIServer()
    api_server.start()
