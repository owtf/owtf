"""
owtf.api.ui_handlers
~~~~~~~~~~~~~~~~~~~~~~~~~~

.note::
    Not been refactored since this is being deprecated
"""

import json
import collections

import tornado.web
from tornado.escape import url_escape

from owtf.dependency_management.dependency_resolver import ServiceLocator
from owtf.lib.exceptions import InvalidTargetReference, InvalidParameterType
from owtf.api.base import UIRequestHandler


class Redirect(UIRequestHandler):
    SUPPORTED_METHODS = ['GET']

    def get(self):
        self.redirect(self.reverse_url('home_ui_url'))


class Home(UIRequestHandler):
    SUPPORTED_METHODS = ['GET']

    def get(self):
        self.render('home.html')


class Dashboard(UIRequestHandler):
    SUPPORTED_METHODS = ['GET']

    def get(self):
        self.render("dashboard.html")


class TransactionLog(UIRequestHandler):
    SUPPORTED_METHODS = ['GET']

    @tornado.web.asynchronous
    def get(self, target_id=None, transaction_id=None):
        if not target_id:
            raise tornado.web.HTTPError(405)
        if transaction_id:
            self.render(
                "transaction.html",
                transaction_api_url=self.reverse_url('transactions_api_url', target_id, transaction_id),
                transaction_log_url=self.reverse_url('transaction_log_url', target_id, None),
                transaction_replay_url=self.reverse_url('transaction_replay_url', target_id, transaction_id),
                forward_zap_url=self.reverse_url('forward_zap_url', target_id, transaction_id)
            )
        else:
            self.render(
                "transaction_log.html",
                transactions_api_url=self.reverse_url('transactions_api_url', target_id, None),
                transactions_search_api_url=self.reverse_url('transactions_search_api_url', target_id),
                transaction_log_url=self.reverse_url('transaction_log_url', target_id, None),
                zest_console_url=self.reverse_url('zest_console_url', target_id)
            )


class HTTPSessions(UIRequestHandler):
    """ HTTPSessions handles the user sessions. """
    SUPPORTED_METHODS = ['GET']

    @tornado.web.asynchronous
    def get(self, target_id=None):
        if not target_id:
            raise tornado.web.HTTPError(405)
        self.render("sessions_manager.html", sessions_api_url=self.reverse_url('sessions_api_url', target_id),)


class UrlLog(UIRequestHandler):
    SUPPORTED_METHODS = ['GET']

    @tornado.web.asynchronous
    def get(self, target_id=None):
        if not target_id:
            raise tornado.web.HTTPError(405)
        self.render(
            "url_log.html",
            urls_api_url=self.reverse_url('urls_api_url', target_id),
            urls_search_api_url=self.reverse_url('urls_search_api_url', target_id),
            transaction_log_url=self.reverse_url('transaction_log_url', target_id, None)
        )


class TargetManager(UIRequestHandler):
    SUPPORTED_METHODS = ['GET']

    @tornado.web.asynchronous
    def get(self, target_id=None):
        if not target_id:
            self.render(
                "target_manager.html",
                owtf_sessions_api_url=self.reverse_url('owtf_sessions_api_url', None, None),
                targets_api_url=self.reverse_url('targets_api_url', None),
                targets_search_api_url=self.reverse_url('targets_search_api_url'),
                targets_ui_url=self.reverse_url('targets_ui_url', None),
                plugins_api_url=self.reverse_url('plugins_api_url', None, None, None),
                worklist_api_url=self.reverse_url('worklist_api_url', None, None)
            )
        else:
            adv_filter_data = self.get_component("plugin_output").get_unique(target_id=int(target_id))
            adv_filter_data["mapping"] = self.get_component("mapping_db").get_mapping_types()
            self.render(
                "target.html",
                target_id=target_id,
                target_api_url=self.reverse_url('targets_api_url', target_id),
                targets_ui_url=self.reverse_url('targets_ui_url', None),
                poutput_ui_url=self.reverse_url('poutput_ui_url', target_id),
                adv_filter_data=json.dumps(adv_filter_data),
                plugins_api_url=self.reverse_url('plugins_api_url', None, None, None),
                worklist_api_url=self.reverse_url('worklist_api_url', None, None),
                transaction_log_url=self.reverse_url('transaction_log_url', target_id, None),
                url_log_url=self.reverse_url('url_log_url', target_id),
                sessions_ui_url=self.reverse_url('sessions_ui_url', target_id),
            )


class PluginOutput(UIRequestHandler):
    SUPPORTED_METHODS = ['GET']

    def get(self, target_id=None):
        if not target_id:
            raise tornado.web.HTTPError(400)
        try:
            filter_data = dict(self.request.arguments)  # IMPORTANT!!
            plugin_outputs = self.get_component("plugin_output").get_all(filter_data, target_id=target_id)
            # Group the plugin outputs to make it easier in template
            grouped_plugin_outputs = {}
            for poutput in plugin_outputs:
                if grouped_plugin_outputs.get(poutput['plugin_code']) is None:
                    # No problem of overwriting
                    grouped_plugin_outputs[poutput['plugin_code']] = []
                grouped_plugin_outputs[poutput['plugin_code']].append(poutput)
            # Needed ordered list for ease in templates
            grouped_plugin_outputs = collections.OrderedDict(sorted(grouped_plugin_outputs.items()))

            # Get mappings
            if self.get_argument("mapping", None):
                mappings = self.get_component("mapping_db").get_mappings(self.get_argument("mapping", None))
            else:
                mappings = None

            # Get test groups as well, for names and info links
            test_groups = {}
            for test_group in self.get_component("db_plugin").get_all_test_groups():
                test_group["mapped_code"] = test_group["code"]
                test_group["mapped_descrip"] = test_group["descrip"]
                if mappings:
                    try:
                        test_group["mapped_code"] = mappings[test_group['code']][0]
                        test_group["mapped_descrip"] = mappings[test_group['code']][1]
                    except KeyError:
                        pass
                test_groups[test_group['code']] = test_group

            self.render(
                "plugin_report.html",
                grouped_plugin_outputs=grouped_plugin_outputs,
                test_groups=test_groups,
                poutput_api_url=self.reverse_url('poutput_api_url', target_id, None, None, None),
                transaction_log_url=self.reverse_url('transaction_log_url', target_id, None),
                url_log_url=self.reverse_url('url_log_url', target_id),
            )
        except InvalidTargetReference:
            raise tornado.web.HTTPError(400)
        except InvalidParameterType:
            raise tornado.web.HTTPError(400)


class WorkerManager(UIRequestHandler):
    SUPPORTED_METHODS = ['GET']

    @tornado.web.asynchronous
    def get(self, worker_id=None):
        config = ServiceLocator.get_component("config")
        ui_port = config.get_val("UI_SERVER_PORT")
        fileserver_port = config.get_val("FILE_SERVER_PORT")
        output_files_server = "%s://%s" % (self.request.protocol, self.request.host.replace(ui_port, fileserver_port))
        if not worker_id:
            self.render(
                "manager_interface.html",
                worklist_api_url=self.reverse_url('worklist_api_url', None, None),
                workers_api_url=output_files_server + self.reverse_url('workers_api_url', None, None),
                targets_api_url=self.reverse_url('targets_api_url', None),
                targets_ui_url=self.reverse_url('targets_ui_url', None),
                plugins_api_url=self.reverse_url('plugins_api_url', None, None, None),
                progress_api_url=output_files_server + self.reverse_url('poutput_count'),
                log_url_port=output_files_server
            )
        else:
            self.render(
                "worker_interface.html",
                worker_api_url=self.reverse_url('workers_api_url', worker_id, None),
                targets_api_url=self.reverse_url('targets_api_url', None),
                targets_ui_url=self.reverse_url('targets_ui_url', None)
            )


class WorklistManager(UIRequestHandler):
    SUPPORTED_METHODS = ['GET']

    def get(self):
        self.render(
            "worklist_manager.html",
            worklist_api_url=self.reverse_url('worklist_api_url', None, None),
            worklist_search_api_url=self.reverse_url('worklist_search_api_url'),
            targets_ui_url=self.reverse_url('targets_ui_url', None),
        )


class Help(UIRequestHandler):
    SUPPORTED_METHODS = ['GET']

    def get(self):
        self.render("help.html")

class Transactions(UIRequestHandler):
    SUPPORTED_METHODS = ['GET']

    def get(self):
        self.render("transaction_log.html")

class ConfigurationManager(UIRequestHandler):
    SUPPORTED_METHODS = ['GET']

    def get(self):
        self.render("config_manager.html", configuration_api_url=self.reverse_url('configuration_api_url'))


class FileRedirectHandler(UIRequestHandler):
    SUPPORTED_METHODS = ['GET']

    def get(self, file_url):
        config = ServiceLocator.get_component("config")
        ui_port = config.get_val("UI_SERVER_PORT")
        fileserver_port = config.get_val("FILE_SERVER_PORT")
        output_files_server = "%s://%s/" % (self.request.protocol, self.request.host.replace(ui_port, fileserver_port))
        redirect_file_url = output_files_server + url_escape(file_url, plus=False)
        self.redirect(redirect_file_url, permanent=True)
