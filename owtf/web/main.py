"""
owtf.web.main
~~~~~~~~~~~~~

OWTF web server.
"""
import logging

import tornado
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web

from owtf.settings import TEMPLATES, STATIC_ROOT, DEBUG, SERVER_ADDR, UI_SERVER_PORT, UI_SERVER_LOG
from owtf.utils.app import Application
from owtf.utils.logger import OWTFLogger
from owtf.web.routes import UI_HANDLERS


def ui_server():
    """Bootstrap and start the OWTF web server. """
    web = Application(
        handlers=UI_HANDLERS,
        autoreload=False,
        debug=DEBUG,
        template_path=TEMPLATES,
        static_path=STATIC_ROOT,
        compiled_template_cache=True)
    address = SERVER_ADDR
    port = UI_SERVER_PORT
    logger = OWTFLogger()
    logger.enable_logging()
    logging.info("Starting web server at http://%s:%s", address, str(port))
    logger.disable_console_logging()
    tornado.options.parse_command_line(
        args=['dummy_arg', '--log_file_prefix={}'.format(UI_SERVER_LOG), '--logging=info'])
    server = tornado.httpserver.HTTPServer(web)
    server.bind(port, address=address)
    server.start()
    try:
        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        tornado.ioloop.IOLoop.instance().stop()
    finally:
        pass


def start_ui_server():
    """This method starts the interface server"""
    try:
        ui_server()
    except Exception:
        logging.error("Unexpected error occurred!")
