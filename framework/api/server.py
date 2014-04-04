import tornado.httpserver
from framework.lib.general import cprint
from framework.lib import general
import tornado.ioloop
import tornado.web
import tornado.options
import json

class TargetConfigHandler(tornado.web.RequestHandler):
    SUPPORTED_METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']

    @tornado.web.asynchronous
    def get(self, target_id = None):
        try:
            # If no target_id, means /target is accessed with or without filters
            if not target_id:
                # Get all filter data here, so that it can be passed
                filter_data = dict( (k,v[0]) for k,v in self.request.arguments.items() )
                self.write(json.dumps(self.application.Core.DB.Target.GetTargetConfigs(filter_data))) # A list has to be encoded
                self.set_header("Content-Type", "application/json") # Has to be set manually
            else:
                self.write(self.application.Core.DB.Target.GetTargetConfigForID(target_id))
            self.finish()
        except general.InvalidTargetException as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)

    @tornado.web.asynchronous
    def post(self, target_id = None):
        if (target_id) or (not self.get_argument("TARGET_URL", default=None)): # How can one post using an id xD
            raise tornado.web.HTTPError(400)
        try:
            self.application.Core.DB.Target.AddTarget(self.get_argument("TARGET_URL"))
            self.write(self.application.Core.DB.Target.GetTargetConfigForURL(self.get_argument("TARGET_URL")))
            self.set_status(201) # Stands for "201 Created"
            self.finish()
        except general.InvalidTargetException as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(409)

    @tornado.web.asynchronous
    def put(self, target_id=None):
        return self.patch(target_id)

    @tornado.web.asynchronous
    def patch(self, target_id = None):
        if not target_id or not self.request.arguments:
            raise tornado.web.HTTPError(400)
        try:
            patch_data = dict((k,v[0]) for k,v in self.request.arguments.items())
            self.application.Core.DB.Target.UpdateTarget(patch_data, ID=target_id)
            self.finish()
        except general.InvalidTargetException as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)

    @tornado.web.asynchronous
    def delete(self, target_id = None):
        if not target_id:
            raise tornado.web.HTTPError(400)
        try:
            self.application.Core.DB.Target.DeleteTarget(ID = target_id)
            self.finish()
        except general.InvalidTargetException as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)

class TargetDataHandler(tornado.web.RequestHandler):
    SUPPORTED_METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']

    @tornado.web.asynchronous
    def get(self, target_id = None):
        if not target_id:
            self.write(json.dumps(self.application.Core.DB.Target.GetTargetConfigs()))
            self.set_header("Content-Type", "application/json")
        else:
            self.write("Test")
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
                                                                (r'/json/target/?([0-9]+)?/?$', TargetConfigHandler),
                                                                (r'/json/target/([0-9]+)/(transactions|urls|plugins)/?$', TargetDataHandler),
                                                            ],
                                                    debug=False,
                                                    gzip=True
                                                  )
        self.application.Core = Core
        self.server = tornado.httpserver.HTTPServer(self.application)

    def start(self):
        try:
            self.server.bind(8009)
            tornado.options.parse_command_line(args=["dummy_arg","--log_file_prefix=/tmp/ui.log","--logging=info"])
            self.server.start(1)
            tornado.ioloop.IOLoop.instance().start()
        except KeyboardInterrupt:
            pass
