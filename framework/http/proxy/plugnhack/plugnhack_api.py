import plugnhack_extension

class PlugnhackAPI(object):              
    """
    PlugnhackAPI handles commands from user.
    """
    def __init__(self,core):
        # Core instance variable to access its methods
        self.Core = core
        # User valid commands
        self.action_monitor = "monitor"
        self.action_start_monitoring = "startMonitoring"
        self.action_stop_monitoring = "stopMonitoring"
        self.action_oracle = "oracle"
        self.param_message = "message"
        self.param_id = "id"
        self.param_url = "url"
        self.extension = plugnhack_extension.PlugnhackExtension()
    
    def handle_api_action(self, command_name, message):
        response = tuple()
        
        if command_name == self.action_monitor:
            # Extract 'message:[]' from message parameter
            monitor_message = message.get(self.param_message)
            # Extract id from message
            page_id = message.get(self.param_id)
            
            # Convert monitor_message to json format
            json_msg = json.loads(monitor_message)
            
            # Pass page_id and json_msg to client_message that creates an
            # message object, used by extension to respond with a message
            # to probe
            resp = self.extension.message_received(client_message.ClientMessage(page_id,json_msg))
            if resp is not None:
                response = resp

        elif command_name == self.action_oracle:
            # Invoke oracle with id from message
            self.extension.oracle_invoked(message.get(self.param_id))

        elif command_name == self.action_start_monitoring:
            # extract url sent by user 
            monitor_url = message.get(self.param_url)
            
            try:
                # Register monitor_url for monitoring
                page_id = self.extension.start_monitoring(monitor_url)
                # Response to probe is the id for monitor_url
                response = self.param_id, page_id
            except:
                self.Core.write_event("Illegal url\n", 'a');
        
        elif command_name == self.action_stop_monitoring:
            # stop monitoring a page, based on its id
            page_id = message.get(self.param_id)
            self.extension.stop_monitoring(page_id)

        return response
