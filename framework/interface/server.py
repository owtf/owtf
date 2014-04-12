from framework.interface import urls
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.options

class InterfaceServer(object):
    def __init__(self, Core):
        self.application = tornado.web.Application(
                                                    handlers=urls.get_handlers(Core),
                                                    debug=False,
                                                    gzip=True
                                                  )
        self.application.Core = Core
        self.server = tornado.httpserver.HTTPServer(self.application)
        # The next line is the heart of everything
        self.manager_cron = tornado.ioloop.PeriodicCallback(self.application.Core.WorkerManager.manage_workers, 2000)

    def start(self):
        try:
            self.server.bind(8009)
            tornado.options.parse_command_line(args=["dummy_arg","--log_file_prefix=/tmp/ui.log","--logging=info"])
            self.server.start(1)
            self.manager_cron.start()
            tornado.ioloop.IOLoop.instance().start()
        except KeyboardInterrupt:
            pass
