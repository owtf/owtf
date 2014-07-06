from framework.lib.general import cprint
from framework.lib import general
from framework.interface import custom_handlers
import tornado.web
import collections
import os

class Redirect(custom_handlers.UIRequestHandler):
    SUPPORTED_METHODS = ['GET']
    def get(self):
        self.redirect(self.reverse_url('home_ui_url'))

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
                        transaction_log_url=self.reverse_url('transaction_log_url', target_id, None),
                        transaction_replay_url=self.reverse_url('transaction_replay_url',target_id, transaction_id),
                        forward_zap_url=self.reverse_url('forward_zap_url',target_id, transaction_id)
                        )
        else:
            self.render("transaction_log.html",
                        transactions_api_url=self.reverse_url('transactions_api_url', target_id, None),
                        transaction_log_url=self.reverse_url('transaction_log_url', target_id, None),
                        zest_console_url=self.reverse_url('zest_console_url', target_id)
                        )


class ReplayRequest(custom_handlers.UIRequestHandler):
    SUPPORTED_METHODS = ['GET']

    @tornado.web.asynchronous
    def get(self, target_id=None, transaction_id=None):
        if not target_id or not transaction_id:
            raise tornado.web.HTTPError(405)
        else:
            self.render("replay_request.html",
                        transaction_api_url=self.reverse_url('transactions_api_url',target_id, transaction_id),
                        transaction_replay_api_url=self.reverse_url('transaction_replay_api_url',target_id, transaction_id)
                        )


class ZestScriptConsoleHandler(custom_handlers.UIRequestHandler):
    SUPPORTED_METHODS = ['GET']

    @tornado.web.asynchronous
    def get(self, target_id=None):
        if not target_id:
            raise tornado.web.HTTPError(405)
        else:
            self.render("zest_console.html",
                       zest_console_api_url=self.reverse_url('zest_console_api_url',target_id),
                       zest_recording=self.application.Core.zest.IsRecording(),
                       zest_target_heading=(self.application.Core.zest.GetTargetConfig(target_id))['Host_and_Port'])


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
                        plugins_api_url=self.reverse_url('plugins_api_url', None, None, None),
                        worklist_api_url=self.reverse_url('worklist_api_url'),
                        transaction_log_url=self.reverse_url('transaction_log_url', target_id, None),
                        url_log_url=self.reverse_url('url_log_url', target_id)
                       )

class PlugnHack(custom_handlers.UIRequestHandler):
    """
    PlugnHack handles the requests which are used for integration
    of OWTF with Firefox browser using Plug-n-Hack add-on.
    For more information about Mozilla Plug-n-Hack standard visit:
    https://blog.mozilla.org/security/2013/08/22/plug-n-hack/
    """
    SUPPORTED_METHODS = ['GET']
    @tornado.web.asynchronous
    def get(self, extension=""):
        """
        pnh is an abbreviation for Plug-n-Hack
        URL in default case = http://127.0.0.1:8009/ui/plugnhack/
        Templates folder is framework/interface/templates/pnh
        For Plug-n-Hack, following files are used:

        ===================================================
        |    File Name    |          Relative path        |
        ===================================================
        |  Provider file  |   /ui/plugnhack/              |
        ---------------------------------------------------
        |  Manifest file  |   /ui/plugnhack/manifest.json |
        ---------------------------------------------------
        |  Commands file  |   /ui/plugnhack/service.json  |
        ---------------------------------------------------
        |  PAC file       |   /ui/plugnhack/proxy.pac     |
        ---------------------------------------------------
        |  CA Cert        |   /ui/plugnhack/ca.crt        |
        ---------------------------------------------------
        """
        root_url = self.request.protocol + "://" + self.request.host
        command_url = os.path.join(root_url,"")
        pnh_url = root_url + "/ui/plugnhack"
        # Obtain path to PlugnHack template files
        # PLUGNHACK_TEMPLATES_DIR is defined in /framework/config/framework_config.cfg
        pnh_folder = os.path.join(self.application.Core.Config.FrameworkConfigGet('PLUGNHACK_TEMPLATES_DIR'),"")
        self.application.ca_cert = os.path.expanduser(self.application.Core.DB.Config.Get('CA_CERT'))

        
        if extension == "":
            manifest_url = pnh_url + "/manifest.json"
            self.render(pnh_folder + "plugnhack.html",
                        manifest_url=manifest_url,
                        plugnhack_ui_url=self.reverse_url('plugnhack_ui_url')
                        )
        elif extension == "manifest.json":
            self.render(pnh_folder + "manifest.json",
                        pnh_url=pnh_url,
                        plugnhack_ui_url=self.reverse_url('plugnhack_ui_url')
                        )
        elif extension == "service.json":
            self.render(pnh_folder + "service.json", 
                        root_url=command_url,
                        plugnhack_ui_url=self.reverse_url('plugnhack_ui_url')
                        )
        elif extension == "proxy.pac":
            self.render(pnh_folder + "proxy.pac", 
                        server_details=self.request.host,
                        plugnhack_ui_url=self.reverse_url('plugnhack_ui_url')
                        )
        elif extension == "ca.crt":
            self.render(self.application.ca_cert,
                        plugnhack_ui_url=self.reverse_url('plugnhack_ui_url')
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
            grouped_plugin_outputs = collections.OrderedDict(sorted(grouped_plugin_outputs.items())) # Needed ordered list for ease in templates
            # Get test groups as well, for names and info links
            test_groups = {}
            for test_group in self.application.Core.DB.Plugin.GetAllTestGroups():
                test_groups[test_group['code']] = test_group
            self.render("plugin_report.html",
                        grouped_plugin_outputs=grouped_plugin_outputs,
                        test_groups=test_groups,
                        poutput_api_url=self.reverse_url('poutput_api_url', target_id, None, None, None),
                        transaction_log_url=self.reverse_url('transaction_log_url', target_id, None),
                        url_log_url=self.reverse_url('url_log_url', target_id)
                        )
        except general.InvalidTargetReference as e:
            raise tornado.web.HTTPError(400)

class WorkerManager(custom_handlers.UIRequestHandler):
    SUPPORTED_METHODS = ['GET']
    @tornado.web.asynchronous
    def get(self, worker_id=None):
        if not worker_id:
            self.render("manager_interface.html",
                        worklist_api_url=self.reverse_url('worklist_api_url'),
                        workers_api_url=self.reverse_url('workers_api_url', None, None),
                        targets_api_url=self.reverse_url('targets_api_url', None),
                        targets_ui_url=self.reverse_url('targets_ui_url', None),
                        )
        else:
            self.render("worker_interface.html",
                        worker_api_url=self.reverse_url('workers_api_url', worker_id, None),
                        targets_api_url=self.reverse_url('targets_api_url', None),
                        targets_ui_url=self.reverse_url('targets_ui_url', None)
                        )

class Help(custom_handlers.UIRequestHandler):
    SUPPORTED_METHODS = ['GET']
    @tornado.web.asynchronous
    def get(self):
        self.render("help.html")


class ConfigurationManager(custom_handlers.UIRequestHandler):
    SUPPORTED_METHODS = ('GET')
    @tornado.web.asynchronous
    def get(self):
        self.render(
            "config_manager.html",
            configuration_api_url=self.reverse_url('configuration_api_url')
        )

    
