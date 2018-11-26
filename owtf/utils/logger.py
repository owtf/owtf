"""
owtf.utils.logger
~~~~~~~~~~~~~~~~~

"""
import sys
import logging
import multiprocessing

from owtf.utils.file import catch_io_errors, get_log_path, FileOperations, get_logs_dir
from owtf.utils.formatters import ConsoleFormatter, FileFormatter

try:
    from raven.handlers.logging import SentryHandler
    from raven.conf import setup_logging
except ImportError:
    SentryHandler = None

__all__ = ["OWTFLogger"]


class OWTFLogger(object):

    def __init__(self):
        # Bootstrap log files directory.
        FileOperations.create_missing_dirs(get_logs_dir())
        self.file_handler = catch_io_errors(logging.FileHandler)

    def enable_logging(self, **kwargs):
        """Enables both file and console logging

         .. note::
            + process_name <-- can be specified in kwargs
            + Must be called from inside the process because we are kind of overriding the root logger

        :param kwargs: Additional arguments to the logger
        :type kwargs: `dict`
        :return:
        :rtype: None
        """
        process_name = kwargs.get("process_name", multiprocessing.current_process().name)
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)

        file_handler = self.file_handler(get_log_path(process_name), mode="w+")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(FileFormatter())
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel(logging.INFO)
        stream_handler.setFormatter(ConsoleFormatter())
        # Replace any old handlers
        logger.handlers = [file_handler, stream_handler]

    def disable_console_logging(self, **kwargs):
        """Disables console logging

        .. note::
            Must be called from inside the process because we should remove handler for that root logger. Since we add
            console handler in the last, we can remove the last handler to disable console logging

        :param kwargs: Additional arguments to the logger
        :type kwargs: `dict`
        :return:
        :rtype: None
        """
        logger = logging.getLogger()
        if isinstance(logger.handlers[-1], logging.StreamHandler):
            logger.removeHandler(logger.handlers[-1])
