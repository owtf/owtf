#!/usr/bin/env python
"""

owtf is an OWASP+PTES-focused try to unite great tools and facilitate pen testing
Copyright (c) 2011, Abraham Aranguren <name.surname@gmail.com> Twitter: @7a_ http://7-a.org
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.
    * Neither the name of the copyright owner nor the
      names of its contributors may be used to endorse or promote products
      derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.  Manager Process

"""
import logging


class ConsoleFormatter(logging.Formatter):
    """
    Custom formatter to show logging messages differently on Console
    """

    error_fmt = "[!] %(message)s"  # Error format
    warn_fmt = "%(message)s"  # This format is kept for tool outputs :P
    debug_fmt = "[+] %(message)s"  # Debug format
    info_fmt = "[-] %(message)s"  # Info format

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
