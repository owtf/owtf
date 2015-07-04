class ClientConfigDialog(object):
    """
    ClientConfigDialog represents the dialog between OWTF and Plug-n-Hack probe
    of a specific monitored page.
    By default, Plug-n-Hack probe hearbeat interval is 1 second, monitor/intercept
    post messages set to 'True' and monitor/intercept events to 'True'.
    From Plug-n-Hack configuration page, user can change hearbeat interval, monitor
    or intercept actions. If default configuration is modified, probe must be
    notified about so it can act as user wants.
    """
    def __init__(self, ext, page, heartbeat=None, monitor_post=None, intercept_post=None, monitor_events=None, intercept_events=None):
        # self._extension instance variable offers message configuration methods.
        # It is a PlugnhackExtension object
        self._extension = ext
        # self._monitored_page instance variable offers information about a monitored page
        # It is a MonitoredPage object
        self._monitored_page = page
        # Configuration variables, their value is modified in Plug-n-Hack browser configuration page
        self._heartbeat = heartbeat or None
        self._monitor_post = monitor_post or None
        self._intercept_post = intercept_post or None
        self._monitor_events = monitor_events or None
        self._intercept_events = intercept_events or None


    def save(self):
        """
        This method compares configuration variables of a monitored page with
        configuration variables sent from Plug-n-Hack browser configuration page
        by user, if one of their values are different, then requests
        self._extension to create a response message and send it to probe.
        """
        # Compare heartbeat value of monitored page with hearbeat value from
        # browser configuration page
        if _monitored_page.heartbeat() != self._heartbeat:
            # If heartbeat values are different, monitored page heartbeat value
            # needs to be updated with the value desired by user
            _monitored_page.heartbeat(self._heartbeat)
            # Request client_config method to create a configuration message with
            # updated heartbeat value. Heartbeat value is multiplied by 1000
            # because value sent to probe must be in miliseconds. 1 s = 1000 ms
            self._extension.client_config(_monitored_page, "heartbeartInterval", _monitored_page.hearbeat() * 1000)
        
        # Compare monitorPostMessage of monitored page with monitorPostMessage
        # value from browser configuration page
        if _monitored_page.monitor_post_msg() != self._monitor_post:
            # If montorPostMessage values are different, monitored page
            # monitorPostMessage value needs to be updated with the value
            # desired by user
            _monitored_page.monitor_post_msg(self._monitor_post)
            # Request client_config method to create a configuration message with
            # updated monitorPostMessage value, monitorPostMessage value
            # is a boolean
            self._extension.client_config(_monitored_page, "monitorPostMessage", _monitored_page.monitor_post_msg())
            

        # Compare interceptPostMessage of monitored page with interceptPostMessage
        # value from browser configuration page
        if _monitored_page.intercept_post_msg() != self._intercept_post:
            # If interceptPostMessage values are different, monitored page
            # interceptPostMessage value needs to be updated with the value
            # desired by user
            _monitored_page.intercept_post_msg(self._intercept_post)
            # Request client_config method to create a configuration message with
            # updated interceptPostMessage value, interceptPostMessage value
            # is a boolean
            self._extension.client_config(_monitored_page, "interceptPostMessage", _monitored_page.intercept_post_msg())
            

        # Compare monitorEvents of monitored page with monitorEvents
        # value from browser configuration page
        if _monitored_page.monitor_events() != self._monitor_events:
            # If monitorEvents values are different, monitored page
            # monitorEvents value needs to be updated with the value
            # desired by user
            _monitored_page.monitor_events(self._monitor_events)
            # Request client_config method to create a configuration message with
            # updated monitorEvents value, monitorEvents value
            # is a boolean
            self._extension.client_config(_monitored_page, "monitorEvents", _monitored_page.monitor_events())


        # Compare interceptEvents of monitored page with interceptEvents
        # value from browser configuration page
        if _monitored_page.intercept_events() != self._intercept_events:
            # If interceptEvents values are different, monitored page
            # interceptEvents value needs to be updated with the value
            # desired by user
            _monitored_page.intercept_events(self._intercept_events)
            # Request client_config method to create a configuration message with
            # updated interceptEvents value, interceptEvents value
            # is a boolean
            self._extension.client_config(_monitored_page, "interceptEvents", _monitored_page.intercept_events())
