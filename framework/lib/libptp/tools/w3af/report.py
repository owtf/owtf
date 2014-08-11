"""

.. module:: report
    :synopsis: Specialized Report class for W3AF.

.. moduleauthor:: Tao Sauvage

"""

from framework.lib.libptp import constants
from framework.lib.libptp.report import AbstractReport
from framework.lib.libptp.tools.w3af.parser import W3AFXMLParser


class W3AFReport(AbstractReport):
    """Retrieve the information of a W3AF report."""

    #: :class:`str` -- Name of the tool.
    __tool__ = 'w3af'
    #: :class:`list` -- Available parsers for W3AF.
    __parsers__ = [W3AFXMLParser]

    HIGH = 'High'
    MEDIUM = 'Medium'
    LOW = 'Low'
    INFO = 'Information'

    # Convert the W3AF's ranking scale to an unified one.
    RANKING_SCALE = {
        HIGH: constants.HIGH,
        MEDIUM: constants.MEDIUM,
        LOW: constants.LOW,
        INFO: constants.INFO}

    def __init__(self, *args, **kwargs):
        AbstractReport.__init__(self, *args, **kwargs)

    @classmethod
    def is_mine(cls, pathname, filename='*.xml'):
        """Check if it is a W3AF report and if it can handle it.

        :param str pathname: Path to the report directory.
        :param str filename: Regex matching the report file.

        :return: `True` if it supports the report, `False` otherwise.
        :rtype: :class:`bool`

        """
        fullpath = cls._recursive_find(pathname, filename)
        if not fullpath:
            return False
        fullpath = fullpath[0]  # Only keep the first file.
        return AbstractReport._is_parser(cls.__parsers__, fullpath)

    def parse(self, pathname=None, filename='*.xml'):
        """Parse a W3AF report.

        :param str pathname: Path to the report directory.
        :param str filename: Regex matching the report file.

        :return: List of dicts where each one represents a vuln.
        :rtype: :class:`list`

        """
        # Reconstruct the path to the report if any.
        self.fullpath = self._recursive_find(pathname, filename)
        if not self.fullpath:
            return []
        self.fullpath = self.fullpath[0]
        # Find the corresponding parser.
        self._init_parser(self.fullpath)
        # Parse specific stuff.
        self.metadata = self.parser.parse_metadata()
        self.vulns = self.parser.parse_report(self.RANKING_SCALE)
        # TODO: Return something like an unified version of the report.
        return self.vulns
