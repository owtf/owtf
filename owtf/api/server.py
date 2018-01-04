"""
owtf.api.server
~~~~~~~~~~~~~~~~~~~~~

"""

import logging

import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.options

from owtf import db
from owtf.api import urls
from owtf.lib.owtf_process import OWTFProcess
from owtf.settings import STATIC_ROOT, UI_SERVER_LOG, SERVER_ADDR, UI_SERVER_PORT, FILE_SERVER_LOG, FILE_SERVER_PORT, \
    TEMPLATES
from owtf.managers.worker import worker_manager


class APIServer(OWTFProcess):
    def pseudo_run(self):
        application = tornado.web.Application(
            handlers=urls.get_handlers(),
            template_path=TEMPLATES,
            debug=False,
            gzip=True,
            static_path=STATIC_ROOT,
            compiled_template_cache=False
        )
        self.server = tornado.httpserver.HTTPServer(application)
        try:
            ui_port = int(UI_SERVER_PORT)
            ui_address = SERVER_ADDR
            self.server.bind(ui_port, address=ui_address)
            tornado.options.parse_command_line(
                args=['dummy_arg', '--log_file_prefix={}'.format(UI_SERVER_LOG), '--logging=info'])
            self.server.start(1)
            tornado.ioloop.IOLoop.instance().start()
        except KeyboardInterrupt:
            pass


class FileServer(object):

    def start(self):
        try:
            self.worker_manager = worker_manager
            self.application = tornado.web.Application(
                handlers=urls.get_file_server_handlers(),
                template_path=TEMPLATES,
                debug=False,
                gzip=True
            )
            self.server = tornado.httpserver.HTTPServer(self.application)
            fileserver_port = int(FILE_SERVER_PORT)
            fileserver_addr = SERVER_ADDR
            self.server.bind(fileserver_port, address=fileserver_addr)
            tornado.options.parse_command_line(
                args=['dummy_arg', '--log_file_prefix={}'.format(FILE_SERVER_LOG), '--logging=info'])
            self.server.start(1)
            # 'self.manage_cron' is an instance of class 'tornado.ioloop.PeriodicCallback',
            # it schedules the given callback to be called periodically.
            # The callback is called every 2000 milliseconds.
            self.manager_cron = tornado.ioloop.PeriodicCallback(self.worker_manager.manage_workers, 2000)
            self.manager_cron.start()
            tornado.ioloop.IOLoop.instance().start()
        except Exception as e:
            logging.error(e)
            self.clean_up()

    def clean_up(self):
        """Properly stop any tornado callbacks."""
        self.manager_cron.stop()


class CliServer(object):
    """
    The CliServer is created only when the user specifies that s-he doesn't
    want to use the WebUI.

    This can be specify with the '--nowebui' argument in the CLI.
    """
    def __init__(self):
        self.worker_manager = worker_manager
        self.manager_cron = tornado.ioloop.PeriodicCallback(self.worker_manager.manage_workers, 2000)

    def start(self):
        try:
            self.manager_cron.start()
            tornado.ioloop.IOLoop.instance().start()
        except KeyboardInterrupt:
            pass

    def clean_up(self):
        """Properly stop any tornado callbacks."""
        self.manager_cron.stop()
