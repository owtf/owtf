"""
owtf.api.handlers.work
~~~~~~~~~~~~~

"""

import logging

import tornado.gen
import tornado.httpclient
import tornado.web

from owtf.api.handlers.base import APIRequestHandler
from owtf.lib import exceptions
from owtf.managers.plugin import get_all_plugin_dicts
from owtf.managers.target import get_target_config_dicts
from owtf.managers.worker import worker_manager
from owtf.managers.worklist import get_all_work, get_work, add_work, remove_work, delete_all_work, patch_work, \
    pause_all_work, resume_all_work, search_all_work
from owtf.utils.strings import str2bool


class WorkerHandler(APIRequestHandler):
    SUPPORTED_METHODS = ['GET', 'POST', 'DELETE', 'OPTIONS']

    def set_default_headers(self):
        self.add_header("Access-Control-Allow-Origin", "*")
        self.add_header("Access-Control-Allow-Methods", "GET, POST, DELETE")

    def get(self, worker_id=None, action=None):
        if not worker_id:
            self.write(worker_manager.get_worker_details())
        try:
            if worker_id and (not action):
                self.write(worker_manager.get_worker_details(int(worker_id)))
            if worker_id and action:
                if int(worker_id) == 0:
                    getattr(worker_manager, '%s_all_workers' % action)()
                getattr(worker_manager, '%s_worker' % action)(int(worker_id))
        except exceptions.InvalidWorkerReference as e:
            logging.warn(e.parameter)
            raise tornado.web.HTTPError(400)

    def post(self, worker_id=None, action=None):
        if worker_id or action:
            raise tornado.web.HTTPError(400)
        worker_manager.create_worker()
        self.set_status(201)  # Stands for "201 Created"

    def options(self, worker_id=None, action=None):
        self.set_status(200)

    def delete(self, worker_id=None, action=None):
        if (not worker_id) or action:
            raise tornado.web.HTTPError(400)
        try:
            worker_manager.delete_worker(int(worker_id))
        except exceptions.InvalidWorkerReference as e:
            logging.warn(e.parameter)
            raise tornado.web.HTTPError(400)


class WorklistHandler(APIRequestHandler):
    SUPPORTED_METHODS = ['GET', 'POST', 'DELETE', 'PATCH']

    def get(self, work_id=None, action=None):
        try:
            if work_id is None:
                criteria = dict(self.request.arguments)
                self.write(get_all_work(self.session, criteria))
            else:
                self.write(get_work(self.session, (work_id)))
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
            plugin_list = get_all_plugin_dicts(self.session, filter_data)
            target_list = get_target_config_dicts(self.session, filter_data)
            if (not plugin_list) or (not target_list):
                raise tornado.web.HTTPError(400)
            force_overwrite = str2bool(self.get_argument("force_overwrite", "False"))
            add_work(self.session, target_list, plugin_list, force_overwrite=force_overwrite)
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
                remove_work(self.session, work_id)
                self.set_status(200)
            else:
                if action == 'delete':
                    delete_all_work(self.session)
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
                    patch_work(self.session, work_id, active=True)
                elif action == 'pause':
                    patch_work(self.session, work_id, active=False)
            else:
                if action == 'pause':
                    pause_all_work(self.session)
                elif action == 'resume':
                    resume_all_work(self.session)
        except exceptions.InvalidWorkReference:
            raise tornado.web.HTTPError(400)


class WorklistSearchHandler(APIRequestHandler):
    SUPPORTED_METHODS = ['GET']

    def get(self):
        try:
            criteria = dict(self.request.arguments)
            criteria["search"] = True
            self.write(search_all_work(self.session, criteria))
        except exceptions.InvalidParameterType:
            raise tornado.web.HTTPError(400)
