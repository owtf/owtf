"""
owtf.lib.owtf_process
~~~~~~~~~~~~~~~~~~~~~

Consists of owtf process class and its manager
"""

from multiprocessing import Process, Queue

from owtf.dependency_management.dependency_resolver import BaseComponent


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
        for key in list(kwargs.keys()):  # Attach all kwargs to self
            setattr(self, key, kwargs.get(key, None))
        super(OWTFProcess, self).__init__()

    def initialize(self, **kwargs):
        """
        Supposed to be overridden if user wants to initialize something
        """
        pass

    def run(self):
        """This method must not be overridden by user

        .note::

        + Set proper logger with file handler and Formatter
        + Launch process specific code

        :return: None
        :rtype: None
        """
        """

        """
        try:
            # ------ DB Reinitialization ------ #
            self.db.create_session()
            # ------ Logging initialization ------ #
            self.core.enable_logging()
            # - Finally run process specific code - #
            self.pseudo_run()
        except KeyboardInterrupt:
            # In case of interrupt while listing plugins
            pass

    def pseudo_run(self):
        """
        This method must be overridden by user with the process related code
        """
        pass
