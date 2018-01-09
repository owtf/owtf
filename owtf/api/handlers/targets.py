"""
owtf.api.handlers.targets
~~~~~~~~~~~~~~~~~~~~~~

"""

import logging

import tornado.gen
import tornado.httpclient
import tornado.web

from owtf.api.handlers.base import APIRequestHandler
from owtf.lib import exceptions
from owtf.lib.exceptions import InvalidTargetReference
from owtf.managers.target import get_target_config_by_id, get_target_config_dicts, add_targets, update_target, \
    delete_target, search_target_configs, get_targets_by_severity_count


class TargetConfigHandler(APIRequestHandler):
    SUPPORTED_METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']

    def get(self, target_id=None):
        try:
            # If no target_id, means /target is accessed with or without filters
            if not target_id:
                # Get all filter data here, so that it can be passed
                filter_data = dict(self.request.arguments)
                self.write(get_target_config_dicts(filter_data))
            else:
                self.write(get_target_config_by_id(self.session, target_id))
        except InvalidTargetReference as e:
            logging.warn(e.parameter)
            raise tornado.web.HTTPError(400)

    def post(self, target_id=None):
        if (target_id) or (not self.get_argument("target_url", default=None)):  # How can one post using an id xD
            raise tornado.web.HTTPError(400)
        try:
            add_targets(self.session, dict(self.request.arguments)["target_url"])
            self.set_status(201)  # Stands for "201 Created"
        except exceptions.DBIntegrityException as e:
            logging.warn(e.parameter)
            raise tornado.web.HTTPError(409)
        except exceptions.UnresolvableTargetException as e:
            logging.warn(e.parameter)
            raise tornado.web.HTTPError(409)

    def put(self, target_id=None):
        return self.patch(target_id)

    def patch(self, target_id=None):
        if not target_id or not self.request.arguments:
            raise tornado.web.HTTPError(400)
        try:
            patch_data = dict(self.request.arguments)
            update_target(self.session, patch_data, id=target_id)
        except InvalidTargetReference as e:
            logging.warn(e.parameter)
            raise tornado.web.HTTPError(400)

    def delete(self, target_id=None):
        if not target_id:
            raise tornado.web.HTTPError(400)
        try:
            delete_target(self.session, id=target_id)
        except InvalidTargetReference as e:
            logging.warn(e.parameter)
            raise tornado.web.HTTPError(400)


class TargetConfigSearchHandler(APIRequestHandler):
    SUPPORTED_METHODS = ['GET']

    def get(self):
        try:
            filter_data = dict(self.request.arguments)
            filter_data["search"] = True
            self.write(search_target_configs(self.session, filter_data=filter_data))
        except exceptions.InvalidParameterType:
            raise tornado.web.HTTPError(400)


class TargetSeverityChartHandler(APIRequestHandler):
    SUPPORTED_METHODS = ['GET']

    def get(self):
        try:
            self.write(get_targets_by_severity_count(self.session))
        except exceptions.InvalidParameterType as e:
            raise tornado.web.HTTPError(400)
