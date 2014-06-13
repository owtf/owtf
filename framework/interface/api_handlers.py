from framework.lib.general import cprint
from framework.lib import general
from framework.interface import custom_handlers
from framework import zest
from framework.http import requester
import tornado.web
import simplejson as json
from BaseHTTPServer import BaseHTTPRequestHandler
from StringIO import StringIO


class PluginDataHandler(custom_handlers.APIRequestHandler):
    SUPPORTED_METHODS = ['GET']
    #TODO: Creation of user plugins

    def get(self, plugin_group=None, plugin_type=None, plugin_code=None):
        try:
            filter_data = dict(self.request.arguments)
            if not plugin_group:  # Check if plugin_group is present in url
                self.write(self.application.Core.DB.Plugin.GetAll(filter_data))
            if plugin_group and (not plugin_type) and (not plugin_code):
                filter_data.update({"group": plugin_group})
                self.write(self.application.Core.DB.Plugin.GetAll(filter_data))
            if plugin_group and plugin_type and (not plugin_code):
                if plugin_type not in self.application.Core.DB.Plugin.GetTypesForGroup(plugin_group):
                    raise tornado.web.HTTPError(400)
                filter_data.update({"type": plugin_type, "group": plugin_group})
                self.write(self.application.Core.DB.Plugin.GetAll(filter_data))
            if plugin_group and plugin_type and plugin_code:
                if plugin_type not in self.application.Core.DB.Plugin.GetTypesForGroup(plugin_group):
                    raise tornado.web.HTTPError(400)
                filter_data.update({"type": plugin_type, "group": plugin_group, "code": plugin_code})
                results = self.application.Core.DB.Plugin.GetAll(filter_data)  # This combination will be unique, so have to return a dict
                if results:
                    self.write(results[0])
                else:
                    raise tornado.web.HTTPError(400)
        except general.InvalidTargetReference as e:
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
                self.write(self.application.Core.DB.Target.GetTargetConfigs(filter_data))
            else:
                self.write(self.application.Core.DB.Target.GetTargetConfigForID(target_id))
        except general.InvalidTargetReference as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)

    def post(self, target_id=None):
        if (target_id) or (not self.get_argument("TARGET_URL", default=None)):  # How can one post using an id xD
            raise tornado.web.HTTPError(400)
        try:
            self.application.Core.DB.Target.AddTarget(str(self.get_argument("TARGET_URL")))
            self.set_status(201)  # Stands for "201 Created"
        except general.DBIntegrityException as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(409)

    def put(self, target_id=None):
        return self.patch(target_id)

    def patch(self, target_id=None):
        if not target_id or not self.request.arguments:
            raise tornado.web.HTTPError(400)
        try:
            patch_data = dict(self.request.arguments)
            self.application.Core.DB.Target.UpdateTarget(patch_data, ID=target_id)
        except general.InvalidTargetReference as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)

    def delete(self, target_id=None):
        if not target_id:
            raise tornado.web.HTTPError(400)
        try:
            self.application.Core.DB.Target.DeleteTarget(ID=target_id)
        except general.InvalidTargetReference as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)


class ZestScriptHandler(custom_handlers.APIRequestHandler):
    SUPPORTED_METHODS = ['GET', 'POST']

    def get(self, target_id=None, transaction_id=None):  # get handles zest consoles functions
        if not target_id:  # does not make sense if no target id provided
                raise tornado.web.HTTPError(400)
        try:
            #self.application.Core.zest = zest.Init(self.application.Core)  # zest instance assigned
            args = self.request.arguments
            if(not any(args)):  # check if arguments is empty then load zest console
                file_list, record_scripts = self.application.Core.zest.GetAllScripts(target_id)
                tdict = {}
                tdict["files"] = file_list
                tdict["recorded_files"] = record_scripts
                self.write(tdict)
            elif 'script' in args and 'record' in args:  # get zest script content
                if args['record'][0] == "true":  # record script
                    content = self.application.Core.zest.GetRecordScriptContent(args['script'][0])
                else:  # target script
                    content = self.application.Core.zest.GetTargetScriptContent(target_id, args['script'][0])
                tdict = {}
                tdict['content'] = content
                self.write(tdict)
            else:
                if 'script' not in args and 'record' in args:  # Recorder handling
                    if args['record'][0] == "true":
                        self.application.Core.zest.StartRecorder()
                    else:
                        self.application.Core.zest.StopRecorder()
        except general.InvalidTargetReference as e:
                cprint(e.parameter)
                raise tornado.web.HTTPError(400)

# all script creation requests are post methods, Zest class instance then handles the script creation part

    def post(self, target_id=None, transaction_id=None):  # handles actual zest script creation
            if not target_id:  # does not make sense if no target id provided
                raise tornado.web.HTTPError(400)
            try:
                if transaction_id:
                    if not self.application.Core.zest.TargetScriptFromSingleTransaction(transaction_id,target_id): #zest script creation from single transaction
                        self.write("file exists")
                else:  # multiple transactions
                    trans_list = self.get_argument('trans', '')   # get transaction ids
                    Scr_Name = self.get_argument('name', '')  # get script name
                    transactions = json.loads(trans_list)  # convert to string from json
                    if not self.application.Core.zest.TargetScriptFromMultipleTransactions(target_id, Scr_Name, transactions): #zest script creation from multiple transactions
                        self.write("file exists")
            except general.InvalidTargetReference as e:
                cprint(e.parameter)
                raise tornado.web.HTTPError(400)

    @tornado.web.asynchronous
    def put(self):
        raise tornado.web.HTTPError(405)

    @tornado.web.asynchronous
    def patch(self):
        raise tornado.web.httperror(405)

    @tornado.web.asynchronous
    def delete(self, target_id=None):
        raise tornado.web.httperror(405)


class ReplayRequestHandler(custom_handlers.APIRequestHandler):
    SUPPORTED_METHODS = {'POST'}

    @tornado.web.asynchronous
    def get(self, target_id=None, transaction_id=None):
        raise tornado.web.HTTPError(405)

    def post(self, target_id=None, transaction_id=None):
        rw_request = self.get_argument("get_req", '')  # get particular request
        parsed_Req = HTTPRequest(rw_request)  # parse if its a valid HTTP request
        if(parsed_Req.error_code == None):
            self.application.Core.Requester.SetHeaders(parsed_Req.headers)  #Set the headers
            trans_obj = self.application.Core.Requester.Request(parsed_Req.path, parsed_Req.command)  # make the actual request using requester module
            Res_data = {}  # received response body and headers will be saved here
            Res_data['Status'] = trans_obj.Status
            Res_data['Headers'] = str(trans_obj.ResponseHeaders)
            Res_data['Body'] = trans_obj.DecodedContent
            self.write(Res_data)
        else:
            print "Cannot send the given HTTP Request" 
            #send something back to interface to let the user know

    @tornado.web.asynchronous
    def put(self):
        raise tornado.web.HTTPError(405)

    @tornado.web.asynchronous
    def patch(self):
        raise tornado.web.httperror(405)  # @UndefinedVariable

    @tornado.web.asynchronous
    def delete(self, target_id=None):
        raise tornado.web.httperror(405)  # @UndefinedVariable


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

"""
    Remove this at the end
    def print_all(self):
        print self.error_code       # None  (check this first)
        print self.command          # "GET"
        print self.path             # "/who/ken/trust.html"
        print self.request_version  # "HTTP/1.1"
        print len(self.headers)     # 3
        print self.headers   # ['accept-charset', 'host', 'accept']
        print self.headers['host']
"""


class TransactionDataHandler(custom_handlers.APIRequestHandler):
    SUPPORTED_METHODS = ['GET', 'DELETE']

    def get(self, target_id=None, transaction_id=None):
        try:
            if transaction_id:
                self.write(self.application.Core.DB.Transaction.GetByIDAsDict(int(transaction_id), target_id=int(target_id)))
            else:
                # Empty criteria ensure all transactions
                filter_data = dict(self.request.arguments)
                self.write(self.application.Core.DB.Transaction.GetAllAsDicts(filter_data, target_id=int(target_id)))
        except general.InvalidTargetReference as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)
        except general.InvalidTransactionReference as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)
        except general.InvalidParameterType as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)

    def post(self, target_url):
        raise tornado.web.HTTPError(405)

    def put(self):
        raise tornado.web.HTTPError(405)

    def patch(self):
        #TODO: Allow modification of transactions from the UI, may be adjusting scope etc.. But I don't understand it's use yet ;)
        raise tornado.web.HTTPError(405)

    def delete(self, target_id=None, transaction_id=None):
        try:
            if transaction_id:
                self.application.Core.DB.Transaction.DeleteTransaction(int(transaction_id), int(target_id))
            else:
                raise tornado.web.HTTPError(400)
        except general.InvalidTargetReference as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)


class URLDataHandler(custom_handlers.APIRequestHandler):
    SUPPORTED_METHODS = ['GET']

    def get(self, target_id=None):
        try:
            # Empty criteria ensure all transactions
            filter_data = dict(self.request.arguments)
            self.write(self.application.Core.DB.URL.GetAll(filter_data, target_id=target_id))
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
        raise tornado.web.httperror(405)  # @UndefinedVariable

    @tornado.web.asynchronous
    def delete(self, target_id=None):
        #TODO: allow deleting of urls from the ui
        raise tornado.web.httperror(405)  # @UndefinedVariable


class PluginOutputHandler(custom_handlers.APIRequestHandler):
    SUPPORTED_METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']

    def get(self, target_id=None, plugin_group=None, plugin_type=None, plugin_code=None):
        try:
            filter_data = dict(self.request.arguments)
            if not plugin_group:  # First check if plugin_group is present in url
                self.write(self.application.Core.DB.POutput.GetAll(filter_data, target_id))
            if plugin_group and (not plugin_type):
                filter_data.update({"plugin_group": plugin_group})
                self.write(self.application.Core.DB.POutput.GetAll(filter_data, target_id))
            if plugin_type and plugin_group and (not plugin_code):
                if plugin_type not in self.application.Core.DB.Plugin.GetTypesForGroup(plugin_group):
                    raise tornado.web.HTTPError(400)
                filter_data.update({"plugin_type": plugin_type, "plugin_group": plugin_group})
                self.write(self.application.Core.DB.POutput.GetAll(filter_data, target_id))
            if plugin_type and plugin_group and plugin_code:
                if plugin_type not in self.application.Core.DB.Plugin.GetTypesForGroup(plugin_group):
                    raise tornado.web.HTTPError(400)
                filter_data.update({"plugin_type": plugin_type, "plugin_group": plugin_group, "plugin_code": plugin_code})
                results = self.application.Core.DB.POutput.GetAll(filter_data, target_id)
                if results:
                    self.write(results[0])
                else:
                    raise tornado.web.HTTPError(400)
        except general.InvalidTargetReference as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)
        except general.InvalidParameterType as e:
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
                self.application.Core.DB.POutput.Update(plugin_group, plugin_type, plugin_code, patch_data, target_id)
        except general.InvalidTargetReference as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)
        except general.InvalidParameterType as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)

    def delete(self, target_id=None, plugin_group=None, plugin_type=None, plugin_code=None):
        try:
            filter_data = dict(self.request.arguments)
            if not plugin_group:  # First check if plugin_group is present in url
                self.application.Core.DB.POutput.DeleteAll(filter_data, target_id)
            if plugin_group and (not plugin_type):
                filter_data.update({"plugin_group": plugin_group})
                self.application.Core.DB.POutput.DeleteAll(filter_data, target_id)
            if plugin_type and plugin_group and (not plugin_code):
                if plugin_type not in self.application.Core.DB.Plugin.GetTypesForGroup(plugin_group):
                    raise tornado.web.HTTPError(400)
                filter_data.update({"plugin_type": plugin_type, "plugin_group": plugin_group})
                self.application.Core.DB.POutput.DeleteAll(filter_data, target_id)
            if plugin_type and plugin_group and plugin_code:
                if plugin_type not in self.application.Core.DB.Plugin.GetTypesForGroup(plugin_group):
                    raise tornado.web.HTTPError(400)
                filter_data.update({"plugin_type": plugin_type, "plugin_group": plugin_group, "plugin_code": plugin_code})
                self.application.Core.DB.POutput.DeleteAll(filter_data, target_id)
        except general.InvalidTargetReference as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)
        except general.InvalidParameterType as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)


class WorkerHandler(custom_handlers.APIRequestHandler):
    SUPPORTED_METHODS = ['GET']

    def get(self, worker_id=None, action=None):
        if not worker_id:
            self.write(self.application.Core.WorkerManager.get_worker_details())
        try:
            if worker_id and (not action):
                self.write(self.application.Core.WorkerManager.get_worker_details(int(worker_id)))
            if worker_id and action:
                getattr(self.application.Core.WorkerManager, action + '_worker')(int(worker_id))
        except general.InvalidWorkerReference as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)


class WorkListHandler(custom_handlers.APIRequestHandler):
    SUPPORTED_METHODS = ['GET', 'POST']

    def get(self):
        self.write(self.application.Core.WorkerManager.get_work_list())

    def post(self):
        try:
            filter_data = dict(self.request.arguments)
            if not filter_data:
                raise tornado.web.HTTPError(400)
            plugin_list = self.application.Core.DB.Plugin.GetAll(filter_data)
            target_list = self.application.Core.DB.Target.GetTargetConfigs(filter_data)
            if (not plugin_list) or (not target_list):
                raise tornado.web.HTTPError(400)
            self.application.Core.WorkerManager.fill_work_list(target_list, plugin_list)
            self.set_status(201)  # TODO: Set proper response code
        except general.InvalidTargetReference as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)
        except general.InvalidParameterType as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)

    def delete(self):
        try:
            filter_data = dict(self.request.arguments)
            plugin_list = self.application.Core.DB.Plugin.GetAll(filter_data)
            target_list = self.application.Core.DB.Target.GetTargetConfigs(filter_data)
            self.application.Core.WorkerManager.filter_work_list(target_list, plugin_list)
        except general.InvalidTargetReference as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)
        except general.InvalidParameterType as e:
            cprint(e.parameter)
            raise tornado.web.HTTPError(400)


class ConfigurationHandler(custom_handlers.APIRequestHandler):
    SUPPORTED_METHODS = ('GET', 'PATCH')

    def get(self):
        filter_data = dict(self.request.arguments)
        self.write(self.application.Core.DB.Config.GetAll(filter_data))

    def patch(self):
        for key, value_list in self.request.arguments.items():
            try:
                self.application.Core.DB.Config.Update(key, value_list[0])
            except general.InvalidConfigurationReference:
                raise tornado.web.HTTPError(400)


class Struct(object):
        def __init__(self, **entries):
            self.__dict__.update(entries)
