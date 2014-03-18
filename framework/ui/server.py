import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.options

class WebPluginHandler(tornado.web.RequestHandler):
    SUPPORTED_METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']

    @tornado.web.asynchronous
    def get(self, group, plugin_code, target):
        self.write("test")
        self.finish()

    @tornado.web.asynchronous
    def post(self):
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

class UIServer(object):
    def __init__(self, Core):
        self.application = tornado.web.Application(
                                                    handlers=[
                                                                (r'.*', WebPluginHandler)
                                                            ],
                                                    debug=True,
                                                    gzip=True
                                                  )
        self.server = torndao.httpserver.HTTPServer(self.application)

    def start(self):
        self.server.bind("127.0.0.1",8009)
        #tornado.options.parse_command_line(args=["dummy_arg","--log_file_prefix="+self.application.Core.Config.Get("PROXY_LOG"),"--logging=info"])
        self.server.start(0)
        tornado.ioloop.IOLoop.instance().start()
