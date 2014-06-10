from framework.lib.general import cprint
from framework.lib import general
from framework.interface import custom_handlers
import tornado.web
import collections

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

class PlugnHack(custom_handlers.UIRequestHandler):
    #SUPPORTED_METHODS = ['GET']
    #@tornado.web.asynchronous
    #def get(self, target_id=None):
    #    if not target_id:
    #        self.render("plugnhack.html",
    #                    plugnhack_ui_url=self.reverse_url('plugnhack_ui_url', None)
    #                    )
    #    else:
    #        self.render("plugnhack.html",
    #                    plugnhack_ui_url=self.reverse_url('plugnhack_ui_url', target_id)
    #                    )
    def get(self):
        self.render('plugnhack.html')

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

    
#class PlugnHackHandler(tornado.web.RequestHandler):
  #  pass
 #   """
#    This handles the requests which are used for firefox configuration 
   # https://blog.mozilla.org/security/2013/08/22/plug-n-hack/
  #  """
 #   @tornado.web.asynchronous
#    def get(self, extension):
     #   """
    #    Root URL (in default case) = http://127.0.0.1:8008/proxy
   #     Templates folder is framework/http/proxy/templates
  #      For PnH, following files (all stored as templates) are used :-
 #       
     #   File Name       ( Relative path )
    #    =========       =================
   #     * Provider file ( /proxy )
  #      * Tool Manifest ( /proxy.json )
 #       * Commands      ( /proxy-service.json )
#        * PAC file      ( /proxy.pac )
   #     * CA Cert       ( /proxy.crt )
  #      """
 #       # Rebuilding the root url
#        root_url = self.request.protocol + "://" + self.request.host
     #   command_url = root_url + "/" + self.application.pnh_token
    #    proxy_url = root_url + "/proxy"
   #     # Absolute path of templates folder using location of this script (proxy.py)
  #      templates_folder = os.path.join(os.path.dirname(os.path.realpath(__file__)), "templates")
 #       print(templates_folder)
#        loader = tornado.template.Loader(templates_folder) # This loads all the templates in the folder
   #     if extension == "":
      #      manifest_url = proxy_url + ".json"
      #      self.write(loader.load("welcome.html").generate(manifest_url=manifest_url))
      #  elif extension == ".json":
     #       self.write(loader.load("manifest.json").generate(proxy_url=proxy_url))
    #        self.set_header("Content-Type", "application/json")
    #    elif extension == "-service.json":
    #        self.write(loader.load("service.json").generate(root_url=command_url))
    #        self.set_header("Content-Type", "application/json")
    #    elif extension == ".pac":
    #        self.write(loader.load("proxy.pac").generate(proxy_details=self.request.host))
     #       self.set_header('Content-Type','text/plain')
   #     elif extension == ".crt":
  #          self.write(open(self.application.ca_cert, 'r').read())
 #           self.set_header('Content-Type','application/pkix-cert')
#        self.finish()
