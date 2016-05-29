#!/usr/bin/env python
import logging

# CUSTOM LOG LEVELS
LOG_LEVEL_TOOL = 25

# Terminal colors
TERMINAL_COLOR_BLUE = '\033[94m'
TERMINAL_COLOR_GREEN = '\033[92m'
TERMINAL_COLOR_YELLOW = '\033[93m'
TERMINAL_COLOR_RED = '\033[91m'
TERMINAL_COLOR_END = '\033[0m'


class ConsoleFormatter(logging.Formatter):
    """
    Custom formatter to show logging messages differently on Console
    """

    error_fmt = TERMINAL_COLOR_RED + "[!] %(message)s" + TERMINAL_COLOR_END
    warn_fmt = TERMINAL_COLOR_YELLOW + "[*] %(message)s" + TERMINAL_COLOR_END
    debug_fmt = TERMINAL_COLOR_GREEN + "[+] %(message)s" + TERMINAL_COLOR_END
    info_fmt = TERMINAL_COLOR_BLUE + "[-] %(message)s" + TERMINAL_COLOR_END

    def format(self, record):

        # Save the original format configured by the user
        # when the logger formatter was instantiated
        format_orig = self._fmt

        # Replace the original format with one customized by logging level
        if record.levelno == logging.DEBUG:
            self._fmt = self.debug_fmt
        elif record.levelno == logging.INFO:
            self._fmt = self.info_fmt
        elif record.levelno == logging.ERROR:
            self._fmt = self.error_fmt
        elif record.levelno == logging.WARN:
            self._fmt = self.warn_fmt

        # Call the original formatter class to do the grunt work
        result = super(ConsoleFormatter, self).format(record)

        # Restore the original format configured by the user
        self._fmt = format_orig

        return result


class FileFormatter(logging.Formatter):
    """
    Custom formatter for log files
    """
    def __init__(self, *args, **kwargs):
        super(FileFormatter, self).__init__()
        self._fmt = "[%(levelname)s] [%(asctime)s] " + \
            "[File '%(filename)s', line %(lineno)s, in %(funcName)s] -" + \
            " %(message)s"
