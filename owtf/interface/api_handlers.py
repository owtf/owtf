"""
owtf.interface.api_handlers
~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""

import collections
from time import gmtime, strftime
from collections import defaultdict

import tornado.gen
import tornado.web
import tornado.httpclient

from owtf.lib import exceptions
from owtf.constants import RANKS
from owtf.lib.general import cprint
from owtf.interface import custom_handlers
from owtf.lib.exceptions import InvalidTargetReference


class PluginDataHandler(custom_handlers.APIRequestHandler):
    SUPPORTED_METHODS = ['GET']
    # TODO: Creation of user plugins

    def get(self, plugin_group=None, plugin_type=None, plugin_code=None):
        try:
            filter_data = dict(self.request.arguments)
            if not plugin_group:  # Check if plugin_group is present in url
                self.write(self.get_component("db_plugin").get_all(filter_data))
            if plugin_group and (not plugin_type) and (not plugin_code):
                filter_data.update({"group": plugin_group})
                self.write(self.get_component("db_plugin").get_all(filter_data))
            if plugin_group and plugin_type and (not plugin_code):
                if plugin_type not in self.get_component("db_plugin").get_types_for_plugin_group(plugin_group):
                    raise tornado.web.HTTPError(400)
                filter_data.update({"type": plugin_type, "group": plugin_group})
                self.write(self.get_component("db_plugin").get_all(filter_data))
            if plugin_group and plugin_type and plugin_code:
                if plugin_type not in self.get_component("db_plugin").get_types_for_plugin_group(plugin_group):
                    raise tornado.web.HTTPError(400)
                filter_data.update({"type": plugin_type, "group": plugin_group, "code": plugin_code})
                # This combination will be unique, so have to return a dict
                results = self.get_component("db_plugin").get_all(filter_data)
                if results:
                    self.write(results[0])
                else:
                    raise tornado.web.HTTPError(400)
        except exceptions.InvalidTargetReference as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)


class PluginNameOutput(custom_handlers.APIRequestHandler):
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
            results = self.get_component("plugin_output").get_all(filter_data, target_id=int(target_id), inc_output=False)

            # Get mappings
            mappings = self.get_component("mapping_db").get_all_mappings()

            # Get test groups as well, for names and info links
            groups = {}
            for group in self.get_component("db_plugin").get_all_test_groups():
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
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)
        except exceptions.InvalidParameterType as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)


class TargetConfigHandler(custom_handlers.APIRequestHandler):
    SUPPORTED_METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']

    def get(self, target_id=None):
        try:
            # If no target_id, means /target is accessed with or without filters
            if not target_id:
                # Get all filter data here, so that it can be passed
                filter_data = dict(self.request.arguments)
                self.write(self.get_component("target").get_target_config_dicts(filter_data))
            else:
                self.write(self.get_component("target").get_target_config_by_id(target_id))
        except InvalidTargetReference as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)

    def post(self, target_id=None):
        if (target_id) or (not self.get_argument("target_url", default=None)):  # How can one post using an id xD
            raise tornado.web.HTTPError(400)
        try:
            self.get_component("target").add_targets(dict(self.request.arguments)["target_url"])
            self.set_status(201)  # Stands for "201 Created"
        except exceptions.DBIntegrityException as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(409)
        except exceptions.UnresolvableTargetException as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(409)

    def put(self, target_id=None):
        return self.patch(target_id)

    def patch(self, target_id=None):
        if not target_id or not self.request.arguments:
            raise tornado.web.HTTPError(400)
        try:
            patch_data = dict(self.request.arguments)
            self.get_component("target").update_target(patch_data, ID=target_id)
        except InvalidTargetReference as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)

    def delete(self, target_id=None):
        if not target_id:
            raise tornado.web.HTTPError(400)
        try:
            self.get_component("target").delete_target(ID=target_id)
        except InvalidTargetReference as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)


class TargetConfigSearchHandler(custom_handlers.APIRequestHandler):
    SUPPORTED_METHODS = ['GET']

    def get(self):
        try:
            filter_data = dict(self.request.arguments)
            filter_data["search"] = True
            self.write(self.get_component("target").search_target_configs(filter_data=filter_data))
        except exceptions.InvalidParameterType:
            raise tornado.web.HTTPError(400)


class TargetSeverityChartHandler(custom_handlers.APIRequestHandler):
    SUPPORTED_METHODS = ['GET']

    def get(self):
        try:
            self.write(self.get_component("target").get_targets_by_severity_count())
        except exceptions.InvalidParameterType as e:
            raise tornado.web.HTTPError(400)


class DashboardPanelHandler(custom_handlers.APIRequestHandler):
    SUPPORTED_METHODS = ['GET']

    def get(self):
        try:
            self.write(self.get_component("plugin_output").get_severity_freq())
        except exceptions.InvalidParameterType:
            raise tornado.web.HTTPError(400)


class OWTFSessionHandler(custom_handlers.APIRequestHandler):
    SUPPORTED_METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']

    def get(self, session_id=None, action=None):
        if action is not None:  # Action must be there only for put
            raise tornado.web.HTTPError(400)
        if session_id is None:
            filter_data = dict(self.request.arguments)
            self.write(self.get_component("session_db").get_all(filter_data))
        else:
            try:
                self.write(self.get_component("session_db").get(session_id))
            except exceptions.InvalidSessionReference:
                raise tornado.web.HTTPError(400)

    def post(self, session_id=None, action=None):
        if (session_id is not None) or (self.get_argument("name", None) is None) or (action is not None):
            # Not supposed to post on specific session
            raise tornado.web.HTTPError(400)
        try:
            self.get_component("session_db").add_session(self.get_argument("name"))
            self.set_status(201)  # Stands for "201 Created"
        except exceptions.DBIntegrityException:
            raise tornado.web.HTTPError(409)

    def patch(self, session_id=None, action=None):
        target_id = self.get_argument("target_id", None)
        if (session_id is None) or (target_id is None and action in ["add", "remove"]):
            raise tornado.web.HTTPError(400)
        try:
            if action == "add":
                self.get_component("session_db").add_target_to_session(int(self.get_argument("target_id")),
                                                                       session_id=int(session_id))
            elif action == "remove":
                self.get_component("session_db").remove_target_from_session(int(self.get_argument("target_id")),
                                                                            session_id=int(session_id))
            elif action == "activate":
                self.get_component("session_db").set_session(int(session_id))
        except exceptions.InvalidTargetReference:
            raise tornado.web.HTTPError(400)
        except exceptions.InvalidSessionReference:
            raise tornado.web.HTTPError(400)

    def delete(self, session_id=None, action=None):
        if (session_id is None) or action is not None:
            raise tornado.web.HTTPError(400)
        try:
            self.get_component("session_db").delete_session(int(session_id))
        except exceptions.InvalidSessionReference:
            raise tornado.web.HTTPError(400)


class SessionsDataHandler(custom_handlers.APIRequestHandler):
    SUPPORTED_METHODS = ['GET']

    def get(self, target_id=None):
        try:
            # gets the session_data for the target
            self.write(self.get_component("transaction").get_session_data(target_id=int(target_id)))
        except exceptions.InvalidTargetReference as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)
        except exceptions.InvalidTransactionReference as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)
        except exceptions.InvalidParameterType as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)

    def post(self, target_url):
        raise tornado.web.HTTPError(405)

    def put(self):
        raise tornado.web.HTTPError(405)

    def patch(self):
        raise tornado.web.HTTPError(405)


class TransactionDataHandler(custom_handlers.APIRequestHandler):
    SUPPORTED_METHODS = ['GET', 'DELETE']

    def get(self, target_id=None, transaction_id=None):
        try:
            if transaction_id:
                self.write(self.get_component("transaction").get_by_id_as_dict(int(transaction_id),
                                                                               target_id=int(target_id)))
            else:
                # Empty criteria ensure all transactions
                filter_data = dict(self.request.arguments)
                self.write(self.get_component("transaction").get_all_as_dicts(filter_data, target_id=int(target_id)))
        except exceptions.InvalidTargetReference as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)
        except exceptions.InvalidTransactionReference as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)
        except exceptions.InvalidParameterType as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)

    def post(self, target_url):
        raise tornado.web.HTTPError(405)

    def put(self):
        raise tornado.web.HTTPError(405)

    def patch(self):
        raise tornado.web.HTTPError(405)

    def delete(self, target_id=None, transaction_id=None):
        try:
            if transaction_id:
                self.get_component("transaction").delete_transaction(int(transaction_id), int(target_id))
            else:
                raise tornado.web.HTTPError(400)
        except exceptions.InvalidTargetReference as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)


class TransactionHrtHandler(custom_handlers.APIRequestHandler):
    SUPPORTED_METHODS = ['POST']

    def post(self, target_id=None, transaction_id=None):
        try:
            if transaction_id:
                filter_data = dict(self.request.arguments)
                self.write(self.get_component("transaction").get_hrt_response(filter_data, int(transaction_id), target_id=int(target_id)))
            else:
                raise tornado.web.HTTPError(400)
        except (InvalidTargetReference, InvalidTransactionReference, InvalidParameterType) as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)


class TransactionSearchHandler(custom_handlers.APIRequestHandler):
    SUPPORTED_METHODS = ['GET']

    def get(self, target_id=None):
        if not target_id:  # Must be a integer target id
            raise tornado.web.HTTPError(400)
        try:
            # Empty criteria ensure all transactions
            filter_data = dict(self.request.arguments)
            filter_data["search"] = True
            self.write(self.get_component("transaction").search_all(filter_data, target_id=int(target_id)))
        except exceptions.InvalidTargetReference as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)
        except exceptions.InvalidTransactionReference as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)
        except exceptions.InvalidParameterType as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)


class URLDataHandler(custom_handlers.APIRequestHandler):
    SUPPORTED_METHODS = ['GET']

    def get(self, target_id=None):
        try:
            # Empty criteria ensure all transactions
            filter_data = dict(self.request.arguments)
            self.write(self.get_component("url_manager").get_all(filter_data, target_id=int(target_id)))
        except exceptions.InvalidTargetReference as e:
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
        # TODO: allow modification of urls from the ui, may be adjusting scope etc.. but i don't understand
        # it's use yet ;)
        raise tornado.web.HTTPError(405)  # @UndefinedVariable

    @tornado.web.asynchronous
    def delete(self, target_id=None):
        # TODO: allow deleting of urls from the ui
        raise tornado.web.HTTPError(405)  # @UndefinedVariable


class URLSearchHandler(custom_handlers.APIRequestHandler):
    SUPPORTED_METHODS = ['GET']

    def get(self, target_id=None):
        if not target_id:  # Must be a integer target id
            raise tornado.web.HTTPError(400)
        try:
            # Empty criteria ensure all transactions
            filter_data = dict(self.request.arguments)
            filter_data["search"] = True
            self.write(self.get_component("url_manager").search_all(filter_data, target_id=int(target_id)))
        except exceptions.InvalidTargetReference as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)
        except exceptions.InvalidParameterType as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)


class PluginOutputHandler(custom_handlers.APIRequestHandler):
    SUPPORTED_METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']

    def get(self, target_id=None, plugin_group=None, plugin_type=None, plugin_code=None):
        try:
            filter_data = dict(self.request.arguments)
            if plugin_group and (not plugin_type):
                filter_data.update({"plugin_group": plugin_group})
            if plugin_type and plugin_group and (not plugin_code):
                if plugin_type not in self.get_component("db_plugin").get_types_for_plugin_group(plugin_group):
                    raise tornado.web.HTTPError(400)
                filter_data.update({"plugin_type": plugin_type, "plugin_group": plugin_group})
            if plugin_type and plugin_group and plugin_code:
                if plugin_type not in self.get_component("db_plugin").get_types_for_plugin_group(plugin_group):
                    raise tornado.web.HTTPError(400)
                filter_data.update({
                    "plugin_type": plugin_type,
                    "plugin_group": plugin_group,
                    "plugin_code": plugin_code
                })
            results = self.get_component("plugin_output").get_all(filter_data, target_id=int(target_id), inc_output=True)
            if results:
                self.write(results)
            else:
                raise tornado.web.HTTPError(400)

        except exceptions.InvalidTargetReference as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)
        except exceptions.InvalidParameterType as e:
            cprint(e.parameter)
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
                self.get_component("plugin_output").update(plugin_group, plugin_type, plugin_code, patch_data,
                                                           target_id=target_id)
        except exceptions.InvalidTargetReference as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)
        except exceptions.InvalidParameterType as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)

    def delete(self, target_id=None, plugin_group=None, plugin_type=None, plugin_code=None):
        try:
            filter_data = dict(self.request.arguments)
            if not plugin_group:  # First check if plugin_group is present in url
                self.get_component("plugin_output").delete_all(filter_data, target_id=int(target_id))
            if plugin_group and (not plugin_type):
                filter_data.update({"plugin_group": plugin_group})
                self.get_component("plugin_output").delete_all(filter_data, target_id=int(target_id))
            if plugin_type and plugin_group and (not plugin_code):
                if plugin_type not in self.get_component("db_plugin").get_types_for_plugin_group(plugin_group):
                    raise tornado.web.HTTPError(400)
                filter_data.update({"plugin_type": plugin_type, "plugin_group": plugin_group})
                self.get_component("plugin_output").delete_all(filter_data, target_id=int(target_id))
            if plugin_type and plugin_group and plugin_code:
                if plugin_type not in self.get_component("db_plugin").get_types_for_plugin_group(plugin_group):
                    raise tornado.web.HTTPError(400)
                filter_data.update({
                    "plugin_type": plugin_type,
                    "plugin_group": plugin_group,
                    "plugin_code": plugin_code
                })
                self.get_component("plugin_output").delete_all(filter_data, target_id=int(target_id))
        except exceptions.InvalidTargetReference as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)
        except exceptions.InvalidParameterType as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)


class ProgressBarHandler(custom_handlers.APIRequestHandler):
    SUPPORTED_METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']

    def set_default_headers(self):
        self.add_header("Access-Control-Allow-Origin", "*")
        self.add_header("Access-Control-Allow-Methods", "GET, POST, DELETE")

    def get(self):
        try:
            self.write(self.get_component("plugin_output").plugin_count_output())
        except exceptions.InvalidParameterType as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)

    def post(self):
        raise tornado.web.HTTPError(405)

    def put(self):
        raise tornado.web.HTTPError(405)

    def patch(self):
        raise tornado.web.HTTPError(405)

    def delete(self):
        raise tornado.web.HTTPError(405)


class WorkerHandler(custom_handlers.APIRequestHandler):
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


class WorklistHandler(custom_handlers.APIRequestHandler):
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


class WorklistSearchHandler(custom_handlers.APIRequestHandler):
    SUPPORTED_METHODS = ['GET']

    def get(self):
        try:
            criteria = dict(self.request.arguments)
            criteria["search"] = True
            self.write(self.get_component("worklist_manager").search_all(criteria))
        except exceptions.InvalidParameterType:
            raise tornado.web.HTTPError(400)


class ConfigurationHandler(custom_handlers.APIRequestHandler):
    SUPPORTED_METHODS = ('GET', 'PATCH')

    def get(self):
        filter_data = dict(self.request.arguments)
        self.write(self.get_component("db_config").get_all(filter_data))

    def patch(self):
        for key, value_list in list(self.request.arguments.items()):
            try:
                self.get_component("db_config").update(key, value_list[0])
            except exceptions.InvalidConfigurationReference:
                raise tornado.web.HTTPError(400)


class ErrorDataHandler(custom_handlers.APIRequestHandler):
    SUPPORTED_METHODS = ['GET', 'POST', 'DELETE', 'PATCH']

    def get(self, error_id=None):
        if error_id is None:
            filter_data = dict(self.request.arguments)
            self.write(self.get_component("db_error").get_all(filter_data))
        else:
            try:
                self.write(self.get_component("db_error").get(error_id))
            except exceptions.InvalidErrorReference:
                raise tornado.web.HTTPError(400)

    def post(self, error_id=None):
        if error_id is None:
            try:
                filter_data = dict(self.request.arguments)
                username = filter_data['username'][0]
                title = filter_data['title'][0]
                body = filter_data['body'][0]
                id = int(filter_data['id'][0])
                self.write(self.get_component("error_handler").add_github_issue(username, title, body, id))
            except:
                raise tornado.web.HTTPError(400)
        else:
            raise tornado.web.HTTPError(400)

    def patch(self, error_id=None):
        if error_id is None:
            raise tornado.web.HTTPError(400)
        if self.request.arguments.get_argument("user_message", default=None):
            raise tornado.web.HTTPError(400)
        self.get_component("db_error").update(error_id, self.request.arguments.get_argument("user_message"))

    def delete(self, error_id=None):
        if error_id is None:
            raise tornado.web.HTTPError(400)
        try:
            self.get_component("db_error").delete(error_id)
        except exceptions.InvalidErrorReference:
            raise tornado.web.HTTPError(400)


class ReportExportHandler(custom_handlers.APIRequestHandler):
    """
    Class handling API methods related to export report funtionality.
    This API returns all information about a target scan present in OWTF.
    :raise InvalidTargetReference: If target doesn't exists.
    :raise InvalidParameterType: If some unknown parameter in `filter_data`.
    """
    # TODO: Add API documentation.

    SUPPORTED_METHODS = ['GET']

    def get(self, target_id=None):
        """
        REST API - /api/targets/<target_id>/export/ returns JSON(data) for template.
        """
        if not target_id:
            raise tornado.web.HTTPError(400)
        try:
            filter_data = dict(self.request.arguments)
            plugin_outputs = self.get_component("plugin_output").get_all(filter_data, target_id=target_id, inc_output=True)
        except exceptions.InvalidTargetReference as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)
        except exceptions.InvalidParameterType as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)
        # Group the plugin outputs to make it easier in template
        grouped_plugin_outputs = defaultdict(list)
        for output in plugin_outputs:
            output['rank'] = RANKS.get(max(output['user_rank'], output['owtf_rank']))
            grouped_plugin_outputs[output['plugin_code']].append(output)

        # Needed ordered list for ease in templates
        grouped_plugin_outputs = collections.OrderedDict(sorted(grouped_plugin_outputs.items()))

        # Get mappings
        mappings = self.get_argument("mapping", None)
        if mappings:
            mappings = self.get_component("mapping_db").get_mappings(mappings)

        # Get test groups as well, for names and info links
        test_groups = {}
        for test_group in self.get_component("db_plugin").get_all_test_groups():
            test_group["mapped_code"] = test_group["code"]
            test_group["mapped_descrip"] = test_group["descrip"]
            if mappings and test_group['code'] in mappings:
                code, description = mappings[test_group['code']]
                test_group["mapped_code"] = code
                test_group["mapped_descrip"] = description
            test_groups[test_group['code']] = test_group

        vulnerabilities = []
        for key, value in list(grouped_plugin_outputs.items()):
            test_groups[key]["data"] = value
            vulnerabilities.append(test_groups[key])

        result = self.get_component("target").get_target_config_by_id(target_id)
        result["vulnerabilities"] = vulnerabilities
        result["time"] = strftime("%Y-%m-%d %H:%M:%S", gmtime())

        if result:
            self.write(result)
        else:
            raise tornado.web.HTTPError(400)
