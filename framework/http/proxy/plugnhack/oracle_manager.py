class OracleManager(self):
    """
    OracleManager handles oracle actions. Save oracle listeners, 
    remove listeners, register oracle.
    """
    def __init__(self):
        self._oracle_map = dict()
        self._listeners = list()
        self._id = 0


    def register_oracle(self, data):
        # data parameter is a dictionary
        # increment _id parameter
        self._id = self._id + 1
        # _id incremented value will be the key in oracle_map
        key = self._id
        # add value 'data' for 'key'
        self.oracle_map[key] = data

        return key


    def data_from_oracle_map(self, data_id):
        # Retrieve value for key 'data_id'
        return self._oracle_map.get(data_id)


    def clear_data_oracle_map(self, data_id):
        # Delete key-value pair from oracle_map
        try:
            del self._oracle_map[data_id]
        except KeyError as e:
            self.Core.write_event(e.parameter + "\n", 'a')


    def reset(self):
        # Set oracle_map and id to default 
        self._oracle_map = dict()
        self._id = 0


    def add_oracle_listener(self, listener):
        # Add new oracle listener
        self._listeners.append(listener)



    def remove_oracle_listener(self, listener):
        # Remove oracle listener
        try:
            self._listeners.remove(listener)
        except ValueError as e:
            self.Core.write_event(e.parameter + "\n", 'a')


    def oracle_invoked(self, oracle_id):
        # For each listener in _listeners call oracle_invoked method with oracle_id parameter
        for listener in self._listeners:
            listener.oracle_invoked(oracle_id)
