"""

.. module:: report
    :synopsis: Specialized Report class for Skipfish.

.. moduleauthor:: Tao Sauvage

"""

import os

from framework.lib.libptp.exceptions import ReportNotFoundError
from framework.lib.libptp import constants
from framework.lib.libptp.report import AbstractReport
from framework.lib.libptp.tools.skipfish.parser import SkipfishJSParser


class SkipfishReport(AbstractReport):
    """Retrieve the information of a Skipfish report."""

    #: :class:`str` -- Name of the tool.
    __tool__ = 'skipfish'
    #: :class:`list` -- Available parsers for Skipfish.
    __parsers__ = [SkipfishJSParser]
    _reportfile = 'samples.js'
    _metadatafile = 'summary.js'

    HIGH = 4
    MEDIUM = 3
    LOW = 2
    WARNINGS = 1
    INFO = 0

    # Convert the Skipfish's ranking scale to an unified one.
    RANKING_SCALE = {
        HIGH: constants.HIGH,
        MEDIUM: constants.MEDIUM,
        LOW: constants.LOW,
        WARNINGS: constants.INFO,
        INFO: constants.INFO}

    def __init__(self, *args, **kwargs):
        AbstractReport.__init__(self, *args, **kwargs)

    @classmethod
    def is_mine(cls, pathname):
        """Check if it is a Skipfish report and if I can handle it.

        :param str pathname: Path to the report directory.

        :return: `True` if it supports the report, `False` otherwise.
        :rtype: :class:`bool`

        """
        metadatafile = cls._recursive_find(pathname, cls._metadatafile)
        if not metadatafile:
            return False
        metadatafile = metadatafile[0]
        reportfile = cls._recursive_find(pathname, cls._reportfile)
        if not reportfile:
            return False
        reportfile = reportfile[0]
        return AbstractReport._is_parser(
            cls.__parsers__,
            metadatafile,
            reportfile)

    def parse(self, pathname=None):
        """Parse a Skipfish report.

        :param str pathname: Path to the report directory.
        :return: List of dicts where each one represents a vuln.
        :rtype: :class:`list`

        :raises: :class:`ReportNotFoundError` -- if the report is not
            supported.

        """
        if (pathname is None or not os.path.isdir(pathname)):
            raise ReportNotFoundError(
                'A directory to the report MUST be specified.')
        # Find metadata file.
        metadatafile = self._recursive_find(pathname, self._metadatafile)
        if not metadatafile:
            raise ReportNotFoundError('The metadata file is not found.')
        self.metadatafile = metadatafile[0]
        # Find report file.
        reportfile = self._recursive_find(pathname, self._reportfile)
        if not reportfile:
            raise ReportNotFoundError('The report file is not found.')
        self.reportfile = reportfile[0]
        # Find the corresponding parser.
        # FIXME: Find a nice way to check for a correct parser.
        self._init_parser(self.metadatafile, self.reportfile)
        # Parser everything.
        self.metadata = self.parser.parse_metadata()
        self.vulns = self.parser.parse_report(self.RANKING_SCALE)
        return self.vulns
