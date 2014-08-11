"""

.. module:: parser
    :synopsis: Specialized Parser classes for Arachni.

.. moduleauthor:: Tao Sauvage

"""

from framework.lib.libptp.exceptions import NotSupportedVersionError
from framework.lib.libptp.parser import XMLParser


class ArachniXMLParser(XMLParser):
    """Arachni XML specialized parser."""

    #: :class:`str` -- Name of the tool.
    __tool__ = 'arachni'
    #: :class:`str` -- Format of Arachni reports it supports.
    __format__ = 'xml'
    #: :class:`list` -- Arachni versions it supports.
    __version__ = ['0.4.6', '0.4.7']

    def __init__(self, pathname):
        XMLParser.__init__(self, pathname)

    @classmethod
    def is_mine(cls, pathname):
        """Check if it is a supported Arachni report.

        :param str pathname: Path to the report file.

        :return: `True` if it supports the report, `False` otherwise.
        :rtype: :class:`bool`

        """
        try:
            stream = cls.handle_file(pathname)
        except ValueError:
            return False
        if not cls.__tool__ in stream.tag:
            return False
        return True

    def parse_metadata(self):
        """Parse the metadatas of the report.

        :return: The metadatas of the report.
        :rtype: dict

        :raises: :class:`NotSupportedVersionError` -- if it does not support
            the version of this report.

        """
        # Find the version of Arachni.
        version = self.stream.find('.//version')
        # Reconstruct the metadata
        # TODO: Retrieve the other metadata likes the date, etc.
        metadata = {version.tag: version.text,}
        if self.check_version(metadata):
            return metadata
        else:
            raise NotSupportedVersionError(
                'PTP does NOT support this version of Arachni.')

    def parse_report(self, scale):
        """Parse the results of the report.

        :return: List of dicts where each one represents a vuln.
        :rtype: :class:`list`

        """
        return [
            {'ranking': scale[vuln.find('.//severity').text]}
            for vuln in self.stream.find('.//issues')]
