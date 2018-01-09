"""
owtf.api.plugin
~~~~~~~~~~~~~~~

"""

import collections
import logging

import tornado.gen
import tornado.httpclient
import tornado.web

from owtf.api.handlers.base import APIRequestHandler
from owtf.lib import exceptions
from owtf.managers.mapping import get_all_mappings
from owtf.managers.plugin import get_types_for_plugin_group, get_all_plugin_dicts, get_all_test_groups
from owtf.managers.poutput import get_all_poutputs, update_poutput, delete_all_poutput


class PluginDataHandler(APIRequestHandler):
    SUPPORTED_METHODS = ['GET']
    # TODO: Creation of user plugins

    def get(self, plugin_group=None, plugin_type=None, plugin_code=None):
        try:
            filter_data = dict(self.request.arguments)
            if not plugin_group:  # Check if plugin_group is present in url
                self.write(get_all_plugin_dicts(self.session, filter_data))
            if plugin_group and (not plugin_type) and (not plugin_code):
                filter_data.update({"group": plugin_group})
                self.write(get_all_plugin_dicts(self.session, filter_data))
            if plugin_group and plugin_type and (not plugin_code):
                if plugin_type not in get_types_for_plugin_group(self.session, plugin_group):
                    raise tornado.web.HTTPError(400)
                filter_data.update({"type": plugin_type, "group": plugin_group})
                self.write(get_all_plugin_dicts(self.session, filter_data))
            if plugin_group and plugin_type and plugin_code:
                if plugin_type not in get_types_for_plugin_group(self.session, plugin_group):
                    raise tornado.web.HTTPError(400)
                filter_data.update({"type": plugin_type, "group": plugin_group, "code": plugin_code})
                # This combination will be unique, so have to return a dict
                results = get_all_plugin_dicts(self.session, filter_data)
                if results:
                    self.write(results[0])
                else:
                    raise tornado.web.HTTPError(400)
        except exceptions.InvalidTargetReference as e:
            logging.warn(e.parameter)
            raise tornado.web.HTTPError(400)


class PluginNameOutput(APIRequestHandler):
    SUPPORTED_METHODS = ['GET']

    def get(self, target_id=None):
        """Retrieve scan results for a target.
        :return: {code: {data: [], details: {}}, code2: {data: [], details: {}} }
        This API doesn't return `output` section as part of optimization.
        `data` is array of scan results according to `plugin_types`.
        `details` contains info about `code`.
        """
        try:
            filter_data = dict(self.request.arguments)
            results = get_all_poutputs(self.session, filter_data, target_id=int(target_id), inc_output=False)

            # Get mappings
            mappings = get_all_mappings(self.session)

            # Get test groups as well, for names and info links
            groups = {}
            for group in get_all_test_groups(self.session):
                group['mappings'] = mappings.get(group['code'], {})
                groups[group['code']] = group

            dict_to_return = {}
            for item in results:
                if (dict_to_return.has_key(item['plugin_code'])):
                    dict_to_return[item['plugin_code']]['data'].append(item)
                else:
                    ini_list = []
                    ini_list.append(item)
                    dict_to_return[item["plugin_code"]] = {}
                    dict_to_return[item["plugin_code"]]["data"] = ini_list
                    dict_to_return[item["plugin_code"]]["details"] = groups[item["plugin_code"]]
            dict_to_return = collections.OrderedDict(sorted(dict_to_return.items()))
            if results:
                self.write(dict_to_return)
            else:
                raise tornado.web.HTTPError(400)

        except exceptions.InvalidTargetReference as e:
            logging.warn(e.parameter)
            raise tornado.web.HTTPError(400)
        except exceptions.InvalidParameterType as e:
            logging.warn(e.parameter)
            raise tornado.web.HTTPError(400)


class PluginOutputHandler(APIRequestHandler):
    SUPPORTED_METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']

    def get(self, target_id=None, plugin_group=None, plugin_type=None, plugin_code=None):
        try:
            filter_data = dict(self.request.arguments)
            if plugin_group and (not plugin_type):
                filter_data.update({"plugin_group": plugin_group})
            if plugin_type and plugin_group and (not plugin_code):
                if plugin_type not in get_types_for_plugin_group(self.session, plugin_group):
                    raise tornado.web.HTTPError(400)
                filter_data.update({"plugin_type": plugin_type, "plugin_group": plugin_group})
            if plugin_type and plugin_group and plugin_code:
                if plugin_type not in get_types_for_plugin_group(self.session, plugin_group):
                    raise tornado.web.HTTPError(400)
                filter_data.update({
                    "plugin_type": plugin_type,
                    "plugin_group": plugin_group,
                    "plugin_code": plugin_code
                })
            results = get_all_poutputs(self.session, filter_data, target_id=int(target_id), inc_output=True)
            if results:
                self.write(results)
            else:
                raise tornado.web.HTTPError(400)

        except exceptions.InvalidTargetReference as e:
            logging.warn(e.parameter)
            raise tornado.web.HTTPError(400)
        except exceptions.InvalidParameterType as e:
            logging.warn(e.parameter)
            raise tornado.web.HTTPError(400)

    def post(self, target_url):
        raise tornado.web.HTTPError(405)

    def put(self):
        raise tornado.web.HTTPError(405)

    def patch(self, target_id=None, plugin_group=None, plugin_type=None, plugin_code=None):
        try:
            if (not target_id) or (not plugin_group) or (not plugin_type) or (not plugin_code):
                raise tornado.web.HTTPError(400)
            else:
                patch_data = dict(self.request.arguments)
                update_poutput(self.session, plugin_group, plugin_type, plugin_code, patch_data, target_id=target_id)
        except exceptions.InvalidTargetReference as e:
            logging.warn(e.parameter)
            raise tornado.web.HTTPError(400)
        except exceptions.InvalidParameterType as e:
            logging.warn(e.parameter)
            raise tornado.web.HTTPError(400)

    def delete(self, target_id=None, plugin_group=None, plugin_type=None, plugin_code=None):
        try:
            filter_data = dict(self.request.arguments)
            if not plugin_group:  # First check if plugin_group is present in url
                delete_all_poutput(self.session, filter_data, target_id=int(target_id))
            if plugin_group and (not plugin_type):
                filter_data.update({"plugin_group": plugin_group})
                delete_all_poutput(self.session, filter_data, target_id=int(target_id))
            if plugin_type and plugin_group and (not plugin_code):
                if plugin_type not in get_types_for_plugin_group(self.session, plugin_group):
                    raise tornado.web.HTTPError(400)
                filter_data.update({"plugin_type": plugin_type, "plugin_group": plugin_group})
                delete_all_poutput(self.session, filter_data, target_id=int(target_id))
            if plugin_type and plugin_group and plugin_code:
                if plugin_type not in get_types_for_plugin_group(self.session, plugin_group):
                    raise tornado.web.HTTPError(400)
                filter_data.update({
                    "plugin_type": plugin_type,
                    "plugin_group": plugin_group,
                    "plugin_code": plugin_code
                })
                delete_all_poutput(self.session, filter_data, target_id=int(target_id))
        except exceptions.InvalidTargetReference as e:
            logging.warn(e.parameter)
            raise tornado.web.HTTPError(400)
        except exceptions.InvalidParameterType as e:
            logging.warn(e.parameter)
            raise tornado.web.HTTPError(400)
