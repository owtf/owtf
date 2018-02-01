"""
owtf.api.main
~~~~~~~~~~~~~
"""

import tornado
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web

from owtf.api.routes import HANDLERS
from owtf.lib.owtf_process import OWTFProcess
from owtf.settings import STATIC_ROOT, UI_SERVER_LOG, SERVER_ADDR, UI_SERVER_PORT, TEMPLATES, SENTRY_API_KEY, DEBUG
from owtf.utils.app import Application


class APIServer(OWTFProcess):
    def pseudo_run(self):
        application = Application(
            handlers=HANDLERS,
            template_path=TEMPLATES,
            debug=DEBUG,
            autoreload=False,
            gzip=True,
            static_path=STATIC_ROOT,
            compiled_template_cache=True
        )
        self.logger.disable_console_logging()
        self.server = tornado.httpserver.HTTPServer(application)
        try:
            ui_port = int(UI_SERVER_PORT)
            ui_address = SERVER_ADDR
            self.server.bind(ui_port, address=ui_address)
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
