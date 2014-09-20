from framework.dependency_management.dependency_resolver import BaseComponent
from framework.interface import urls
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.options


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
                    '--log_file_prefix='+self.db_config.Get('SERVER_LOG'),
                    '--logging=info']
                )
            self.server.start(1)
            self.manager_cron.start()
            tornado.ioloop.IOLoop.instance().start()
        except KeyboardInterrupt:
            pass
