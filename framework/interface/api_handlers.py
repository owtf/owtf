from framework.lib.general import cprint
from framework.lib import general
from framework.interface import custom_handlers
import tornado.web
import subprocess,os




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
    SUPPORTED_METHODS = ['GET']

    def get(self, target_id=None, transaction_id=None):

        response = self.application.Core.DB.Transaction.GetByIDAsDict(int(transaction_id), target_id= int(target_id))
        self.Output_Dir = self.application.Core.DB.Target.PathConfig['URL_OUTPUT']
        self.Raw_Request = response['raw_request']
        self.Res_Headers = response['response_headers']
        self.Res_Body = response['response_body']
        self.Res_status = response['response_status']
        self.Root_Dir = self.application.Core.Config.RootDir
        self.Script_Path = self.Root_Dir + "/zest/zest.sh"
        self.SanitizeArgForCommandline()
        proc = subprocess.call(['sh', self.Script_Path,self.Output_Dir, self.Raw_Request, self.Res_Headers, self.Res_Body,self.Root_Dir])
        #stdout=subprocess.PIPE,stdin=subprocess.PIPE, stderr=subprocess.PIPE)

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

    def SanitizeArgForCommandline(self):
        self.Output_Dir = self.AddQuotes(self.Output_Dir)
        self.Raw_Request = self.AddQuotes(self.Raw_Request)
        self.Res_Headers = self.Res_status + self.Res_Headers
        self.Res_Headers = self.AddQuotes(self.Res_Headers)
        self.Res_Body = self.EscapeForQuotes(self.Res_Body)
        self.Res_Body = self.AddQuotes(self.Res_Body)

    def AddQuotes(self, content):
        content = '"' + content + '"'
        return content

    def EscapeForQuotes(self, content):
        content.replace('"', '\"')
        return content


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
