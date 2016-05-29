import plugnhack_extension
import datetime
import json


def enum(**named_values):
    """
    enum represents a simulation of 'enum' data type in programming languages as 
    C, C++, Java etc.
    enum type is available as a built-in type in Python 3.4, not in Python 2.7, 
    enum data type was backported to 2.7 through pypi.
    For installing it run: pip install enum34
    """
    return type('Enum', (), named_values)

class ClientMessage(object):
    """
    ClientMessage represents information about a client message (state of a message
    , receiving time, if its content was changed), methods to modify a message 
    (change 'type', 'data', 'name' etc.), organize message content in a human
    readable format and appropriate for computers.
    """
    def __init__(self, client_id=None, json_obj=None):
        # id of monitored page
        self._client_id = client_id or None
        # information that must be updated/verified is represented as json
        self._json_obj = json.loads(json_obj) or None
        # save at which time message was received
        self._received = datetime.datetime.now()
        # state that a message pass
        self.State = enum(pending="pending",received="received",resent="resent",dropped="dropped",oraclehit="oraclehit")
        # first state for a message
        self._state = self.State.received
        # a new message haven't been modified
        self._changed = False
        self._index = -1
        self._extra_fields = dict()
        self._reflect_fields = ["eventData","originalEventTarget"]
        

    # Respond with the self._index current value
    @property
    def index(self):
        return self._index
    
    # Change value of self._index to a new value
    @index.setter
    def index(self, index):
        self._index = index

    # Respond with the self._json_obj current value
    @property
    def json_obj(self):
        return json.dumps(self._json_obj)

    # Update self._json_obj with new information
    @json_obj.setter
    def json_obj(self, json_obj):
        self._json_obj = json.loads(json_obj)

    # Respond with the self._received current value
    @property
    def received(self):
        return self._received

    # Update time at which message was received
    @received.setter
    def received(self, received):
        self._received = received

    # Respond with the value of key 'from', if it is present in self._json_obj
    def get_from(self):
        value = self._json_obj.get("from")
        if value:
            return value
        else:
            return None
    
    # Update/add the value for key 'from'
    def set_from(self, msg_from):
        self._json_obj["from"] = msg_from

    # Respond with the value of key 'to', if it is present in self._json_obj
    def get_to(self):
        value = self._json_obj.get("to")
        if value:
            return value
        else:
            return None

    # Update/add the value of key 'to'
    def set_to(self, msg_to):
        self._json_obj["to"] = msg_to
        
    # Respond with the value of key 'type', if it is present in self._json_obj
    # An example of type: "type":"setConfig"
    def get_type(self):
        value = self._json_obj.get("type")
        if value:
            return value
        else:
            return None

    #Update/add the value of key 'type'
    def set_type(self, type_p):
        self._json_obj["type"] = type_p

    # Respond with the value of key 'data', if it is present in self._json_obj 
    def get_data(self):
        value = self._json_obj.get("data")
        if value:
            return value
        else:
            return None

    # Update/add the value of key 'data'
    def set_data(self, data):
        self._json_obj["data"] = data

    # Respond with the value of key 'endpointId', if it is present in self._json_obj
    def get_endpoint_id(self):
        value = self._json_obj.get("endpointId")
        if value:
            return value
        else:
            return None
        
    # Update/add the value of key 'endpointId'
    def set_endpoint_id(self, endpoint_id):
        self._json_obj["endpointId"] = endpoint_id

    # Respond with a dictionary containing key-value pairs of a message
    def to_map(self):
        h_map = dict()
        if self.get_to() is not None:
            h_map["to"] = self.get_to()

        if self.get_from() is not None:
            h_map["from"] = self.get_from()

        if self.get_type() is not None:
            h_map["type"] = self.get_type()

        if self.get_target() is not None:
            h_map["target"] = self.get_target()

        if self.get_data() is not None:
            h_map["data"] = self.get_data()

        if self.get_message_id() is not None:
            h_map["messageId"] = self.get_message_id()

        if self.get_endpoint_id() is not None:
            h_map["endpointId"] = self.get_endpoint_id()

        for field in self._reflect_fields:
            data = self._json_obs.get(field)
            if data is not None:
                h_map[field] = data

        for key, value in self._extra_fields.iteritems():
            h_map[key] = value
        
        if self._changed:
            h_map["changed"] = True
        
        return h_map

    # Respond with the value of key 'target', if it is present in self._json_obj
    def get_target(self):
        value = self._json_obj.get("target")
        if value:
            return value
        else:
            return None
        
    # Update/add the value of key 'target'
    def set_target(self, target):
        self._json_obj["target"] = target

    # Respond with the value of key 'messageId', if it is present in self._json_onj
    def get_message_id(self):
        value = self._json_obj.get("messageId")
        if value:
            return value
        else:
            return None

    # Update/add the value of key 'messageId'
    def set_message_id(self, msg_id):
        self._json_obj["messageId"] = msg_id

    # Respond with the value of self._client_id
    @property
    def client_id(self):
        return self._client_id

    # Update value of self._client_id
    @client_id.setter
    def client_id(self, client_id):
        self._client_id = client_id

    
    def is_in_scope(self):
        return False

    def is_force_intercept(self):
        return False
    
    # Respond with the value of self._changed
    @property
    def changed(self):
        return self._changed
    
    # Update the value of self._changed
    @changed.setter
    def changed(self, changed):
        self._changed = changed

    # Respond with the value of self._state
    @property
    def state(self):
        return self._state

    # Update the value of self._state
    @state.setter
    def state(self, state):
        self._state = state

    # Update key-value pair in self._extra_fields and self._json_obj depending on the value of 'value' argument
    def set_key_value(self, key, value):
        if value is None:
            self._extra_fields.pop(key, None)
            self._json_obj.pop(key, None)
        else:
            self._extra_fields[key] = value
            self._json_obj[key] = value

    # Respond with the value of 'key' argument as json data
    def get_json(self, key):
        return json.dumps(self._json_obj.get(key))

    # Respond with a boolean if self._json_obj contains 'key' or not 
    def get_bool(self, key):
        if self._json_obj.has_key(key):
            return True
        else:
            return False
        
    # Respond with self._extra_fields list DS 
    @property
    def extra_fields(self):
        return self._extra_fields
