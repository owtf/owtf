import os
import collections
import tornado.web
from tornado.escape import url_escape
import uuid
from framework.dependency_management.dependency_resolver import ServiceLocator
from framework.lib.exceptions import InvalidTargetReference, \
    InvalidParameterType
from framework.lib.general import cprint
from framework.interface import custom_handlers


class Redirect(custom_handlers.UIRequestHandler):
    SUPPORTED_METHODS = ['GET']
    def get(self):
        self.redirect(self.reverse_url('home_ui_url'))


class Home(custom_handlers.UIRequestHandler):
    SUPPORTED_METHODS = ['GET']
    def get(self):
        self.render('home.html',
                auto_updater_api_url=self.reverse_url('auto_updater_api_url'),
                )


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
                        transactions_search_api_url=self.reverse_url('transactions_search_api_url', target_id),
                        transaction_log_url=self.reverse_url('transaction_log_url', target_id, None),
                        zest_console_url=self.reverse_url('zest_console_url', target_id)
                        )


class HTTPSessions(custom_handlers.UIRequestHandler):
    """ HTTPSessions handles the user sessions. """
    SUPPORTED_METHODS = ['GET']

    @tornado.web.asynchronous
    def get(self, target_id=None):
        if not target_id:
            raise tornado.web.HTTPError(405)
        self.render("sessions_manager.html",
                    sessions_api_url=self.reverse_url('sessions_api_url', target_id),
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
                        transaction_replay_api_url=self.reverse_url('transaction_replay_api_url', target_id, transaction_id)
                        )


class ZestScriptConsoleHandler(custom_handlers.UIRequestHandler):
    SUPPORTED_METHODS = ['GET']

    @tornado.web.asynchronous
    def get(self, target_id=None):
        if not target_id:
            raise tornado.web.HTTPError(405)
        else:
            self.render("zest_console.html",
                       zest_console_api_url=self.reverse_url('zest_console_api_url', target_id),
                       zest_recording=self.get_component("zest").IsRecording(),
                       zest_target_heading=(self.get_component("zest").GetTargetConfig(target_id))['HOST_AND_PORT']
                       )


class UrlLog(custom_handlers.UIRequestHandler):
    SUPPORTED_METHODS = ['GET']

    @tornado.web.asynchronous
    def get(self, target_id=None):
        if not target_id:
            raise tornado.web.HTTPError(405)
        self.render("url_log.html",
                    urls_api_url=self.reverse_url('urls_api_url', target_id),
                    urls_search_api_url=self.reverse_url('urls_search_api_url', target_id),
                    transaction_log_url=self.reverse_url('transaction_log_url', target_id, None)
                    )


class TargetManager(custom_handlers.UIRequestHandler):
    SUPPORTED_METHODS = ['GET']
    @tornado.web.asynchronous
    def get(self, target_id=None):
        if not target_id:
            self.render("target_manager.html",
                        owtf_sessions_api_url=self.reverse_url('owtf_sessions_api_url', None, None),
                        targets_api_url=self.reverse_url('targets_api_url', None),
                        targets_search_api_url=self.reverse_url('targets_search_api_url'),
                        targets_ui_url=self.reverse_url('targets_ui_url', None),
                        plugins_api_url=self.reverse_url('plugins_api_url', None, None, None),
                        worklist_api_url=self.reverse_url('worklist_api_url', None, None)
                        )
        else:
            adv_filter_data = self.get_component("plugin_output").GetUnique(target_id=int(target_id))
            adv_filter_data["mapping"] = self.get_component("mapping_db").GetMappingTypes()
            self.render("target.html",
                        target_api_url=self.reverse_url('targets_api_url', target_id),
                        targets_ui_url=self.reverse_url('targets_ui_url', None),
                        poutput_ui_url=self.reverse_url('poutput_ui_url', target_id),
                        adv_filter_data=adv_filter_data,
                        plugins_api_url=self.reverse_url('plugins_api_url', None, None, None),
                        worklist_api_url=self.reverse_url('worklist_api_url', None, None),
                        transaction_log_url=self.reverse_url('transaction_log_url', target_id, None),
                        url_log_url=self.reverse_url('url_log_url', target_id),
                        sessions_ui_url=self.reverse_url('sessions_ui_url', target_id),
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
        root_url = self.request.protocol + "://" + self.request.host # URL of UI SERVER, http://127.0.0.1:8009
        command_url = os.path.join(root_url,"") # URL for use in service.json, http://127.0.0.1:8009/
        pnh_url = os.path.join(root_url,"ui/plugnhack") # URL for use in manifest.json, http://127.0.0.1:8009/ui/plugnhack
        probe_url = "http://" + self.get_component("db_config").Get('INBOUND_PROXY_IP') + ":" + self.get_component("db_config").Get('INBOUND_PROXY_PORT') # URL for use in manifest.json, Plug-n-Hack probe will send messages to http://127.0.0.1:8008/plugnhack
        # Obtain path to PlugnHack template files
        # PLUGNHACK_TEMPLATES_DIR is defined in /framework/config/framework_config.cfg
        pnh_folder = os.path.join(self.get_component("config").FrameworkConfigGet('PLUGNHACK_TEMPLATES_DIR'),"")
        self.application.ca_cert = os.path.expanduser(self.get_component("db_config").Get('CA_CERT')) # CA certificate
        # Using UUID system generate a key for substitution of 'api_key' in
        # 'manifest.json', 'probe' descriptor section
        # Its use is temporary, till Bhadarwaj implements 'API key generation'
        api_key = uuid.uuid4().hex

        if extension == "": # In this case plugnhack.html is rendered and {{ manifest_url }} is replaced with 'manifest_url' value
            manifest_url = pnh_url + "/manifest.json"
            # Set response status code to 200 'OK'
            self.set_status(200)
            # Set response header 'Content-Type'
            self.set_header("Content-Type","text/html")
            # Set response header 'Etag', it will not appear in response,
            # we don't need web-cache validation
            self.set_header("Etag","")
            # Set response header 'Server, it will not appear in response
            self.set_header("Server","")
            # Set response header 'Date', it will not appear in response
            self.set_header("Date","")
            # Set response header 'Cache-Control', it will not appear,
            # we don't need caching for Plugnhack
            self.add_header("Cache-Control","no-cache")
            # Set response header 'Pragma', it will not appear in response
            self.add_header("Pragma","no-cache")
            # Set response headers for CORS, it allows many resources on a
            # web page to be requested from another domain outside the domain
            # the resource originated from. This mechanism is used in OWASP ZAP.
            self.add_header("Access-Control-Allow-Origin","*")
            self.add_header("Access-Control-Allow-Header","OWTF-Header")
            self.add_header("Access-Control-Allow-Method","GET,POST,OPTIONS")

            self.render(pnh_folder + "plugnhack.html",
                        manifest_url=manifest_url,
                        plugnhack_ui_url=self.reverse_url('plugnhack_ui_url')
                        )

        elif extension == "manifest.json": # In this case {{ pnh_url }} in manifest.json are replaced with 'pnh_url' value
            # Set response status code to 200 'OK'
            self.set_status(200)
            # Set response header 'Content-Type'
            self.set_header("Content-Type","application/json")
            # Set response header 'Etag', it will not appear in response,
            # we don't need web-cache validation
            self.set_header("Etag","")
            # Set response header 'Server, it will not appear in response
            self.set_header("Server","")
            # Set response header 'Date', it will not appear in response
            self.set_header("Date","")
            # Set response header 'Cache-Control', it will not appear,
            # we don't need caching for Plugnhack
            self.add_header("Cache-Control","no-cache")
            # Set response header 'Pragma', it will not appear in response
            self.add_header("Pragma","no-cache")
            # Set response headers for CORS, it allows many resources on a
            # web page to be requested from another domain outside the domain
            # the resource originated from. This mechanism is used in OWASP ZAP.
            # Without this Plug-n-Hack cannot send messages and error:
            # 'Cross-Origin Request Blocked: The Same Origin Policy disallows reading
            # the remote resource at' will be present in browser console
            self.add_header("Access-Control-Allow-Origin","*")
            self.add_header("Access-Control-Allow-Header","OWTF-Header")
            self.add_header("Access-Control-Allow-Method","GET,POST,OPTIONS")

            self.render(pnh_folder + "manifest.json",
                        pnh_url=pnh_url,
                        probe_url=probe_url,
                        api_key=api_key,
                        plugnhack_ui_url=self.reverse_url('plugnhack_ui_url')
                        )
        elif extension == "service.json": # In this case {{ root_url }} in service.json are replaced with 'root_url' value
            # Set response status code to 200 'OK'
            self.set_status(200)
            # Set response header 'Content-Type'
            self.set_header("Content-Type","application/json")
            # Set response header 'Etag', it will not appear in response,
            # we don't need web-cache validation
            self.set_header("Etag","")
            # Set response header 'Server, it will not appear in response
            self.set_header("Server","")
            # Set response header 'Date', it will not appear in response
            self.set_header("Date","")
            # Set response header 'Cache-Control', it will not appear,
            # we don't need caching for Plugnhack
            self.add_header("Cache-Control","no-cache")
            # Set response header 'Pragma', it will not appear in response
            self.add_header("Pragma","no-cache")
            # Set response headers for CORS, it allows many resources on a
            # web page to be requested from another domain outside the domain
            # the resource originated from. This mechanism is used in OWASP ZAP.

            self.add_header("Access-Control-Allow-Origin","*")
            self.add_header("Access-Control-Allow-Header","OWTF-Header")
            self.add_header("Access-Control-Allow-Method","GET,POST,OPTIONS")

            self.render(pnh_folder + "service.json",
                        root_url=command_url,
                        plugnhack_ui_url=self.reverse_url('plugnhack_ui_url')
                        )

        elif extension == "proxy.pac": # In this case {{ proxy_details }} in proxy.pac is replaced with 'proxy_details' value
            proxy_details = self.get_component("db_config").Get('INBOUND_PROXY_IP') + ":" + self.get_component("db_config").Get('INBOUND_PROXY_PORT') # OWTF proxy 127.0.0.1:8008

            # Set response status code to 200 'OK'
            self.set_status(200)
            # Set response header 'Content-Type'
            self.set_header("Content-Type","text/plain")
            # Set response header 'Etag', it will not appear in response,
            # we don't need web-cache validation
            self.set_header("Etag","")
            # Set response header 'Server, it will not appear in response
            self.set_header("Server","")
            # Set response header 'Date', it will not appear in response
            self.set_header("Date","")
            # Set response header 'Cache-Control', it will not appear,
            # we don't need caching for Plugnhack
            self.add_header("Cache-Control","no-cache")
            # Set response header 'Pragma', it will not appear in response
            self.add_header("Pragma","no-cache")
            # Set response headers for CORS, it allows many resources on a
            # web page to be requested from another domain outside the domain
            # the resource originated from. This mechanism is used in OWASP ZAP.
            self.add_header("Access-Control-Allow-Origin","*")
            self.add_header("Access-Control-Allow-Header","OWTF-Header")
            self.add_header("Access-Control-Allow-Method","GET,POST,OPTIONS")

            self.render(pnh_folder + "proxy.pac",
                        proxy_details=proxy_details,
                        plugnhack_ui_url=self.reverse_url('plugnhack_ui_url')
                        )

        elif extension == "ca.crt":
            # Set response status code to 200 'OK'
            self.set_status(200)
            # Set response header 'Content-Type'
            self.set_header("Content-Type","application/pkix-cert")
            # Set response header 'Etag', it will not appear in response,
            # we don't need web-cache validation
            self.set_header("Etag","")
            # Set response header 'Server, it will not appear in response
            self.set_header("Server","")
            # Set response header 'Date', it will not appear in response
            self.set_header("Date","")
            # Set response header 'Cache-Control', it will not appear,
            # we don't need caching for Plugnhack
            self.add_header("Cache-Control","no-cache")
            # Set response header 'Pragma', it will not appear in response
            self.add_header("Pragma","no-cache")
            # Set response headers for CORS, it allows many resources on a
            # web page to be requested from another domain outside the domain
            # the resource originated from. This mechanism is used in OWASP ZAP.
            self.add_header("Access-Control-Allow-Origin","*")
            self.add_header("Access-Control-Allow-Header","OWTF-Header")
            self.add_header("Access-Control-Allow-Method","GET,POST,OPTIONS")

            self.render(self.application.ca_cert,
                        plugnhack_ui_url=self.reverse_url('plugnhack_ui_url')
                        )


class PluginOutput(custom_handlers.UIRequestHandler):
    SUPPORTED_METHODS = ['GET']

    def get(self, target_id=None):
        if not target_id:
            raise tornado.web.HTTPError(400)
        try:
            filter_data = dict(self.request.arguments)  # IMPORTANT!!
            plugin_outputs = self.get_component("plugin_output").GetAll(
                filter_data,
                target_id=target_id)
            # Group the plugin outputs to make it easier in template
            grouped_plugin_outputs = {}
            for poutput in plugin_outputs:
                if grouped_plugin_outputs.get(poutput['plugin_code']) is None:
                    # No problem of overwriting
                    grouped_plugin_outputs[poutput['plugin_code']] = []
                grouped_plugin_outputs[poutput['plugin_code']].append(poutput)
            # Needed ordered list for ease in templates
            grouped_plugin_outputs = collections.OrderedDict(
                sorted(grouped_plugin_outputs.items()))

            # Get mappings
            if self.get_argument("mapping", None):
                mappings = self.get_component("mapping_db").GetMappings(self.get_argument("mapping", None))
            else:
                mappings = None

            # Get test groups as well, for names and info links
            test_groups = {}
            for test_group in self.get_component("db_plugin").GetAllTestGroups():
                test_group["mapped_code"] = test_group["code"]
                test_group["mapped_descrip"] = test_group["descrip"]
                if mappings:
                    try:
                        test_group["mapped_code"] = mappings[test_group['code']][0]
                        test_group["mapped_descrip"] = mappings[test_group['code']][1]
                    except KeyError:
                        pass
                test_groups[test_group['code']] = test_group

            self.render("plugin_report.html",
                        grouped_plugin_outputs=grouped_plugin_outputs,
                        test_groups=test_groups,
                        poutput_api_url=self.reverse_url('poutput_api_url', target_id, None, None, None),
                        transaction_log_url=self.reverse_url('transaction_log_url', target_id, None),
                        url_log_url=self.reverse_url('url_log_url', target_id),
                        )
        except InvalidTargetReference as e:
            raise tornado.web.HTTPError(400)
        except InvalidParameterType as e:
            raise tornado.web.HTTPError(400)


class WorkerManager(custom_handlers.UIRequestHandler):
    SUPPORTED_METHODS = ['GET']
    @tornado.web.asynchronous
    def get(self, worker_id=None):
        config = ServiceLocator.get_component("config")
        output_files_server = "%s://%s" % (
            self.request.protocol,
            self.request.host.replace(
                config.FrameworkConfigGet("UI_SERVER_PORT"),
                config.FrameworkConfigGet("FILE_SERVER_PORT")))
        if not worker_id:
            self.render("manager_interface.html",
                        worklist_api_url=self.reverse_url('worklist_api_url', None, None),
                        workers_api_url=output_files_server+self.reverse_url('workers_api_url', None, None),
                        targets_api_url=self.reverse_url('targets_api_url', None),
                        targets_ui_url=self.reverse_url('targets_ui_url', None),
                        )
        else:
            self.render("worker_interface.html",
                        worker_api_url=self.reverse_url('workers_api_url', worker_id, None),
                        targets_api_url=self.reverse_url('targets_api_url', None),
                        targets_ui_url=self.reverse_url('targets_ui_url', None)
                        )


class WorklistManager(custom_handlers.UIRequestHandler):
    SUPPORTED_METHODS = ['GET']

    def get(self):
        self.render(
            "worklist_manager.html",
            worklist_api_url=self.reverse_url('worklist_api_url', None, None),
            worklist_search_api_url=self.reverse_url('worklist_search_api_url'),
            targets_ui_url=self.reverse_url('targets_ui_url', None),
        )


class Help(custom_handlers.UIRequestHandler):
    SUPPORTED_METHODS = ['GET']

    def get(self):
        self.render("help.html")


class ConfigurationManager(custom_handlers.UIRequestHandler):
    SUPPORTED_METHODS = ('GET')

    def get(self):
        self.render(
            "config_manager.html",
            configuration_api_url=self.reverse_url('configuration_api_url')
        )


class FileRedirectHandler(custom_handlers.UIRequestHandler):
    SUPPORTED_METHODS = ('GET')

    def get(self, file_url):
        config = ServiceLocator.get_component("config")
        output_files_server = "%s://%s/" % (
            self.request.protocol,
            self.request.host.replace(
                config.FrameworkConfigGet("UI_SERVER_PORT"),
                config.FrameworkConfigGet("FILE_SERVER_PORT")))
        redirect_file_url = output_files_server + url_escape(file_url, plus=False)
        self.redirect(redirect_file_url, permanent=True)
