from framework.lib.general import cprint
from framework.lib import general
import tornado.web
import json

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
