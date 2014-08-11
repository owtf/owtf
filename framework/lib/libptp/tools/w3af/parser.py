"""

.. module:: parser
    :synopsis: Specialized Parser classes for W3AF.

.. moduleauthor:: Tao Sauvage

"""

import re
import re

from framework.lib.libptp.exceptions import NotSupportedVersionError
from framework.lib.libptp.parser import XMLParser


class W3AFXMLParser(XMLParser):
    """W3AF XML specialized parser."""

    #: :class:`str` -- Name of the tool.
    __tool__ = 'w3af'
    #: :class:`str` -- Format of W3AF reports it supports.
    __format__ = 'xml'
    #: :class:`list` -- W3AF versions it supports.
    __version__ = ['1.6.0.2', '1.6.0.3']

    def __init__(self, pathname):
        XMLParser.__init__(self, pathname)
        self.re_version = re.compile(r'Version: (\S*)\s')

    @classmethod
    def is_mine(cls, pathname):
        """Check if it is a supported W3AF report.

        :param str pathname: Path to the report file.

        :return: `True` if it supports the report, `False` otherwise.
        :rtype: :class:`bool`

        """
        try:
            stream = cls.handle_file(pathname)
        except ValueError:
            return False
        if stream.find('.//w3af-version') is None:
            return False
        return True

    def parse_metadata(self):
        """Parse the metadatas of the report.

        :return: The metadatas of the report.
        :rtype: dict

        :raises: :class:`NotSupportedVersionError` -- if it does not support
            the version of this report.

        """
        raw_metadata = self.stream.find('.//w3af-version').text
        # Find the version of w3af.
        version = self.re_version.findall(raw_metadata)
        if len(version) >= 1:  # In case we found several version numbers.
            version = version[0]
        # Reconstruct the metadata
        # TODO: Retrieve the other metadata likes the date, etc.
        metadata = {'version': version,}
        if self.check_version(metadata):
            self.metadata = metadata
        else:
            raise NotSupportedVersionError(
                'PTP does NOT support this version of ' + self.__tool__ + '.')

    def parse_report(self, scale):
        """Parse the results of the report.

        :return: List of dicts where each one represents a vuln.
        :rtype: :class:`list`

        """
        return [
            {'ranking': scale[vuln.get('severity')],}
            for vuln in self.stream.findall('.//vulnerability')]
