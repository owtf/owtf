"""

.. module:: parser
    :synopsis: Specialized Parser classes for DirBuster.

.. moduleauthor:: Tao Sauvage

"""

import re

from framework.lib.libptp.parser import LineParser
from framework.lib.libptp.tools.dirbuster.signatures import DIRECTORIES, FILES


class DirbusterParser(LineParser):
    """DirBuster specialized parser."""
    #: :class:`str` -- Name of the tool.
    __tool__ = 'dirbuster'
    #: :class:`str` -- Format of DirBuster reports it supports.
    __format__ = 'dirbuster'
    #: :class:`list` -- DirBuster versions it supports.
    __version__ = ['1.0-RC1']

    #: :class:`str` -- Regex matching DirBuster section separator.
    _re_sep = r"^-*$"
    #: :class:`str` -- Regex matching DirBuster version.
    _re_version = r"^DirBuster (?P<version>[0-9]+\.[0-9]+(-RC[0-9])?) - Report$"
    #: :class:`str` -- Regex matching DirBuster directories status code.
    _re_dir_status = r"^Dirs found with a (?P<status>[0-9]{3}) response:$"
    #: :class:`str` -- Regex matching DirBuster files status code.
    _re_file_status = r"^Files found with a (?P<status>[0-9]{3}) responce:$"

    def __init__(self, pathname):
        LineParser.__init__(self, pathname)

    # TODO: Properly check the supported versions.
    @classmethod
    def is_mine(cls, pathname=None, filename='DirBuster-Report*'):
        stream = cls.handle_file(pathname)
        if stream and re.match(cls._re_version, stream[0]):
            return True
        return False

    # TODO: Properly retrieve the metadatas.
    def parse_metadata(self):
        return {}

    def parse_report(self):
        """Parser the results of a DirBuster report.

        :return: List of dicts where each one represents a vuln.
        :rtype: :class:`list`

        """
        # Retrieve the results from the report.
        discoveries = {'directories': [], 'files': [], 'errors': []}
        type_disco = 'errors'
        status_code = -1
        for line in self.stream:
            match_dir_status = re.match(self._re_dir_status, line)
            match_file_status = re.match(self._re_file_status, line)
            if match_dir_status:
                type_disco = 'directories'
                status_code = match_dir_status.group('status')
            elif match_file_status:
                type_disco = 'files'
                status_code = match_file_status.group('status')
            elif line.startswith('/'):  # This line contains a discovery
                status = int(status_code)
                # If this is the section of the successful ones (2xx).
                if status >= 200 and status < 300:
                    discoveries[type_disco].append(line)
        # Match found discoveries against signatures database.
        vulns = []
        matching = ((DIRECTORIES, 'directories'), (FILES, 'files'))
        for signatures, type_disco in matching:
            try:
                signatures = signatures.iteritems()
            except AttributeError:  # Python3
                signatures = signatures.items()
            for signature, ranking in signatures:
                matched = [
                    True
                    for disco in discoveries[type_disco]
                    if re.match(signature, disco)]
                if True in matched:
                    vulns.extend([{'ranking': ranking}])
        return vulns
