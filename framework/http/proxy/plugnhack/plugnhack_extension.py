import monitor_manager, oracle_manager
import tornado.web

class PlugnhackExtension(object):
    def __init__(self):
        self._mpm = monitor_manager.MonitoredPage()
        self._oracle = oracle_manager.OracleManager()
        self._id_count = 0
        self._known_types = list()
    

    def inject_probe(self, data):
        # Path to probe code
        path = os.path.dirname(os.path.realpath(__file__))
        loader = tornado.template.Loader(path)
        # Load probe code from pnh_probe.js
        probe_code = loader.load("pnh_probe.js").generate()
        # url of manifest.json, there is specified endpointName etc.
        root = self.get_proxy_info()
        self._id_count = self._id_count + 1
        id_token = "OWTF_ID-" + str(self._id_count)
        script_start = "<!-- OWASP OWTF Start of injected code -->\n" + "<script>\n"
        # JS code for probe initialisation
        script_end = "\nvar probe = new Probe('" + root + "','" + id_token + "');\n" + \
            "OWASP OWTF End of injected code -->\n" + \
            "<script>\n"
        # Inject probe code only into a monitored page
        if self._mpm.is_monitored(message, data):
            try:
                # Find index of <head> tag, probe is injected in between
                # <head> and </head>
                start_head = data.find("<head")
                # Predicate variable to verify if injection succeeded
                injected = False
                # If <head> tag is present in html code
                if start_head > 0:
                    # Find </head> tag
                    end_head = data.find(">", start_head)
                    if end_head > 0:
                        # We need to inject after </head> tag
                        # If not increment end_head the probe will be
                        # inject into </head 'probe'>
                        end_head = end_head + 1
                        # Save monitored page in DB
                        page = self._mpm.monitor_page(message)
                        try:
                            self.application.Core.DB.Target.AddTarget(page)
                            self.set_status(201)
                        except DBIntegrityException as e:
                            cprint(e.parameter)
                            raise tornado.web.HTTPError(409)
                        except UnresolvableTargetException as e:
                            cprint(e.parameter)
                            raise tornado.web.HTTPError(409)
                        # inject probe code in html page
                        data = data[:end_head] + script_start + probe_code + script_end + data[end_head:]
                        # Change predicate variable value
                        injected = True
                        if not injected:
                            raise tornado.web.HTTPError(412)
            except:
                raise tornado.web.HTTPError(412)
            
            return True

        
    def message_received(self, message):
        # If type of message is not in known_types, add it to known_types
        if not message.get_type() in self._known_types:
            self._known_types.append(message.get_type())
            # Get page id from monitored pages manager using message id
            page = self._mpm.client(message.client_id())
            self.persist(msg)
            return self._mpm.message_received(msg)
        
        
    def persist(self, client_message):
        try:
            if client_message.get_index() > 0:
                if client_message.is_changed():
                    # TO DO
                    # Need to record that a client message was changed
                    # ZAP uses a table in DB for recording messages
                    pass
                elif not (client_message.get_type() == self._mpm.heartbeat_message):
                    # TO DO
                    # Need to insert this in table something like in ZAP
                    pass
        except InvalidMessageReference as e:
            self.Core.write_event(e.parameter, 'a')
            raise tornado.web.HTTPError(400)


    # Check if page is monitored
    def is_monitored(self, client_id):
        return self._mpm.is_monitored(client_id)
        

    def register_oracle(self, data):
        return self._oracle.register_oracle(data)
    

    def add_oracle_listener(self, listenner):
        return self._oracle.add_listener(listenner)
    

    def remove_oracle_listener(self, listenner):
        return self._oracle.remove_listener(listenner)
        

    def oracle_invoked(self, id_orc):
        self.Core.write_event("Oracle invoked for " + id_orc, 'a')
        self._oracle.oracle_invoked(id_orc)
        

    def start_monitoring(self, uri):
        page = self._mpm.start_monitoring(uri)
        try:
            # TO DO
            # Insert this page into a table (DB) like in ZAP
            pass
        except:
            self.Core.write_event(uri + "is not monitored")
            return page.page_id()
        

    def stop_monitoring(self, id_page):
        return self._mpm.stop_monitoring(id_page)
    

    # mpm -> monitored page manager
    def add_mpm_listener(self, listenner):
        self._mpm.add_listener(listenner)


    def remove_mpm_listener(self, listenner):
        self._mpm.remove_listener(listenner)
        

    def get_proxy_info(self):
        proxy_address = "http://127.0.0.1:8009/ui/plugnhack/manifest.json"
        return proxy_address
    

    # Sort known_types and return to caller
    def get_known_types(self):
        return sorted(self._known_types)
    

    # Sort active clients and return to caller
    def get_active_clients(self):
        return sorted(self._mpm.get_active_clients())


    # Sort active ids and return to caller
    def get_active_ids(self):
        return sorted(self._mpm.get_active_ids())


    # Sort inactive clients and return to caller
    def get_inactive_clients(self):
        return sorted(self._mpm.get_inactive_clnts())


    # Sort inactive ids and return to caller
    def get_inactive_ids(self):
        return sorted(self._mpm.get_inactice_ids())
    

    # Create message that will be sent to client (probe)
    def set_client_config(self, page, key, value):
        cmsg = client_message.ClientMessage()
        cmsg.set_to("OWTF")
        cmsg.set_type("setConfig")
        cmsg.client_id(page.get_id())
        cmsg.set_key_value("name",key)
        cmsg.set_key_value("value",value)
        return cmsg
