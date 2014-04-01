import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.options

class TargetJSONApiHandler(tornado.web.RequestHandler):
    SUPPORTED_METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']

    @tornado.web.asynchronous
    def get(self, target_url = None):
        self.write(target_url or 'None')
        self.finish()

    @tornado.web.asynchronous
    def post(self, target_url):
        return self.get()

    @tornado.web.asynchronous
    def put(self):
        return self.get()

    @tornado.web.asynchronous
    def patch(self):
        return self.get()

    @tornado.web.asynchronous
    def delete(self):
        return self.get()

class ApiServer(object):
    def __init__(self, Core):
        self.application = tornado.web.Application(
                                                    handlers=[
                                                                (r'/json/targets/([^/]*)', TargetJSONApiHandler)
                                                            ],
                                                    debug=True,
                                                    gzip=True
                                                  )
        self.server = tornado.httpserver.HTTPServer(self.application)

    def start(self):
        try:
            self.server.bind(8009)
            tornado.options.parse_command_line(args=["dummy_arg","--log_file_prefix=/tmp/ui.log","--logging=info"])
            self.server.start(1)
            tornado.ioloop.IOLoop.instance().start()
        except KeyboardInterrupt:
            pass
