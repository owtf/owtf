"""

.. module:: report
    :synopsis: Specialized Report class for Arachni.

.. moduleauthor:: Tao Sauvage

"""

from framework.lib.libptp import constants
from framework.lib.libptp.report import AbstractReport
from framework.lib.libptp.tools.arachni.parser import ArachniXMLParser


class ArachniReport(AbstractReport):
    """Retrieve the information of an Arachni report."""

    #: :class:`str` -- Name of the tool.
    __tool__ = 'arachni'
    #: :class:`list` -- Available parsers for Arachni.
    __parsers__ = [ArachniXMLParser]

    HIGH = 'High'
    MEDIUM = 'Medium'
    LOW = 'Low'
    INFO = 'Informational'

    # Convert the Arachni's ranking scale to an unified one.
    RANKING_SCALE = {
        HIGH: constants.HIGH,
        MEDIUM: constants.MEDIUM,
        LOW: constants.LOW,
        INFO: constants.INFO}

    def __init__(self, *args, **kwargs):
        AbstractReport.__init__(self, *args, **kwargs)

    @classmethod
    def is_mine(cls, pathname, filename='*.xml'):
        """Check if it is an Arachni report and if it can handle it.

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
        """Parse an Arachni report.

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
