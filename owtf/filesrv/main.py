import logging

import tornado
import tornado.ioloop
import tornado.httpserver
import tornado.options

from owtf.utils.app import Application
from owtf.settings import TEMPLATES, FILE_SERVER_PORT, SERVER_ADDR, FILE_SERVER_LOG
from owtf.filesrv.routes import HANDLERS
from owtf.managers.worker import worker_manager
from owtf.utils.logger import logger


class FileServer(object):

    def start(self):
        try:
            self.worker_manager = worker_manager
            self.application = Application(
                handlers=HANDLERS,
                template_path=TEMPLATES,
                debug=False,
                gzip=True
            )
            self.logger = logger
            self.logger.setup_logging()
            self.logger.disable_console_logging()
            self.server = tornado.httpserver.HTTPServer(self.application)
            self.server.bind(int(FILE_SERVER_PORT), address=SERVER_ADDR)
            tornado.options.parse_command_line(
                args=['dummy_arg', '--log_file_prefix={}'.format(FILE_SERVER_LOG), '--logging=info'])
            self.server.start()
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


def start_file_server():
    file_server = FileServer()
    file_server.start()
