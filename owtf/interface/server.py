import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.options

from owtf.dependency_management.dependency_resolver import BaseComponent
from owtf.interface import urls
from owtf.lib.owtf_process import OWTFProcess


class InterfaceServer(OWTFProcess, BaseComponent):
    def pseudo_run(self):
        self.get_component("core").disable_console_logging()
        config = self.get_component("config")
        db_config = self.get_component("db_config")
        db = self.get_component("db")
        application = tornado.web.Application(
            handlers=urls.get_handlers(),
            template_path=config.FrameworkConfigGet('INTERFACE_TEMPLATES_DIR'),
            debug=False,
            gzip=True,
            static_path=config.FrameworkConfigGet('STATICFILES_DIR'),
            compiled_template_cache=False
        )
        self.server = tornado.httpserver.HTTPServer(application)
        try:
            ui_port = int(config.FrameworkConfigGet("UI_SERVER_PORT"))
            ui_address = config.FrameworkConfigGet("SERVER_ADDR")
            self.server.bind(ui_port, address=ui_address)
            tornado.options.parse_command_line(
                args=['dummy_arg', '--log_file_prefix=%s' % db_config.Get('UI_SERVER_LOG'), '--logging=info'])
            self.server.start(0)
            db.create_session()
            tornado.ioloop.IOLoop.instance().start()
        except KeyboardInterrupt:
            pass


class FileServer(BaseComponent):

    def start(self):
        try:
            self.worker_manager = self.get_component("worker_manager")
            self.get_component("core").disable_console_logging()
            config = self.get_component("config")
            db = self.get_component("db")
            self.application = tornado.web.Application(
                handlers=urls.get_file_server_handlers(),
                template_path=config.FrameworkConfigGet('INTERFACE_TEMPLATES_DIR'),
                debug=False,
                gzip=True
            )
            self.application.Core = self.get_component("core")
            self.server = tornado.httpserver.HTTPServer(self.application)
            fileserver_port = int(config.FrameworkConfigGet("FILE_SERVER_PORT"))
            fileserver_addr = config.FrameworkConfigGet("SERVER_ADDR")
            self.server.bind(fileserver_port, address=fileserver_addr)
            tornado.options.parse_command_line(
                args=['dummy_arg', '--log_file_prefix=%s' % db.Config.Get('FILE_SERVER_LOG'), '--logging=info'])
            self.server.start(1)
            # 'self.manage_cron' is an instance of class 'tornado.ioloop.PeriodicCallback',
            # it schedules the given callback to be called periodically.
            # The callback is called every 2000 milliseconds.
            self.manager_cron = tornado.ioloop.PeriodicCallback(self.worker_manager.manage_workers, 2000)
            self.manager_cron.start()
            tornado.ioloop.IOLoop.instance().start()
        except KeyboardInterrupt:
            pass
        finally:
            self.clean_up()

    def clean_up(self):
        """Properly stop any tornado callbacks."""
        self.manager_cron.stop()