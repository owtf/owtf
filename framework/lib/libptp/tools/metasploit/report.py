"""

.. module:: report
    :synopsis: Specialized Report class for Metasploit.

.. moduleauthor:: Tao Sauvage

"""

from framework.lib.libptp.report import AbstractReport
from framework.lib.libptp.tools.metasploit.parser import MetasploitParser


class MetasploitReport(AbstractReport):
    """Retrieve the information of a Metasploit report."""

    #: :class:`str` -- Name of the tool.
    __tool__ = 'metasploit'
    #: :class:`list` -- Available parsers for Metasploit.
    __parsers__ = [MetasploitParser]

    def __init__(self, *args, **kwargs):
        AbstractReport.__init__(self, *args, **kwargs)

    # TODO: Properly check if it is a Metasploit report.
    @classmethod
    def is_mine(cls, pathname, filename='*.txt', plugin=''):
        if plugin:
            return True
        return False

    def parse(self, pathname=None, filename='*.txt', plugin=''):
        """Parse a Metasploit report.

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
        self._init_parser(self.fullpath, filename, plugin)
        # Parse specific stuff.
        self.metadata = self.parser.parse_metadata()
        self.vulns = self.parser.parse_report()
        # TODO: Return something like an unified version of the report.
        return self.vulns
