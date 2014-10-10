from framework.dependency_management.dependency_resolver import BaseComponent
from framework.interface import urls
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.options
from framework.lib.owtf_process import OWTFProcess


class InterfaceServer(BaseComponent):
    def __init__(self):
        self.config = self.get_component("config")
        self.db_config = self.get_component("db_config")
        self.worker_manager = self.get_component("worker_manager")
        self.application = tornado.web.Application(
            handlers=urls.get_handlers(),
            template_path=self.config.FrameworkConfigGet(
                'INTERFACE_TEMPLATES_DIR'),
            debug=False,
            gzip=True,
            compiled_template_cache=False
            )
        self.server = tornado.httpserver.HTTPServer(self.application)
        # 'self.manage_cron' is an instance of class 'tornado.ioloop.PeriodicCallback',
        # it schedules the given callback to be called periodically.
        # The callback is called every 2000 milliseconds.
        self.manager_cron = tornado.ioloop.PeriodicCallback(
            self.worker_manager.manage_workers,
            2000)

    def start(self):
        try:
            self.server.bind(
                int(self.config.FrameworkConfigGet(
                    "UI_SERVER_PORT")),
                address=self.config.FrameworkConfigGet(
                    "UI_SERVER_ADDR")
                )
            tornado.options.parse_command_line(
                args=[
                    'dummy_arg',
                    '--log_file_prefix='+self.db_config.Get('UI_SERVER_LOG'),
                    '--logging=info']
                )
            self.server.start(1)
            self.manager_cron.start()
            tornado.ioloop.IOLoop.instance().start()
        except KeyboardInterrupt:
            pass


class FileServer(OWTFProcess, BaseComponent):

    def pseudo_run(self):
        try:
            self.get_component("core").disable_console_logging()
            config = self.get_component("config")
            db = self.get_component("db")
            self.application = tornado.web.Application(
                handlers=urls.get_file_server_handlers(),
                template_path=config.FrameworkConfigGet(
                    'INTERFACE_TEMPLATES_DIR'),
                debug=False,
                gzip=True)
            self.application.Core = self.get_component("core")
            self.server = tornado.httpserver.HTTPServer(self.application)
            self.server.bind(
                int(config.FrameworkConfigGet(
                    "FILE_SERVER_PORT")),
                address=config.FrameworkConfigGet(
                    "SERVER_ADDR")
                )
            tornado.options.parse_command_line(
                args=[
                    'dummy_arg',
                    '--log_file_prefix='+db.Config.Get('FILE_SERVER_LOG'),
                    '--logging=info']
                )
            self.server.start(1)
            tornado.ioloop.IOLoop.instance().start()
        except KeyboardInterrupt:
            pass
