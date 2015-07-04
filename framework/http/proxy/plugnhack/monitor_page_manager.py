import client_message
import datetime

class MonitoredPageManager(object):
    """
    MonitoredPageManager supervises what pages a monitored, what pages are 
    active/inactive, also handles messages (changes their state). 
    MonitoredPageManager activates as a dispatcher, saves information from 
    its actors and responds with useful information to actors.
    """
    class __init__(self, ext, core):
        # Core instance variable for accessing write_event and other methods
        self.Core = core
        self.heartbeat_message = "heartbeat"
        # extension instance variable for accessing PlugnhackExtension methods and properties
        self._extension = ext
        self._monitor_all_scope = False
        # Save one-time urls in a list DS
        self._one_time_urls = list()
        # Save monitored pages in a dict DS
        self._monitored_pages = dict()
        # Save inactive pages in a dict DS
        self._inactive_pages = dict()
        # Save listeners in a list DS
        self._listeners = list()
        # Sale queued messages in a list DS
        self._queued_msgs = list()
        # Counter for page id: 'OWTF_ID-' + value of _counter
        self._counter = 0
        


    # Verify if message (url) is monitored, if its a one-time url.
    def is_monitored(self, msg):
        if msg is None:
            return False
        
        uri = msg.get('url')
        
        for otu in self._one_time_urls:
            if otu == uri:
                self.Core.write_event("It is a one time URL " + uri + "\n", 'a')
                return True
        
        if self._monitor_all_scope:
            self.Core.write_event("URL in scope " + uri + "\n", 'a')
            return True

        self.Core.write_event("URL is not monitored " + uri + '\n', 'a')
        return False


    # Add url to one_time_urls
    def add_onetime_url(self, url):
        self._one_time_urls.append(url)


    # Respond with value of monitor_all_scope
    @property
    def monitor_all_scope(self):
        return self._monitor_all_scope


    # Update value of monitor_all_scope
    @monitor_all_scope.setter
    def monitor_all_scope(self, scope):
        self._monitor_all_scope = scope


    def message_received(self, msg):
        # Save response messages in a list DS
        response_list = list()
        
        page = monitor_manager.MonitoredPage()
        # If page with message client_id is in monitored_page retrieve and 
        # store it in 'page' instance
        page = self._monitored_pages.get(msg.client_id())
        if page is not None:
            # If this page is already monitored, it needs to update time for last_message
            page.last_message(datetime.datetime.now())
            uri = msg.get('url')

            # Iterate through one_time_urls, if current 'uri' is a one time url remove it and stop the search
            # A one-time URL is a specially crafted address that is valid for one use only, 
            # for example the link when you validate your account
            # otu -> one-time url
            for otu in self._one_time_urls:
                if otu == uri:
                    self.Core.write_event("Removing onetime URL " + uri "\n", 'a')
                    self._one_time_urls.remove(otu)
                    break

        # If the value of key 'type' is 'heartbeat' ignore it
        # this is a usual message, default 'type' of probe message is 'heartbeat'
        if msg.get_type() == self.heartbeat_message:
            pass
        else:
            # Get response from each listener, if response is present add it to response_list
            for listener in self._listeners:
                response = listener.message_received(msg)
                if response is not None:
                    response_list.append(response)
        
        # Save handled messages into a list DS
        handled_messages = list()
        
        # Verify if current message is present in queued messages
        # If it exists in queued messages update received time and add to response list
        # Update queued message state
        for qmsg in self._queued_msgs:
            if qmsg.client_id() == msg.client_id():
                self.Core.write_event("Adding queued message for " + qmsg.client_id() + ":" + qmsg.get_data(), 'a')
                qmsg.received(datetime.datime.now())
                response_list.append(self.msg_to_response(qmsg,True))
                qmsg.state(qmsg.State.resent)

                for listener in self._listeners:
                    listener.message_received(qmsg)
                
                # Add handled message to handled_messages 
                # and verify if queued message state is changed or add to DB
                handled_messages.append(qmsg)
                self._extension.persist(qmsg)
                break
        
        # hmsg -> handled message
        # Remove handled messages from queued messages
        for hmsg in handled_messages:
            try:
                self._queued_msgs.remove(hmsg)
            except ValueError as e:
                self.Core.write_event(e.parameter, 'a')

        response = tuple()
        response = "messages", response_list
        return response

    
    # Check if 'client'/'page' is monitored
    def is_monitored(self, client):
        return self._monitored_pages.has_key(client)
    
    
    
    def msg_to_response(self, msg, resend=False):
        # Message to probe is a dictionary
        msg_map = msg.to_map()
        # Update type, for example 'setConfig'
        msg_map["type"] = msg.get_type()
        if resend:
            msg_map["responseTo"] = msg.get_endpoint_id()
        else:
            msg_map["responseTo"] = msg.get_message_id()

        #return "message", msg_map
        response = "messages", msg_map
        return response

    
    def get_unique_id(self):
        # Each monitored page must have an unique id
        self._counter = self._counter + 1
        return "OWTF_ID-" + str(self._counter)


    def start_monitoring(self, uri):
        # Save url of page to monitor and its id in monitored_pages
        msg = tornado.httpclient.HTTPRequest(url=uri)
        page = monitor_manager.MonitoredPage(self.get_unique_id(), msg, datetime.datetime.now())
        self._monitored_pages[page.page_id()] = page
        # Listen for messages coming for each monitored page and present them to user. UI for this is not implemented. !!! TO DO !!!
        #for listener in self._listeners:
        #    listener.start_monitoring_page_event(page)

        return page


    def stop_monitoring(self, param_id):
        # Using page id, remove it from monitored_pages
        # Update state to inactive page
        page = self._monitored_pages.pop(param_id)
        if page is not None:
            page.active(False)
            self._inactive_pages[str(param_id)] = page


    def monitor_page(self, msg):
        page = monitor_manager.MonitoredPage(self.get_unique_id(), msg, datetime.datetime.now())
        self._monitored_pages[page.page_id()] = page
        # !!! TO DO !!!
        # for listener in self._listeners:
        #    listener.start_monitoring_page_event(page)

        return page

    
    def get_monitored_pages(self, param_id, inactive):
        # Using the page id retrieve it from monitored_page
        page = self._monitored_page.get(param_id)
        # If page is not monitored and is inactive, it it stored in inactive_pages
        if page is None and inactive:
            page = self._inactive_pages.get(param_id)

        return page


    def reset(self):
        # Set to default 
        self._monitor_all_scope = False
        self._monitored_pages.clear()
        self._inactive_pages.clear()
        
    
    # Add listener to _listeners
    @listeners.setter
    def listener(self, listener):
        self._listeners.append(listener)


    # Remove listener from _listeners
    @listeners.setter
    def remove_listener(self, listener):
        try:
            self._listeners.remove(listener)
        except ValueError as e:
            pass


    def pending_messages(self, client_id):
        # Check if a message is queued using its id
        for qmsg in self._queued_msgs:
            if client_id == qmsg.client_id():
                return True
        return False

    # Resend a message
    def resend(self, msg):
        msg2 = client_message.ClientMessage(msg.client_id(), msg.json_obj)
        msg2.changed(True)
        self.send(msg2)

    # Send a message
    # Change message state to pending and add it to queued messages
    def send(self, msg):
        msg.state(msg.State.pending)
        self.Core.write_event("Adding message to queue for " + msg.client_id() + ":" + msg.get_data())
        self.queued_msgs.append(msg)

    
    # Get a list with ids of monitored_pages
    def active_clients_ids(self):
        response = list()
        for page in self._monitored_pages.values():
            response.append(page.page_id())

        return response
    
    
    # Get a list with active pages
    def active_clients(self):
        response = list()
        for page in self._monitored_pages.values():
            response.append(page)

        return response


    # Get a list with ids of inactive pages
    def inactive_clients_ids(self):
        response = list()
        for page in self._inactive_pages.values():
            response.append(page.page_id())

        return response

    # Get a list with inactive pages
    def inactive_clients(self):
        response = list()
        for page in self._inactive_pages.values():
            response.append(page)

        return response


    # Change a page from active to inactive
    @inactive_pages.setter
    def inactive_client(self, page):
        page.active(False)
        self._inactive_pages[page.page_id()] = page


    # Get a page with 'client_id' if it is in monitored_pages or inactive_pages
    @property
    def client(self, client_id):
        client = self._monitored_pages.get(client_id)
        if client is None:
            client = self._inactive_pages.get(client_id)
        
        return client
            
