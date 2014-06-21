from framework.interface import urls
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.options

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
                    "UI_SERVER_ADDR")
                )
            tornado.options.parse_command_line(
                args=[
                    'dummy_arg',
                    '--log_file_prefix='+self.application.Core.DB.Config.Get('SERVER_LOG'),
                    '--logging=info']
                )
            self.server.start(1)
            self.manager_cron.start()
            tornado.ioloop.IOLoop.instance().start()
        except KeyboardInterrupt:
            pass
