from framework.interface import urls
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.options
from framework.lib.owtf_process import OWTFProcess


class InterfaceServer(object):
    def __init__(self, Core):
        self.application = tornado.web.Application(
            handlers=urls.get_handlers(Core),
            template_path=Core.Config.FrameworkConfigGet(
                'INTERFACE_TEMPLATES_DIR'),
            debug=False,
            gzip=True,
            compiled_template_cache=False
            )
        self.application.Core = Core
        self.server = tornado.httpserver.HTTPServer(self.application)
        # 'self.manage_cron' is an instance of class 'tornado.ioloop.PeriodicCallback',
        # it schedules the given callback to be called periodically.
        # The callback is called every 2000 milliseconds.
        self.manager_cron = tornado.ioloop.PeriodicCallback(
            self.application.Core.WorkerManager.manage_workers,
            2000)

    def start(self):
        try:
            self.server.bind(
                int(self.application.Core.Config.FrameworkConfigGet(
                    "UI_SERVER_PORT")),
                address=self.application.Core.Config.FrameworkConfigGet(
                    "SERVER_ADDR")
                )
            tornado.options.parse_command_line(
                args=[
                    'dummy_arg',
                    '--log_file_prefix='+self.application.Core.DB.Config.Get('UI_SERVER_LOG'),
                    '--logging=info']
                )
            self.server.start(1)
            self.manager_cron.start()
            tornado.ioloop.IOLoop.instance().start()
        except KeyboardInterrupt:
            pass


class FileServer(OWTFProcess):

    def pseudo_run(self):
        try:
            self.core.disable_console_logging()
            self.application = tornado.web.Application(
                handlers=urls.get_file_server_handlers(self.core),
                template_path=self.core.Config.FrameworkConfigGet(
                    'INTERFACE_TEMPLATES_DIR'),
                debug=False,
                gzip=True)
            self.application.Core = self.core
            self.server = tornado.httpserver.HTTPServer(self.application)
            self.server.bind(
                int(self.core.Config.FrameworkConfigGet(
                    "FILE_SERVER_PORT")),
                address=self.core.Config.FrameworkConfigGet(
                    "SERVER_ADDR")
                )
            tornado.options.parse_command_line(
                args=[
                    'dummy_arg',
                    '--log_file_prefix='+self.core.DB.Config.Get('FILE_SERVER_LOG'),
                    '--logging=info']
                )
            self.server.start(1)
            tornado.ioloop.IOLoop.instance().start()
        except KeyboardInterrupt:
            pass
