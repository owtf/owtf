"""
owtf.api.handlers.work
~~~~~~~~~~~~~

"""

import tornado.gen
import tornado.web
import tornado.httpclient

from owtf.lib import exceptions
from owtf.lib.general import cprint
from owtf.api.base import APIRequestHandler


class WorkerHandler(APIRequestHandler):
    SUPPORTED_METHODS = ['GET', 'POST', 'DELETE', 'OPTIONS']

    def set_default_headers(self):
        self.add_header("Access-Control-Allow-Origin", "*")
        self.add_header("Access-Control-Allow-Methods", "GET, POST, DELETE")

    def get(self, worker_id=None, action=None):
        if not worker_id:
            self.write(self.get_component("worker_manager").get_worker_details())
        try:
            if worker_id and (not action):
                self.write(self.get_component("worker_manager").get_worker_details(int(worker_id)))
            if worker_id and action:
                if int(worker_id) == 0:
                    getattr(self.get_component("worker_manager"), '%s_all_workers' % action)()
                getattr(self.get_component("worker_manager"), '%s_worker' % action)(int(worker_id))
        except exceptions.InvalidWorkerReference as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)

    def post(self, worker_id=None, action=None):
        if worker_id or action:
            raise tornado.web.HTTPError(400)
        self.get_component("worker_manager").create_worker()
        self.set_status(201)  # Stands for "201 Created"

    def options(self, worker_id=None, action=None):
        self.set_status(200)

    def delete(self, worker_id=None, action=None):
        if (not worker_id) or action:
            raise tornado.web.HTTPError(400)
        try:
            self.get_component("worker_manager").delete_worker(int(worker_id))
        except exceptions.InvalidWorkerReference as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)


class WorklistHandler(APIRequestHandler):
    SUPPORTED_METHODS = ['GET', 'POST', 'DELETE', 'PATCH']

    def get(self, work_id=None, action=None):
        try:
            if work_id is None:
                criteria = dict(self.request.arguments)
                self.write(self.get_component("worklist_manager").get_all(criteria))
            else:
                self.write(self.get_component("worklist_manager").get(int(work_id)))
        except exceptions.InvalidParameterType:
            raise tornado.web.HTTPError(400)
        except exceptions.InvalidWorkReference:
            raise tornado.web.HTTPError(400)

    def post(self, work_id=None, action=None):
        if work_id is not None or action is not None:
            tornado.web.HTTPError(400)
        try:
            filter_data = dict(self.request.arguments)
            if not filter_data:
                raise tornado.web.HTTPError(400)
            plugin_list = self.get_component("db_plugin").get_all(filter_data)
            target_list = self.get_component("target").get_target_config_dicts(filter_data)
            if (not plugin_list) or (not target_list):
                raise tornado.web.HTTPError(400)
            force_overwrite = self.get_component("config").str2bool(self.get_argument("force_overwrite",
                                                                                              "False"))
            self.get_component("worklist_manager").add_work(target_list, plugin_list, force_overwrite=force_overwrite)
            self.set_status(201)
        except exceptions.InvalidTargetReference:
            raise tornado.web.HTTPError(400)
        except exceptions.InvalidParameterType:
            raise tornado.web.HTTPError(400)

    def delete(self, work_id=None, action=None):
        if work_id is None or action is not None:
            tornado.web.HTTPError(400)
        try:
            work_id = int(work_id)
            if work_id != 0:
                self.get_component("worklist_manager").remove_work(work_id)
                self.set_status(200)
            else:
                if action == 'delete':
                    self.get_component("worklist_manager").delete_all()
        except exceptions.InvalidTargetReference:
            raise tornado.web.HTTPError(400)
        except exceptions.InvalidParameterType:
            raise tornado.web.HTTPError(400)
        except exceptions.InvalidWorkReference:
            raise tornado.web.HTTPError(400)

    def patch(self, work_id=None, action=None):
        if work_id is None or action is None:
            tornado.web.HTTPError(400)
        try:
            work_id = int(work_id)
            if work_id != 0:  # 0 is like broadcast address
                if action == 'resume':
                    self.get_component("db").Worklist.patch_work(work_id, active=True)
                elif action == 'pause':
                    self.get_component("db").Worklist.patch_work(work_id, active=False)
            else:
                if action == 'pause':
                    self.get_component("worklist_manager").pause_all()
                elif action == 'resume':
                    self.get_component("worklist_manager").resume_all()
        except exceptions.InvalidWorkReference:
            raise tornado.web.HTTPError(400)


class WorklistSearchHandler(APIRequestHandler):
    SUPPORTED_METHODS = ['GET']

    def get(self):
        try:
            criteria = dict(self.request.arguments)
            criteria["search"] = True
            self.write(self.get_component("worklist_manager").search_all(criteria))
        except exceptions.InvalidParameterType:
            raise tornado.web.HTTPError(400)
