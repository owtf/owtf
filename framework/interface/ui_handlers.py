from framework.lib.general import cprint
from framework.lib import general
from framework.interface import custom_handlers
import tornado.web

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
                        poutput_api_url=self.reverse_url('poutput_api_url', target_id, None, None, None),
                        transaction_log_url=self.reverse_url('transaction_log_url', target_id, None),
                        url_log_url=self.reverse_url('url_log_url', target_id)
                        )
