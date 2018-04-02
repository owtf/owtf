"""
owtf.api.handlers.work
~~~~~~~~~~~~~~~~~~~~~~

"""
import logging

import tornado.gen
import tornado.httpclient
import tornado.web

from owtf.api.handlers.base import APIRequestHandler
from owtf.lib import exceptions
from owtf.lib.exceptions import APIError
from owtf.managers.plugin import get_all_plugin_dicts
from owtf.managers.target import get_target_config_dicts
from owtf.managers.worker import worker_manager
from owtf.managers.worklist import add_work, delete_all_work, get_all_work, get_work, \
    patch_work, pause_all_work, remove_work, resume_all_work, search_all_work
from owtf.utils.strings import str2bool

__all__ = ['WorkerHandler', 'WorklistHandler', 'WorklistSearchHandler']


class WorkerHandler(APIRequestHandler):
    """Manage workers."""

    SUPPORTED_METHODS = ['GET', 'POST', 'DELETE', 'OPTIONS']

    def set_default_headers(self):
        self.add_header("Access-Control-Allow-Origin", "*")
        self.add_header("Access-Control-Allow-Methods", "GET, POST, DELETE")

    def get(self, worker_id=None, action=None):
        """Get all workers by ID.

        **Example request**:

        .. sourcecode:: http

            GET /api/v1/workers/ HTTP/1.1
            Accept: application/json, text/javascript, */*; q=0.01
            Origin: http://localhost:8009

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Access-Control-Allow-Origin: *
            Access-Control-Allow-Methods: GET, POST, DELETE
            Content-Type: application/json

            [
                {
                    "busy": false,
                    "name": "Worker-1",
                    "start_time": "NA",
                    "work": [],
                    "worker": 43775,
                    "paused": false,
                    "id": 1
                },
                {
                    "busy": false,
                    "name": "Worker-2",
                    "start_time": "NA",
                    "work": [],
                    "worker": 43778,
                    "paused": false,
                    "id": 2
                },
                {
                    "busy": false,
                    "name": "Worker-3",
                    "start_time": "NA",
                    "work": [],
                    "worker": 43781,
                    "paused": false,
                    "id": 3
                },
                {
                    "busy": false,
                    "name": "Worker-4",
                    "start_time": "NA",
                    "work": [],
                    "worker": 43784,
                    "paused": false,
                    "id": 4
                }
            ]
        """
        if not worker_id:
            self.success(worker_manager.get_worker_details())
        try:
            if worker_id and (not action):
                self.success(worker_manager.get_worker_details(int(worker_id)))
            if worker_id and action:
                if int(worker_id) == 0:
                    getattr(worker_manager, '%s_all_workers' % action)()
                getattr(worker_manager, '%s_worker' % action)(int(worker_id))
        except exceptions.InvalidWorkerReference:
            raise APIError(400, "Invalid worker referenced")

    def post(self, worker_id=None, action=None):
        """Add a new worker.

        **Example request**:

        .. sourcecode:: http

            POST /api/v1/workers/ HTTP/1.1
            Origin: http://localhost:8009
            Content-Length: 0

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 201 Created
            Content-Length: 0
            Access-Control-Allow-Origin: *
            Access-Control-Allow-Methods: GET, POST, DELETE
            Content-Type: text/html; charset=UTF-8
        """
        if worker_id or action:
            raise tornado.web.HTTPError(400)
        worker_manager.create_worker()
        self.set_status(201)  # Stands for "201 Created"
        self.success({})

    def options(self, worker_id=None, action=None):
        """OPTIONS check (pre-flight) for CORS.

        **Example request**:

        .. sourcecode:: http

            OPTIONS /api/v1/workers/1 HTTP/1.1
            Host: localhost:8010
            Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
            Access-Control-Request-Method: DELETE
            Origin: http://localhost:8009

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Length: 0
            Access-Control-Allow-Origin: *
            Access-Control-Allow-Methods: GET, POST, DELETE
            Content-Type: text/html; charset=UTF-8
        """
        self.set_status(200)
        self.finish()

    def delete(self, worker_id=None, action=None):
        """Delete a worker.

        **Example request**:

        .. sourcecode:: http

            DELETE /api/v1/workers/1 HTTP/1.1
            Origin: http://localhost:8009

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Length: 0
            Access-Control-Allow-Origin: *
            Access-Control-Allow-Methods: GET, POST, DELETE
            Content-Type: text/html; charset=UTF-8
        """
        if not worker_id and action:
            raise APIError(400, "Needs worker id")
        try:
            worker_manager.delete_worker(int(worker_id))
            self.success({})
        except exceptions.InvalidWorkerReference:
            raise APIError(400, "Invalid worker referenced")


class WorklistHandler(APIRequestHandler):
    """Handle the worklist."""

    SUPPORTED_METHODS = ['GET', 'POST', 'DELETE', 'PATCH']

    def get(self, work_id=None, action=None):
        try:
            if work_id is None:
                criteria = dict(self.request.arguments)
                self.success(get_all_work(self.session, criteria))
            else:
                self.success(get_work(self.session, (work_id)))
        except exceptions.InvalidParameterType:
            raise APIError(400, "Invalid parameter type provided")
        except exceptions.InvalidWorkReference:
            raise APIError(400, "Invalid worker referenced")

    def post(self, work_id=None, action=None):
        """Add plugins for a target.

        **Example request**:

        .. sourcecode:: http

            POST /api/v1/worklist/ HTTP/1.1
            Origin: http://localhost:8009
            Content-Type: application/x-www-form-urlencoded; charset=UTF-8
            X-Requested-With: XMLHttpRequest


            group=web&type=external&id=5&force_overwrite=true

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 201 Created
            Content-Length: 0
            Content-Type: text/html; charset=UTF-8
        """
        if work_id is not None or action is not None:
            raise APIError(400, "worker_id and action should be None")
        try:
            filter_data = dict(self.request.arguments)
            if not filter_data:
                raise APIError(400, "Arguments should not be null")
            plugin_list = get_all_plugin_dicts(self.session, filter_data)
            target_list = get_target_config_dicts(self.session, filter_data)
            if not plugin_list:
                raise APIError(400, "Plugin list should not be empty")
            if not target_list:
                raise APIError(400, "Target list should not be empty")
            force_overwrite = str2bool(self.get_argument("force_overwrite", "False"))
            add_work(self.session, target_list, plugin_list, force_overwrite=force_overwrite)
            self.set_status(201)
            self.success({})
        except exceptions.InvalidTargetReference:
            raise APIError(400, "Invalid target reference provided")
        except exceptions.InvalidParameterType:
            raise APIError(400, "Invalid parameter type provided")

    def delete(self, work_id=None, action=None):
        """Delete work from the worklist queue.

        **Example request**:

        .. sourcecode:: http

            DELETE /api/v1/worklist/207 HTTP/1.1
            Origin: http://localhost:8009
            X-Requested-With: XMLHttpRequest

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Length: 0
        """
        if work_id is None:
            raise APIError(400, "work_id should not be None")
        if action is not None:
            raise APIError(400, "action should be None")
        try:
            work_id = int(work_id)
            if work_id != 0:
                remove_work(self.session, work_id)
                self.set_status(200)
            else:
                if action == 'delete':
                    delete_all_work(self.session)
            self.success({})
        except exceptions.InvalidTargetReference:
            raise APIError(400, "Invalid target reference provided")
        except exceptions.InvalidParameterType:
            raise APIError(400, "Invalid parameter type provided")
        except exceptions.InvalidWorkReference:
            raise APIError(400, "Invalid worker referenced")

    def patch(self, work_id=None, action=None):
        """Resume or pause the work in the worklist.

        **Example request**:

        .. sourcecode:: http

            PATCH /api/v1/worklist/212/pause HTTP/1.1
            Host: localhost:8009
            Accept: */*
            Origin: http://localhost:8009
            X-Requested-With: XMLHttpRequest

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Length: 0
        """
        if work_id is None:
            raise APIError(400, "work_id should not be None")
        if action is None:
            raise APIError(400, "action should be None")
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
            self.success({})
        except exceptions.InvalidWorkReference:
            raise APIError(400, "Invalid worker referenced")


class WorklistSearchHandler(APIRequestHandler):
    """Search worklist."""

    SUPPORTED_METHODS = ['GET']

    def get(self):
        """

        **Example request**:

        .. sourcecode:: http

            GET /api/v1/worklist/search/?limit=100&offset=0&target_url=google.com HTTP/1.1
            Host: localhost:8009
            Accept: application/json, text/javascript, */*; q=0.01
            X-Requested-With: XMLHttpRequest

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json; charset=UTF-8


            {
                "records_total": 0,
                "records_filtered": 0,
                "data": []
            }
        """
        try:
            criteria = dict(self.request.arguments)
            criteria["search"] = True
            self.success(search_all_work(self.session, criteria))
        except exceptions.InvalidParameterType:
            raise APIError(400, "Invalid parameter type provided")
