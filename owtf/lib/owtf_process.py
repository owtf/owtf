"""
owtf.lib.owtf_process
~~~~~~~~~~~~~~~~~~~~~

Consists of owtf process class and its manager
"""
from multiprocessing import Process, Queue

from owtf.db.session import get_scoped_session
from owtf.utils.error import setup_signal_handlers
from owtf.plugin.runner import runner
from owtf.utils.logger import OWTFLogger

__all__ = ["OWTFProcess"]


class OWTFProcess(Process):
    """
    Implementing own proxy of Process for better control of processes launched
    from OWTF both while creating and terminating the processes
    """

    def __init__(self, **kwargs):
        """
        Ideally not to override this but can be done if needed. If overridden
        please give a call to super() and make sure you run this
        """
        self.poison_q = Queue()
        self._process = None
        self.session = get_scoped_session()
        self.plugin_handler = runner
        self.logger = OWTFLogger()
        setup_signal_handlers()
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

        Sets proper logger with file handler and Formatter
        and launches process specific code

        :return: None
        :rtype: None
        """
        try:
            self.logger.enable_logging()
            self.pseudo_run()
        except KeyboardInterrupt:
            # In case of interrupt while listing plugins
            pass

    def pseudo_run(self):
        """
        This method must be overridden by user with the process related code
        """
        pass
