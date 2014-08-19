class MonitoredPage(object):
    """
    MonitoredPage saves information about monitored page, if it is
    active/inactive, heartbeat interval, last message received,
    performed actions as monitor/intercept post messages, 
    monitor/intercept events.
    """
    def __init__(self, page_id=None, message=None, last_message=None, index=None):
        # id of monitored page
        self._page_id = page_id or None
        # messaged received from monitored page
        self._message = message or None
        # last message from monitored page
        self._last_message = last_message or None
        # index of monitored page
        self._index = index or None
        # page is active or inactive
        self._active = True
        # hearbeat interval of monitored page
        self._heartbeat = 0
        # monitor post messages of monitored page
        self._monitor_post_messages = True
        # intercept post messages of monitored page
        self._intercept_post_messages = True
        # monitor events of monitored page
        self._monitor_events = True
        # intercept events of monitored page
        self._intercept_events = True

    
    # Respond with page id
    @property
    def page_id(self):
        return self._page_id


    # Update page id
    @page_id.setter
    def page_id(self, param_id):
        self._page_id = param_id

    
    # Respond with message instance variable
    @property
    def message(self):
        return self._message

    # Update the value of message instance variable 
    @message.setter
    def message(self, message):
        self._message = message

    # Respond with last_message value
    @property
    def last_message(self):
        return self._last_message

    # Update last_message value
    @last_message.setter
    def last_message(self, last_msg):
        self._last_message = last_msg

    # Respond with the value of active (True is page is active)
    @property
    def active(self):
        return self._active

    # Update active value
    @active.setter
    def active(self, value):
        self._active = value

    
    # Respond with 'url' from message
    def get_uri(self):
        return self._message.get_argument('url')

    # Respond with heartbeat value of page
    @property
    def heartbeat(self):
        return self._heartbeat

    # Update hearbeat value of page
    @heartbeat.setter
    def heartbeat(self, heartbeat):
        self._heartbeat = heartbeat

    # Respond with the value of monitor_post_messages
    @property
    def monitor_post_message(self):
        return self._monitor_post_messages

    # Update monitor_post_messages
    @monitor_post_messages.setter
    def monitor_post_messages(self, monitor_value):
        self._monitor_post_messages = monitor_value

    # Respond with the value of intercept_post_messages
    @property
    def intercept_post_messages(self):
        return self._intercept_post_messages

    # Update intercept_post_messages value
    @intercept_post_messages.setter
    def intercept_post_messages(self, intercept_value):
        self._intercept_post_messages = intercept_value

    # Respond with the value of monitor_events
    @property
    def monitor_events(self):
        return self._monitor_events

    # Update the value of monitor_events
    @monitor_events.setter
    def monitor_events(self, monitor_value):
        self._monitor_events = monitor_value

    # Respond with the value of intercept_post
    @property
    def intercept_events(self):
        return self._intercept_events
    
    # Update the value of intercept_events
    @intercept_events.setter
    def intercept_events(self, intercept_value):
        self._intercept_events = intercept_value

    # Respond with the value of page index
    @property
    def index(self):
        return self._index

    # Update page index value
    @index.setter
    def index(self, index):
        self._index = index
