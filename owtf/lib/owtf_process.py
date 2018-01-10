"""
owtf.lib.owtf_process
~~~~~~~~~~~~~~~~~~~~~

Consists of owtf process class and its manager
"""

import logging
from multiprocessing import Process, Queue
import signal
import sys
import multiprocessing
import os

from owtf.db.database import get_scoped_session
from owtf.utils.logger import logger
from owtf.utils.process import kill_children


def signal_handler(signal, frame):
    logging.warn('Cleaning up %s', multiprocessing.current_process().name)
    sys.exit(0)


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
        self.output_q = None
        self.session = get_scoped_session()
        self.logger = logger
        signal.signal(signal.SIGINT, signal_handler)
        self.logger.setup_logging()
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
            self.pseudo_run()
        except KeyboardInterrupt:
            # In case of interrupt while listing plugins
            pass

    def pseudo_run(self):
        """
        This method must be overridden by user with the process related code
        """
        pass
