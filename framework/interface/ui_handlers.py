from framework.lib.general import cprint
from framework.lib import general
from framework.interface import custom_handlers
import tornado.web
import collections

class Home(custom_handlers.UIRequestHandler):
    SUPPORTED_METHODS = ['GET']
    def get(self):
        self.render('home.html')

class TransactionLog(custom_handlers.UIRequestHandler):
    SUPPORTED_METHODS = ['GET']
    @tornado.web.asynchronous
    def get(self, target_id=None, transaction_id=None):
        if not target_id:
            raise tornado.web.HTTPError(405)
        if transaction_id:
            self.render("transaction.html",
                        transaction_api_url=self.reverse_url('transactions_api_url', target_id, transaction_id),
                        transaction_log_url=self.reverse_url('transaction_log_url', target_id, None)
                        )
        else:
            self.render("transaction_log.html",
                        transactions_api_url=self.reverse_url('transactions_api_url', target_id, None),
                        transaction_log_url=self.reverse_url('transaction_log_url', target_id, None)
                        )

class UrlLog(custom_handlers.UIRequestHandler):
    SUPPORTED_METHODS = ['GET']
    @tornado.web.asynchronous
    def get(self, target_id=None):
        if not target_id:
            raise tornado.web.HTTPError(405)
        self.render("url_log.html",
                    urls_api_url=self.reverse_url('urls_api_url', target_id),
                    transaction_log_url=self.reverse_url('transaction_log_url', target_id, None)
                    )

class TargetManager(custom_handlers.UIRequestHandler):
    SUPPORTED_METHODS = ['GET']
    @tornado.web.asynchronous
    def get(self, target_id=None):
        if not target_id:
            self.render("target_manager.html",
                        targets_api_url=self.reverse_url('targets_api_url', None),
                        targets_ui_url=self.reverse_url('targets_ui_url', None)
                        )
        else:
            self.render("target.html",
                        target_api_url=self.reverse_url('targets_api_url', target_id),
                        targets_ui_url=self.reverse_url('targets_ui_url', None),
                        poutput_ui_url=self.reverse_url('poutput_ui_url', target_id),
                        poutput_api_url=self.reverse_url('poutput_api_url', target_id, None, None, None),
                        plugins_api_url=self.reverse_url('plugins_api_url', None, None, None),
                        worklist_api_url=self.reverse_url('worklist_api_url'),
                        transaction_log_url=self.reverse_url('transaction_log_url', target_id, None),
                        url_log_url=self.reverse_url('url_log_url', target_id)
                       )

class PluginOutput(custom_handlers.UIRequestHandler):
    SUPPORTED_METHODS = ['GET']
    @tornado.web.asynchronous
    def get(self, target_id=None):
        if not target_id:
            raise tornado.web.HTTPError(400)
        try:
            filter_data = dict(self.request.arguments)
            plugin_outputs = self.application.Core.DB.POutput.GetAll(filter_data, target_id)
            grouped_plugin_outputs = {}
            for poutput in plugin_outputs:
                if not grouped_plugin_outputs.get(poutput['plugin_code'], None):
                    grouped_plugin_outputs[poutput['plugin_code']] = [] # No problem of overwriting
                grouped_plugin_outputs[poutput['plugin_code']].append(poutput)
            grouped_plugin_outputs = collections.OrderedDict(sorted(grouped_plugin_outputs.items()))
            self.render("plugin_report.html",
                        grouped_plugin_outputs=grouped_plugin_outputs,
                        poutput_api_url=self.reverse_url('poutput_api_url', target_id, None, None, None),
                        transaction_log_url=self.reverse_url('transaction_log_url', target_id, None),
                        url_log_url=self.reverse_url('url_log_url', target_id)
                        )
        except general.InvalidTargetReference as e:
            raise tornado.web.HTTPError(400)
