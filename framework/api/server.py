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
    def get(self, target_id=None):
        try:
            # If no target_id, means /target is accessed with or without filters
            if not target_id:
                # Get all filter data here, so that it can be passed
                filter_data = dict(self.request.arguments)
                self.write(json.dumps(self.application.Core.DB.Target.GetTargetConfigs(filter_data))) # A list has to be encoded
                self.set_header("Content-Type", "application/json") # Has to be set manually
            else:
                self.write(self.application.Core.DB.Target.GetTargetConfigForID(target_id))
            self.finish()
        except general.InvalidTargetReference as e:
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
        except general.InvalidTargetReference as e:
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
            patch_data = dict(self.request.arguments)
            self.application.Core.DB.Target.UpdateTarget(patch_data, ID=target_id)
            self.finish()
        except general.InvalidTargetReference as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)

    @tornado.web.asynchronous
    def delete(self, target_id = None):
        if not target_id:
            raise tornado.web.HTTPError(400)
        try:
            self.application.Core.DB.Target.DeleteTarget(ID = target_id)
            self.finish()
        except general.InvalidTargetReference as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)

class TransactionDataHandler(tornado.web.RequestHandler):
    SUPPORTED_METHODS = ['GET', 'DELETE']

    @tornado.web.asynchronous
    def get(self, target_id=None, transaction_id=None):
        try:
            if transaction_id:
                self.write(self.application.Core.DB.Transaction.GetByID(transaction_id))
            else:
                # Empty criteria ensure all transactions
                filter_data = dict(self.request.arguments)
                self.write(json.dumps(self.application.Core.DB.Transaction.GetAllAsDicts(filter_data, target_id=target_id)))
                self.set_header("Content-Type", "application/json")
            self.finish()
        except general.InvalidTargetReference as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)
        except general.InvalidTransactionReference as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)

    @tornado.web.asynchronous
    def post(self, target_url):
        raise tornado.web.HTTPError(405)

    @tornado.web.asynchronous
    def put(self):
        raise tornado.web.HTTPError(405)

    @tornado.web.asynchronous
    def patch(self):
        #TODO: Allow modification of transactions from the UI, may be adjusting scope etc.. But I don't understand it's use yet ;)
        raise tornado.web.HTTPError(405)

    @tornado.web.asynchronous
    def delete(self, target_id=None, transaction_id=None):
        try:
            if transaction_id:
                self.application.Core.DB.Transaction.DeleteTransaction(transaction_id, target_id)
            else:
                raise tornado.web.HTTPError(400)
            self.finish()
        except general.InvalidTargetReference as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)

class URLDataHandler(tornado.web.RequestHandler):
    SUPPORTED_METHODS = ['GET']

    @tornado.web.asynchronous
    def get(self, target_id=None):
        try:
            # Empty criteria ensure all transactions
            filter_data = dict(self.request.arguments)
            self.write(json.dumps(self.application.Core.DB.URL.GetAll(filter_data, target_id=target_id)))
            self.set_header("Content-Type", "application/json")
            self.finish()
        except general.InvalidTargetReference as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)

    @tornado.web.asynchronous
    def post(self, target_url):
        raise tornado.web.HTTPError(405)

    @tornado.web.asynchronous
    def put(self):
        raise tornado.web.HTTPError(405)

    @tornado.web.asynchronous
    def patch(self):
        #TODO: allow modification of urls from the ui, may be adjusting scope etc.. but i don't understand it's use yet ;)
        raise tornado.web.httperror(405)

    @tornado.web.asynchronous
    def delete(self, target_id=None):
        #TODO: allow deleting of urls from the ui
        raise tornado.web.httperror(405)

class PluginOutputHandler(tornado.web.RequestHandler):
    SUPPORTED_METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']

    @tornado.web.asynchronous
    def get(self, target_id = None, plugin_group = None, plugin_type = None, plugin_code = None):
        try:
            filter_data = dict(self.request.arguments)
            if not plugin_group: # First check if plugin_group is present in url
                self.write(json.dumps(self.application.Core.DB.POutput.GetAll(filter_data, target_id)))
            if plugin_group and (not plugin_type):
                filter_data.update({"plugin_group":plugin_group})
                self.write(json.dumps(self.application.Core.DB.POutput.GetAll(filter_data, target_id)))
            if plugin_type and plugin_group and (not plugin_code):
                if plugin_type not in self.application.Core.DB.Plugin.GetTypesForGroup(plugin_group):
                    raise tornado.web.HTTPError(400)
                filter_data.update({"plugin_type":plugin_type, "plugin_group":plugin_group})
                self.write(json.dumps(self.application.Core.DB.POutput.GetAll(filter_data, target_id)))
            if plugin_type and plugin_group and plugin_code:
                if plugin_type not in self.application.Core.DB.Plugin.GetTypesForGroup(plugin_group):
                    raise tornado.web.HTTPError(400)
                filter_data.update({"plugin_type":plugin_type, "plugin_group":plugin_group, "plugin_code":plugin_code})
                self.write(json.dumps(self.application.Core.DB.POutput.GetAll(filter_data, target_id)))
            self.set_header("Content-Type", "application/json")
            self.finish()
        except general.InvalidTargetReference as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)
        except general.InvalidParameterType as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)

    @tornado.web.asynchronous
    def post(self, target_url):
        raise tornado.web.HTTPError(405)

    @tornado.web.asynchronous
    def put(self):
        raise tornado.web.HTTPError(405)

    @tornado.web.asynchronous
    def patch(self, target_id = None, plugin_group = None, plugin_type = None, plugin_code = None):
        try:
            if (not target_id) or (not plugin_group) or (not plugin_type) or (not plugin_code):
                raise tornado.web.httperror(400)
            else:
                patch_data = dict(self.request.arguments)
                self.application.Core.DB.POutput.Update(plugin_group, plugin_type, plugin_code, patch_data, targte_id)
            self.finish()
        except general.InvalidTargetReference as e:
            cprint(e.parameter)
            raise tornado.web.HTTPErro(400)
        except general.InvalidParameterType as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)

    @tornado.web.asynchronous
    def delete(self, target_id=None, plugin_group = None, plugin_type = None, plugin_code = None):
        try:
            filter_data = dict(self.request.arguments)
            if not plugin_group: # First check if plugin_group is present in url
                self.application.Core.DB.POutput.DeleteAll(filter_data, target_id)
            if plugin_group and (not plugin_type):
                filter_data.update({"plugin_group":plugin_group})
                self.application.Core.DB.POutput.DeleteAll(filter_data, target_id)
            if plugin_type and plugin_group and (not plugin_code):
                if plugin_type not in self.application.Core.DB.Plugin.GetTypesForGroup(plugin_group):
                    raise tornado.web.HTTPError(400)
                filter_data.update({"plugin_type":plugin_type, "plugin_group":plugin_group})
                self.application.Core.DB.POutput.DeleteAll(filter_data, target_id)
            if plugin_type and plugin_group and plugin_code:
                if plugin_type not in self.application.Core.DB.Plugin.GetTypesForGroup(plugin_group):
                    raise tornado.web.HTTPError(400)
                filter_data.update({"plugin_type":plugin_type, "plugin_group":plugin_group, "plugin_code":plugin_code})
                self.application.Core.DB.POutput.DeleteAll(filter_data, target_id)
            self.finish()
        except general.InvalidTargetReference as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)
        except general.InvalidParameterType as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)

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

class WorkerHandler(tornado.web.RequestHandler):
    SUPPORTED_METHODS = ['GET']

    @tornado.web.asynchronous
    def get(self, worker_id = None, action = None):
        if not worker_id:
            self.write(json.dumps(self.application.Core.WorkerManager.get_worker_details()))
            self.set_header("Content-Type", "application/json")
        try:
            if worker_id and (not action):
                self.write(self.application.Core.WorkerManager.get_worker_details(int(worker_id))) # No json dumps because a dict is being returned
            if worker_id and action:
                getattr(self.application.Core.WorkerManager, action + '_worker')(int(worker_id))
        except general.InvalidWorkerReference as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)
        self.finish()

class WorkListHandler(tornado.web.RequestHandler):
    SUPPORTED_METHODS = ['GET', 'POST']
    @tornado.web.asynchronous
    def get(self):
        self.write(json.dumps(self.application.Core.WorkerManager.get_work_list()))
        self.set_header('Content-Type', 'application/json')
        self.finish()

    @tornado.web.asynchronous
    def post(self):
        try:
            filter_data = dict(self.request.arguments)
            plugin_list = self.application.Core.DB.Plugin.GetAll(filter_data)
            target_list = self.application.Core.DB.Target.GetTargetConfigs(filter_data)
            if (not plugin_list) or (not target_list):
                raise tornado.web.HTTPError(400)
            self.application.Core.WorkerManager.fill_work_list(target_list, plugin_list)
            self.set_status(201) # TODO: Set proper response code
            self.finish()
        except general.InvalidTargetReference as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)
        except general.InvalidParameterType as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)

    @tornado.web.asynchronous
    def delete(self):
        try:
            filter_data = dict(self.request.arguments)
            plugin_list = self.application.Core.DB.Plugin.GetAll(filter_data)
            target_list = self.application.Core.DB.Target.GetTargetConfigs(filter_data)
            self.application.Core.WorkerManager.filter_work_list(target_list, plugin_list)
            self.finish()
        except general.InvalidTargetReference as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)
        except general.InvalidParameterType as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)

class ApiServer(object):
    def __init__(self, Core):
        plugin_group_re = '(' + '|'.join(Core.DB.Plugin.GetAllGroups()) + ')?'
        plugin_type_re = '(' + '|'.join(Core.DB.Plugin.GetAllTypes()) + ')?'
        plugin_code_re = '([0-9A-Z\-]+)?'
        self.application = tornado.web.Application(
                                                    handlers=[
                                                                (r'/api/targets/?([0-9]+)?/?$', TargetConfigHandler),
                                                                (r'/api/targets/([0-9]+)/urls/?$', URLDataHandler),
                                                                (r'/api/targets/([0-9]+)/transactions/?([0-9]+)?/?$', TransactionDataHandler),
                                                                (r'/api/targets/([0-9]+)/plugins/?' + plugin_group_re + '/?' + plugin_type_re + '/?' + plugin_code_re + '/?$', PluginOutputHandler),
                                                                (r'/api/plugins/?' + plugin_group_re + '/?' + plugin_type_re + '/?' + plugin_code_re + '/?$', PluginDataHandler),
                                                                (r'/api/workers/?([0-9]+)?/?(abort|pause|resume)?/?$', WorkerHandler),
                                                                (r'/api/worklist/?$', WorkListHandler),
                                                            ],
                                                    debug=False,
                                                    gzip=True
                                                  )
        self.application.Core = Core
        self.server = tornado.httpserver.HTTPServer(self.application)
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
