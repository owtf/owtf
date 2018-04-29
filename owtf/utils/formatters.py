"""
owtf.utils.formatters
~~~~~~~~~~~~~~~~~~~~~

CLI string formatting
"""

import logging

# CUSTOM LOG LEVELS
LOG_LEVEL_TOOL = 25

# Terminal colors
TERMINAL_COLOR_BLUE = "\033[94m"
TERMINAL_COLOR_GREEN = "\033[92m"
TERMINAL_COLOR_YELLOW = "\033[93m"
TERMINAL_COLOR_RED = "\033[91m"
TERMINAL_COLOR_END = "\033[0m"
TERMINAL_COLOR_LIGHT_BLUE = "\033[96m"


class ConsoleFormatter(logging.Formatter):
    """
    Custom formatter to show logging messages differently on Console
    """

    error_fmt = TERMINAL_COLOR_RED + "[-] {}" + TERMINAL_COLOR_END
    warn_fmt = TERMINAL_COLOR_YELLOW + "[!] {}" + TERMINAL_COLOR_END
    debug_fmt = TERMINAL_COLOR_GREEN + "[*] {}" + TERMINAL_COLOR_END
    info_fmt = TERMINAL_COLOR_BLUE + "[+] {}" + TERMINAL_COLOR_END

    def format(self, record):
        """ Choose format according to record level

        :param record: Record to format
        :type record: `str`
        :return: Formatted string
        :rtype: `str`
        """

        # Replace the original message with one customized by logging level
        if record.levelno == logging.DEBUG:
            record.msg = self.debug_fmt.format(record.msg)
        elif record.levelno == logging.INFO:
            record.msg = self.info_fmt.format(record.msg)
        elif record.levelno == logging.ERROR:
            record.msg = self.error_fmt.format(record.msg)
        elif record.levelno == logging.WARN:
            record.msg = self.warn_fmt.format(record.msg)

        # Call the original formatter class to do the grunt work
        result = super(ConsoleFormatter, self).format(record)

        return result


class FileFormatter(logging.Formatter):
    """
    Custom formatter for log files
    """

    def __init__(self, *args, **kwargs):
        super(FileFormatter, self).__init__()
        self._fmt = "[%(levelname)s] [%(asctime)s] " + "[File '%(filename)s', line %(lineno)s, in %(funcName)s] -" + " %(message)s"
