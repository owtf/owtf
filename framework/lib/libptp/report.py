"""

.. module:: report
    :synopsis: The Report class will be the summary of a complete report
        provided by a pentesting tool.

.. moduleauthor:: Tao Sauvage

"""


import os
import fnmatch

from framework.lib.libptp.exceptions import NotSupportedVersionError
from framework.lib.libptp.constants import UNKNOWN, RANKING_SCALE


class AbstractReport(object):

    """Abstract representation of a report provided by a pentesting tool.

    .. note::

        This class will be extended for each pentesting tool. That way, each
        tool will add its own report/parsing specificities.

    """

    #: :class:`str` -- Name of the tool.
    __tool__ = None
    #: :class:`tuple` -- Available parsers for the tool.
    __parsers__ = None

    def __init__(self, vulns=None):
        """Self-explanatory."""
        #: The current parser the report is using.
        self.parser = None
        #: List of dictionaries of the results found in the report.
        self.vulns = [] or vulns

    def __str__(self):
        return ', '.join([info.__str__() for info in self.vulns])

    @classmethod
    def is_mine(cls, pathname, filename=None):
        """Check if it is a report from the tool this class supports.

        :param str pathname: The path to the report.
        :param str filename: The name of the report file.
        :return: `True` if this class supports this tool, `False` otherwise.
        :rtype: :class:`bool`

        """
        return False

    @classmethod
    def _is_parser(cls, parsers, *args, **kwargs):
        """Check if a parser exists for that report.

        :param :class:`list` parsers: The available parsers of this
            class.
        :param list args: Arguments that will be pass to the parser.
        :param dict kwargs: Arguments that will be pass to the parser.
        :return: `True` if this class has a parser for this tool, `False`
            otherwise.
        :rtype: :class:`bool`

        """
        if parsers is not None:
            for parser in parsers:
                if parser.is_mine(*args, **kwargs):
                    return True
        return False

    @staticmethod
    def _recursive_find(pathname='./', file_regex='*', early_break=True):
        """Retrieve the full path to the report.

        The search occurs in the directory `pathname`.
        :param str pathname: The root directory where to start the search.
        :param re file_regex: The regex that will be matched against all files
            from within `pathname`.
        :param bool early_break: Stop the search as soon as a file has been
            matched.
        :return: A list of paths to matched files starting from
            `pathname`.
        :rtype: :class:`list`

        """
        founds = []
        for base, _, files in os.walk(pathname):
            matched_files = fnmatch.filter(files, file_regex)
            founds.extend(
                os.path.join(base, matched_file)
                for matched_file in matched_files)
            if founds and early_break:
                break
        return founds

    def _init_parser(self, *args, **kwargs):
        """Instantiate the correct parser for the report.

        :param list args: Arguments that will be pass to the parser.
        :param dict kwargs: Arguments that will be pass to the parser.

        :raises: :class:`NotSupportedVersionError` -- if it does not support
            that version of the tool.

        """
        for parser in self.__parsers__:
            try:
                if parser.is_mine(*args, **kwargs):
                    self.parser = parser(*args, **kwargs)
            except TypeError:
                pass
            except NotSupportedVersionError:
                pass
        if self.parser is None:
            raise NotSupportedVersionError

    def get_highest_ranking(self):
        """Return the highest ranking id of the report.

        :return: the risk id of the highest ranked vulnerability
            referenced in the report.
        :rtype: :class:`int`

        .. note::

            The risk id varies from `0` (not ranked/unknown) to `n` (the
            highest risk).

        """
        if not self.vulns:
            return UNKNOWN
        return max(
            RANKING_SCALE.get(vuln.get('ranking')) for vuln in self.vulns)

    def parse(self):
        """Abstract parser that will parse the report of a tool.

        :raises: :class:`NotImplementedError` -- because this is an abstract
            method.

        """
        raise NotImplementedError('The parser MUST be define for each tool.')
