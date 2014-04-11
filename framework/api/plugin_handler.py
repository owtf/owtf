from framework.lib.general import cprint
from framework.lib import general
import tornado.web
import json

class PluginDataHandler(tornado.web.RequestHandler):
    SUPPORTED_METHODS = ['GET'] #, 'POST', 'PUT', 'PATCH', 'DELETE']

    @tornado.web.asynchronous
    def get(self, plugin_group = None, plugin_type = None, plugin_code = None):
        try:
            filter_data = dict(self.request.arguments)
            if not plugin_group: # First check if plugin_group is present in url
                self.write(json.dumps(self.application.Core.DB.Plugin.GetAll(filter_data)))
            if plugin_group and (not plugin_type) and (not plugin_code):
                filter_data.update({"group":plugin_group})
                self.write(json.dumps(self.application.Core.DB.Plugin.GetAll(filter_data)))
            if plugin_group and plugin_type and (not plugin_code):
                if plugin_type not in self.application.Core.DB.Plugin.GetTypesForGroup(plugin_group):
                    raise tornado.web.HTTPError(400)
                filter_data.update({"type":plugin_type, "group":plugin_group})
                self.write(json.dumps(self.application.Core.DB.Plugin.GetAll(filter_data)))
            if plugin_group and plugin_type and plugin_code:
                if plugin_type not in self.application.Core.DB.Plugin.GetTypesForGroup(plugin_group):
                    raise tornado.web.HTTPError(400)
                filter_data.update({"type":plugin_type, "group":plugin_group, "code":plugin_code})
                self.write(json.dumps(self.application.Core.DB.Plugin.GetAll(filter_data)))
            self.set_header("Content-Type", "application/json")
            self.finish()
        except general.InvalidTargetReference as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)

    @tornado.web.asynchronous
    def post(self, target_url):
        #TODO: Creation of user plugins
        raise tornado.web.HTTPError(405)

    @tornado.web.asynchronous
    def put(self):
        raise tornado.web.HTTPError(405)

    @tornado.web.asynchronous
    def patch(self):
        raise tornado.web.httperror(405)

    @tornado.web.asynchronous
    def delete(self, target_id=None):
        raise tornado.web.httperror(405)
