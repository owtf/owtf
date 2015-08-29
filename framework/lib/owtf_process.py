#!/usr/bin/env python
"""
Consists of owtf process class and its manager
"""
import logging
from multiprocessing import Process, current_process, Queue
from framework.dependency_management.dependency_resolver import BaseComponent


class OWTFProcess(Process, BaseComponent):
    """
    Implementing own proxy of Process for better control of processes launched
    from OWTF both while creating and terminating the processes
    """
    def __init__(self, **kwargs):
        """
        Ideally not to override this but can be done if needed. If overridden
        please give a call to super() and make sure you run this
        """
        self.core = self.get_component("core")  # Attach core
        self.db = self.get_component("db")
        self.plugin_handler = self.get_component("plugin_handler")
        self.poison_q = Queue()
        self._process = None
        for key in kwargs.keys():  # Attach all kwargs to self
            setattr(self, key, kwargs.get(key, None))
        super(OWTFProcess, self).__init__()

    def make_daemon(self):
        """
        Method used to set daemon value to true
        """
        self.daemon = True

    def initialize(self, **kwargs):
        """
        Supposed to be overridden if user wants to initialize something
        """
        pass

    def run(self):
        """
        This method must not be overridden by user
        + Set proper logger with file handler and Formatter
        + Launch process specific code
        """
        # ------ DB Reinitialization ------ #
        try:
            self.db.create_session()
            # ------ Logging initialization ------ #
            self.core.enable_logging()
            # - Finally run process specific code - #
            self.pseudo_run()
        except KeyboardInterrupt, e:
            # In case of listing plugins
            pass

    def pseudo_run(self):
        """
        This method must be overridden by user with the process related code
        """
        pass
