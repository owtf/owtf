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
from tornado.routing import RuleRouter, Rule, PathMatches, AnyMatches
from tornado.web import Application

from owtf.api.routes import API_v1_HANDLERS, UI_HANDLERS
from owtf.api.utils import VersionMatches
from owtf.lib.owtf_process import OWTFProcess
from owtf.settings import DEBUG, SERVER_ADDR, TEMPLATES, STATIC_ROOT, SERVER_PORT, SERVER_LOG, APP_SECRET
from owtf.utils.app import Application

__all__ = ["start_server"]


class APIServer(OWTFProcess):

    def pseudo_run(self):
        api_v1 = Application(handlers=API_v1_HANDLERS, debug=DEBUG, autoreload=False, gzip=True)

        # Prepare the security context
        ctx = {"cookie_secret": APP_SECRET, "xsrf_cookies": True}
        web = Application(
            handlers=UI_HANDLERS,
            autoreload=False,
            debug=DEBUG,
            template_path=TEMPLATES,
            static_path=STATIC_ROOT,
            compiled_template_cache=True,
            **ctx
        )
        # fmt: off
        router = RuleRouter([
            Rule(PathMatches("/api/.*"), RuleRouter([
                Rule(VersionMatches("v1"), api_v1)])),
            Rule(AnyMatches(), web)
        ])
        # fmt: on
        self.server = tornado.httpserver.HTTPServer(router)
        try:
            port = int(SERVER_PORT)
            address = SERVER_ADDR
            self.server.bind(port, address=address)
            logging.warning("Starting API and UI server at http://{}:{}".format(SERVER_ADDR, str(SERVER_PORT)))
            self.logger.disable_console_logging()
            tornado.options.parse_command_line(
                args=["dummy_arg", "--log_file_prefix={}".format(SERVER_LOG), "--logging=info"]
            )
            self.server.start(0)
            tornado.ioloop.IOLoop.instance().start()
        except KeyboardInterrupt:
            pass


def start_server():
    """This method starts the interface server"""
    api_server = APIServer()
    api_server.start()
