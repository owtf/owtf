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

from owtf.api.routes import API_v1_HANDLERS
from owtf.api.utils import VersionMatches
from owtf.lib.owtf_process import OWTFProcess
from owtf.settings import DEBUG, SERVER_ADDR, API_SERVER_PORT, API_SERVER_LOG
from owtf.utils.app import Application

__all__ = ['start_api_server']


class APIServer(OWTFProcess):

    def pseudo_run(self):
        api_v1 = Application(handlers=API_v1_HANDLERS, debug=DEBUG, autoreload=False, gzip=True)
        # yapf: disable
        router = RuleRouter([
            Rule(PathMatches("/api/.*"), RuleRouter([
                Rule(VersionMatches("v1"), api_v1)])),
            Rule(AnyMatches(), api_v1)
        ])
        # yapf: enable
        self.server = tornado.httpserver.HTTPServer(router)
        try:
            port = int(API_SERVER_PORT)
            address = SERVER_ADDR
            self.server.bind(port, address=address)
            logging.warning("Starting API server at {}:{}".format(SERVER_ADDR, str(API_SERVER_PORT)))
            self.logger.disable_console_logging()
            tornado.options.parse_command_line(
                args=['dummy_arg', '--log_file_prefix={}'.format(API_SERVER_LOG), '--logging=info'])
            self.server.start(0)
            tornado.ioloop.IOLoop.instance().start()
        except KeyboardInterrupt:
            pass


def start_api_server():
    """This method starts the interface server"""
    api_server = APIServer()
    api_server.start()
