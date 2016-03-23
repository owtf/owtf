import os
import tornado.gen
import tornado.web
import tornado.httpclient
from BaseHTTPServer import BaseHTTPRequestHandler
from StringIO import StringIO
import json
from framework.lib import exceptions
from framework.utils import print_version
from framework.lib.exceptions import InvalidTargetReference
from framework.lib.general import cprint
from framework.interface import custom_handlers


class PluginDataHandler(custom_handlers.APIRequestHandler):
    SUPPORTED_METHODS = ['GET']
    #TODO: Creation of user plugins

    def get(self, plugin_group=None, plugin_type=None, plugin_code=None):
        try:
            filter_data = dict(self.request.arguments)
            if not plugin_group:  # Check if plugin_group is present in url
                self.write(self.get_component("db_plugin").GetAll(filter_data))
            if plugin_group and (not plugin_type) and (not plugin_code):
                filter_data.update({"group": plugin_group})
                self.write(self.get_component("db_plugin").GetAll(filter_data))
            if plugin_group and plugin_type and (not plugin_code):
                if plugin_type not in self.get_component("db_plugin").GetTypesForGroup(plugin_group):
                    raise tornado.web.HTTPError(400)
                filter_data.update({"type": plugin_type, "group": plugin_group})
                self.write(self.get_component("db_plugin").GetAll(filter_data))
            if plugin_group and plugin_type and plugin_code:
                if plugin_type not in self.get_component("db_plugin").GetTypesForGroup(plugin_group):
                    raise tornado.web.HTTPError(400)
                filter_data.update({"type": plugin_type, "group": plugin_group, "code": plugin_code})
                results = self.get_component("db_plugin").GetAll(filter_data)  # This combination will be unique, so have to return a dict
                if results:
                    self.write(results[0])
                else:
                    raise tornado.web.HTTPError(400)
        except exceptions.InvalidTargetReference as e:
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
                self.write(self.get_component("target").GetTargetConfigs(filter_data))
            else:
                self.write(self.get_component("target").GetTargetConfigForID(target_id))
        except InvalidTargetReference as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)

    def post(self, target_id=None):
        if (target_id) or (not self.get_argument("target_url", default=None)):  # How can one post using an id xD
            raise tornado.web.HTTPError(400)
        try:
            self.get_component("target").AddTargets(
                dict(self.request.arguments)["target_url"])
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
            self.get_component("target").UpdateTarget(patch_data, ID=target_id)
        except InvalidTargetReference as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)

    def delete(self, target_id=None):
        if not target_id:
            raise tornado.web.HTTPError(400)
        try:
            self.get_component("target").DeleteTarget(ID=target_id)
        except InvalidTargetReference as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)


class TargetConfigSearchHandler(custom_handlers.APIRequestHandler):
    SUPPORTED_METHODS = ['GET']

    def get(self):
        try:
            filter_data = dict(self.request.arguments)
            filter_data["search"] = True
            self.write(self.get_component("target").SearchTargetConfigs(
                filter_data=filter_data))
        except exceptions.InvalidParameterType as e:
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
        if session_id is not None or \
           self.get_argument("name", None) is None or \
           action is not None:
            # Not supposed to post on specific session
            raise tornado.web.HTTPError(400)
        try:
            self.get_component("session_db").add_session(
                self.get_argument("name"))
            self.set_status(201)  # Stands for "201 Created"
        except exceptions.DBIntegrityException:
            raise tornado.web.HTTPError(409)

    def patch(self, session_id=None, action=None):
        target_id = self.get_argument("target_id", None)
        if session_id is None or \
           (target_id is None and action in ["add", "remove"]):
            raise tornado.web.HTTPError(400)
        try:
            if action == "add":
                self.get_component("session_db").add_target_to_session(
                    int(self.get_argument("target_id")),
                    session_id=int(session_id))
            elif action == "remove":
                self.get_component("session_db").remove_target_from_session(
                    int(self.get_argument("target_id")),
                    session_id=int(session_id))
            elif action == "activate":
                self.get_component("session_db").set_session(
                    int(session_id))
        except exceptions.InvalidTargetReference:
            raise tornado.web.HTTPError(400)
        except exceptions.InvalidSessionReference:
            raise tornado.web.HTTPError(400)

    def delete(self, session_id=None, action=None):
        if session_id is None or \
           action is not None:
            raise tornado.web.HTTPError(400)
        try:
            self.get_component("session_db").delete_session(
                int(session_id))
        except exceptions.InvalidSessionReference:
            raise tornado.web.HTTPError(400)


class SessionsDataHandler(custom_handlers.APIRequestHandler):
    SUPPORTED_METHODS = ['GET']

    def get(self, target_id=None):
        try:
            # gets the session_data for the target
            self.write(self.get_component("transaction").GetSessionData(target_id=int(target_id)))
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


class ZestScriptHandler(custom_handlers.APIRequestHandler):
    SUPPORTED_METHODS = ['GET', 'POST']

    def get(self, target_id=None, transaction_id=None):  # get handles zest consoles functions
        if not target_id:  # does not make sense if no target id provided
            raise tornado.web.HTTPError(400)
        try:
            args = self.request.arguments
            if(not any(args)):  # check if arguments is empty then load zest console
                target_scripts, record_scripts = self.get_component("zest").GetAllScripts(target_id)
                tdict = {}
                tdict["target_scripts"] = target_scripts
                tdict["recorded_scripts"] = record_scripts
                self.write(tdict)
            elif 'script' in args and 'record' in args and 'run' not in args:  # get zest script content
                if args['record'][0] == "true":  # record script
                    content = self.get_component("zest").GetRecordScriptContent(args['script'][0])
                else:  # target script
                    content = self.get_component("zest").GetTargetScriptContent(target_id, args['script'][0])
                self.write({"content": content})
            elif 'script' in args and 'record'in args and 'run' in args:  # runner handling
                if args['run'][0] == "true":
                    if args['record'][0] == "true":  # run record script
                        result = self.get_component("zest").RunRecordScript(args['script'][0])
                    else:  # run target script
                        result = self.get_component("zest").RunTargetScript(target_id, args['script'][0])
                    self.write({"result": result})
            else:
                if 'script' not in args and 'record' in args:  # Recorder handling
                    if args['record'][0] == "true" and 'file' in args:
                        if not self.get_component("zest").StartRecorder(args['file'][0]):
                            self.write({"exists": "true"})
                    else:
                        self.get_component("zest").StopRecorder()
        except exceptions.InvalidTargetReference as e:
                cprint(e.parameter)
                raise tornado.web.HTTPError(400)

# all script creation requests are post methods, Zest class instance then handles the script creation part

    def post(self, target_id=None, transaction_id=None):  # handles actual zest script creation
            if not target_id:  # does not make sense if no target id provided
                raise tornado.web.HTTPError(400)
            try:
                if transaction_id:
                    Scr_Name = self.get_argument('name', '')
                    if not self.get_component("zest").TargetScriptFromSingleTransaction(transaction_id,Scr_Name,target_id): #zest script creation from single transaction
                        self.write({"exists": "true"})
                else:  # multiple transactions
                    trans_list = self.get_argument('trans', '')   # get transaction ids
                    Scr_Name = self.get_argument('name', '')  # get script name
                    transactions = json.loads(trans_list)  # convert to string from json
                    if not self.get_component("zest").TargetScriptFromMultipleTransactions(target_id, Scr_Name, transactions): #zest script creation from multiple transactions
                        self.write({"exists": "true"})
            except exceptions.InvalidTargetReference as e:
                cprint(e.parameter)
                raise tornado.web.HTTPError(400)

    @tornado.web.asynchronous
    def put(self):
        raise tornado.web.HTTPError(405)

    @tornado.web.asynchronous
    def patch(self):
        raise tornado.web.HTTPError(405)

    @tornado.web.asynchronous
    def delete(self, target_id=None):
        raise tornado.web.HTTPError(405)


class ReplayRequestHandler(custom_handlers.APIRequestHandler):
    SUPPORTED_METHODS = ['POST']

    @tornado.web.asynchronous
    def get(self, target_id=None, transaction_id=None):
        raise tornado.web.HTTPError(405)

    def post(self, target_id=None, transaction_id=None):
        rw_request = self.get_argument("get_req", '')  # get particular request
        parsed_req = HTTPRequest(rw_request)  # parse if its a valid HTTP request
        if(parsed_req.error_code == None):
            replay_headers = self.RemoveIfNoneMatch(parsed_req.headers)
            self.get_component("requester").SetHeaders(replay_headers)  #Set the headers
            trans_obj = self.get_component("requester").Request(parsed_req.path, parsed_req.command)  # make the actual request using requester module
            res_data = {}  # received response body and headers will be saved here
            res_data['STATUS'] = trans_obj.Status
            res_data['HEADERS'] = str(trans_obj.ResponseHeaders)
            res_data['BODY'] = trans_obj.DecodedContent
            self.write(res_data)
        else:
            print "Cannot send the given HTTP Request"
            #send something back to interface to let the user know

    @tornado.web.asynchronous
    def put(self):
        raise tornado.web.HTTPError(405)

    @tornado.web.asynchronous
    def patch(self):
        raise tornado.web.HTTPError(405)  # @UndefinedVariable

    @tornado.web.asynchronous
    def delete(self, target_id=None):
        raise tornado.web.HTTPError(405)  # @UndefinedVariable

    def RemoveIfNoneMatch(self, headers):  # Required to force request and not respond with the cached response
        del headers["If-None-Match"]
        return headers


class HTTPRequest(BaseHTTPRequestHandler):
    # this class parses the raw request and  verifies
    def __init__(self, request_text):
        self.rfile = StringIO(request_text)
        self.raw_requestline = self.rfile.readline()
        self.error_code = self.error_message = None
        self.parse_request()

    def send_error(self, code, message):
        self.error_code = code
        self.error_message = message


class ForwardToZAPHandler(custom_handlers.APIRequestHandler):
    SUPPORTED_METHODS = ['GET']

    def get(self, target_id=None, transaction_id=None):
        try:
            if not transaction_id or not target_id:
                raise tornado.web.HTTPError(400)
            else:
                self.get_component("zap_api").ForwardRequest(target_id, transaction_id)
        except exceptions.InvalidTargetReference as e:
                cprint(e.parameter)
                raise tornado.web.HTTPError(400)


class TransactionDataHandler(custom_handlers.APIRequestHandler):
    SUPPORTED_METHODS = ['GET', 'DELETE']

    def get(self, target_id=None, transaction_id=None):
        try:
            if transaction_id:
                self.write(
                    self.get_component("transaction").GetByIDAsDict(
                        int(transaction_id),
                        target_id=int(target_id)))
            else:
                # Empty criteria ensure all transactions
                filter_data = dict(self.request.arguments)
                self.write(
                    self.get_component("transaction").GetAllAsDicts(
                        filter_data,
                        target_id=int(target_id)))
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
                self.get_component("transaction").DeleteTransaction(int(transaction_id), int(target_id))
            else:
                raise tornado.web.HTTPError(400)
        except exceptions.InvalidTargetReference as e:
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
            self.write(self.get_component("transaction").SearchAll(
                filter_data,
                target_id=int(target_id)))
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
            self.write(self.get_component("url_manager").GetAll(filter_data, target_id=int(target_id)))
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
        #TODO: allow modification of urls from the ui, may be adjusting scope etc.. but i don't understand it's use yet ;)
        raise tornado.web.HTTPError(405)  # @UndefinedVariable

    @tornado.web.asynchronous
    def delete(self, target_id=None):
        #TODO: allow deleting of urls from the ui
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
            self.write(self.get_component("url_manager").SearchAll(
                filter_data,
                target_id=int(target_id)))
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
            if not plugin_group: # First check if plugin_group is present in url
                self.write(self.get_component("plugin_output").GetAll(filter_data, target_id=int(target_id)))
            if plugin_group and (not plugin_type):
                filter_data.update({"plugin_group": plugin_group})
                self.write(self.get_component("plugin_output").GetAll(filter_data, target_id=int(target_id)))
            if plugin_type and plugin_group and (not plugin_code):
                if plugin_type not in self.get_component("db_plugin").GetTypesForGroup(plugin_group):
                    raise tornado.web.HTTPError(400)
                filter_data.update({"plugin_type": plugin_type, "plugin_group": plugin_group})
                self.write(self.get_component("plugin_output").GetAll(filter_data, target_id=int(target_id)))
            if plugin_type and plugin_group and plugin_code:
                if plugin_type not in self.get_component("db_plugin").GetTypesForGroup(plugin_group):
                    raise tornado.web.HTTPError(400)
                filter_data.update({"plugin_type": plugin_type, "plugin_group": plugin_group, "plugin_code": plugin_code})
                results = self.get_component("plugin_output").GetAll(filter_data, target_id=int(target_id))
                if results:
                    self.write(results[0])
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
                self.get_component("plugin_output").Update(plugin_group, plugin_type, plugin_code, patch_data, target_id=target_id)
        except exceptions.InvalidTargetReference as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)
        except exceptions.InvalidParameterType as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)

    def delete(self, target_id=None, plugin_group=None, plugin_type=None, plugin_code=None):
        try:
            filter_data = dict(self.request.arguments)
            if not plugin_group: # First check if plugin_group is present in url
                self.get_component("plugin_output").DeleteAll(filter_data, target_id=int(target_id))
            if plugin_group and (not plugin_type):
                filter_data.update({"plugin_group": plugin_group})
                self.get_component("plugin_output").DeleteAll(filter_data, target_id=int(target_id))
            if plugin_type and plugin_group and (not plugin_code):
                if plugin_type not in self.get_component("db_plugin").GetTypesForGroup(plugin_group):
                    raise tornado.web.HTTPError(400)
                filter_data.update({"plugin_type": plugin_type, "plugin_group": plugin_group})
                self.get_component("plugin_output").DeleteAll(filter_data, target_id=int(target_id))
            if plugin_type and plugin_group and plugin_code:
                if plugin_type not in self.get_component("db_plugin").GetTypesForGroup(plugin_group):
                    raise tornado.web.HTTPError(400)
                filter_data.update({"plugin_type": plugin_type, "plugin_group": plugin_group, "plugin_code": plugin_code})
                self.get_component("plugin_output").DeleteAll(filter_data, target_id=int(target_id))
        except exceptions.InvalidTargetReference as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)
        except exceptions.InvalidParameterType as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)


class ProgressBarHandler(custom_handlers.APIRequestHandler):
    SUPPORTED_METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']

    def get(self):
        try:
            self.write(self.get_component("plugin_output").PluginCountOutput())
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
        self.add_header("Access-Control-Allow-Origin","*")
        self.add_header("Access-Control-Allow-Methods","GET, POST, DELETE")

    def get(self, worker_id=None, action=None):
        if not worker_id:
            self.write(self.get_component("worker_manager").get_worker_details())
        try:
            if worker_id and (not action):
                self.write(self.get_component("worker_manager").get_worker_details(int(worker_id)))
            if worker_id and action:
                if int(worker_id) == 0:
                    getattr(self.get_component("worker_manager"), action + '_all_workers')()
                getattr(self.get_component("worker_manager"), action + '_worker')(int(worker_id))
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
            plugin_list = self.get_component("db_plugin").GetAll(filter_data)
            target_list = self.get_component("target").GetTargetConfigs(filter_data)
            if (not plugin_list) or (not target_list):
                raise tornado.web.HTTPError(400)
            self.get_component("worklist_manager").add_work(
                target_list,
                plugin_list,
                force_overwrite=self.get_component("config").ConvertStrToBool(
                    self.get_argument("force_overwrite", "False"))
            )
            self.set_status(201)
        except exceptions.InvalidTargetReference as e:
            raise tornado.web.HTTPError(400)
        except exceptions.InvalidParameterType as e:
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
        except exceptions.InvalidTargetReference as e:
            raise tornado.web.HTTPError(400)
        except exceptions.InvalidParameterType as e:
            raise tornado.web.HTTPError(400)
        except exceptions.InvalidWorkReference as e:
            raise tornado.web.HTTPError(400)

    def patch(self, work_id=None, action=None):
        if work_id is None or action is None:
            tornado.web.HTTPError(400)
        try:
            work_id = int(work_id)
            if work_id != 0:  # 0 is like broadcast address
                if action == 'resume':
                    self.get_component("db").Worklist.patch_work(
                        work_id, active=True)
                elif action == 'pause':
                    self.get_component("db").Worklist.patch_work(
                        work_id, active=False)
            else:
                if action == 'pause':
                    self.get_component("worklist_manager").pause_all()
                elif action == 'resume':
                    self.get_component("worklist_manager").resume_all()
        except exceptions.InvalidWorkReference as e:
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
        self.write(self.get_component("db_config").GetAll(filter_data))

    def patch(self):
        for key, value_list in self.request.arguments.items():
            try:
                self.get_component("db_config").Update(key, value_list[0])
            except exceptions.InvalidConfigurationReference:
                raise tornado.web.HTTPError(400)


class ErrorDataHandler(custom_handlers.APIRequestHandler):
    SUPPORTED_METHODS = ('GET', 'PATCH', 'DELETE')

    def get(self, error_id=None):
        if error_id is None:
            filter_data = dict(self.request.arguments)
            self.write(self.get_component("db_error").GetAll(filter_data))
        else:
            try:
                self.write(self.get_component("db_error").Get(error_id))
            except exceptions.InvalidErrorReference:
                raise tornado.web.HTTPError(400)

    def patch(self, error_id=None):
        if error_id is None:
            raise tornado.web.HTTPError(400)
        if self.request.arguments.get_argument("user_message", default=None):
            raise tornado.web.HTTPError(400)
        self.get_component("db_error").Update(
            error_id,
            self.request.arguments.get_argument("user_message"))

    def delete(self, error_id=None):
        if error_id is None:
            raise tornado.web.HTTPError(400)
        try:
            self.get_component("db_error").Delete(error_id)
        except exceptions.InvalidErrorReference:
            raise tornado.web.HTTPError(400)


class PlugnhackHandler(custom_handlers.APIRequestHandler):
    """
    API handler for Plug-n-Hack. Purpose of this handler is to catch
    parameters defining actions (or/and) state that were sent from Plug-n-Hack
    commands invoked in browser, validate them, then send to proxy Plug-n-Hack
    Handler that will process received information and take action corresponding to received information (i.e inject probe into a target, start/stop monitor a target)
    """
    SUPPORTED_METHODS = ['POST']
    # PnH API Handler must accept and send only an action that is a member of VALID_ACTIONS group
    VALID_ACTIONS = ["probe","monitor","oracle","startMonitoring","stopMonitoring"]

    def post(self):
        # Extract useful information from POST request and store it as a dictionary data structure
        self.message = dict(self.request.arguments)
        # Extract value of url, action and state request parameters from request body
        # Request parameters values by default is []
        self.url = self.get_body_argument("url", default=[])
        self.action = self.get_body_argument("action", default=[])
        self.state = self.get_body_argument("state", default=[])

        # Validate url parameter
        try:
            if not self.url:
                pass
            elif self.get_component("url_manager").IsURL(self.url):
                pass
            else:
                raise exceptions.InvalidUrlReference(400)
        except exceptions.InvalidUrlReference:
            raise tornado.web.HTTPError(400, "exceptions.Invalid URL")
        # Validate action parameter
        try:
            if (self.action in self.VALID_ACTIONS) or (not self.action):
                pass
            else:
                raise exceptions.InvalidActionReference(400)
        except exceptions.InvalidActionReference:
            raise tornado.web.HTTPError(400, "exceptions.Invalid action")
        # Validate state parameter
        try:
            if (self.state == "on") or (self.state == "off") or (not self.state):
                pass
            else:
                raise exceptions.InvalidActionReference(400)
        except exceptions.InvalidActionReference:
            raise tornado.web.HTTPError(400, "exceptions.Invalid action state")
        # If received message is valid, send it to proxy PnH Handler and log this event
        try:
            if not self.message:
                raise exceptions.InvalidMessageReference
            else:
                # TO DO: send message to proxy handler and verify if event registered in log file
                self.application.Core.write_event(json.dumps(self.message), 'a')
        except exceptions.InvalidMessageReference:
            raise tornado.web.HTTPError(412, "Empty message")
        except IOError as e:
            cprint("\n")
            cprint("I/O error at event writing: ({0}): {1}".format(e.errno, e.strerror))
            cprint("\n")


class AutoUpdaterHandler(custom_handlers.APIRequestHandler):
    """
    Notify on the home page if the repo is at its latest commit from upstream
    """
    SUPPORTED_METHODS = ['GET']

    @tornado.gen.coroutine
    def get(self):
        client = tornado.httpclient.AsyncHTTPClient()
        response = yield client.fetch("https://api.github.com/repos/owtf/owtf/commits/develop",
                                  user_agent='OWTF')

        info = json.loads(response.body)
        root_dir = self.get_component("config").RootDir

        # now compare the commit_hash with the latest tag
        if print_version(root_dir, commit_hash=True) != info["sha"]:
            self.write("Seems that your repository is older than the upstream. The lastest commit is \
                from"+info["commit"]["message"]+". \nPlease update, it may resolve some issues!")
        else:
            self.write('Seems like you are running latest version. Happy Pwning!')
