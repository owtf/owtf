"""

.. module:: report
    :synopsis: Specialized Report class for DirBuster.

.. moduleauthor:: Tao Sauvage

"""

from framework.lib.libptp.report import AbstractReport
from framework.lib.libptp.tools.dirbuster.parser import DirbusterParser


class DirbusterReport(AbstractReport):
    """Retrieve the information of a DirBuster report."""

    #: :class:`str` -- Name of the tool.
    __tool__ = 'dirbuster'
    #: :class:`list` -- Available parsers for DirBuster.
    __parsers__ = [DirbusterParser]

    def __init__(self, *args, **kwargs):
        AbstractReport.__init__(self, *args, **kwargs)

    # TODO: Properly check if it is a DirBuster report.
    @classmethod
    def is_mine(cls, pathname=None, filename='DirBuster-Report*'):
        fullpath = cls._recursive_find(pathname, filename)
        if not fullpath:
            return False
        fullpath = fullpath[0]  # Only keep the first file.
        return AbstractReport._is_parser(cls.__parsers__, fullpath)

    def parse(self, pathname=None, filename='DirBuster-Report*'):
        """Parse a Dirbuster report.

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
        self.vulns = self.parser.parse_report()
        # TODO: Return something like an unified version of the report.
        return self.vulns
