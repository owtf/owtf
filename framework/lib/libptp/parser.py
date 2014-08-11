"""

.. module:: parser
    :synopsis: The Parser class will extract the information contained in a
        report.

.. moduleauthor:: Tao Sauvage

"""


from lxml import etree
from lxml.etree import LxmlError


class AbstractParser(object):
    """Abstract representation of a parser."""

    #: :class:`str` -- Name of the tool.
    __tool__ = None
    #: :class:`str` -- Format of reports it supports.
    __format__ = None
    #: :class:`list` -- Versions it can supports.
    __version__ = None

    def __init__(self, pathname):
        """Initialize AbstractParser.

        :param str pathname: path to the report file.

        """
        #: i/o stream -- i/o stream of the report.
        self.stream = self.handle_file(pathname)

    @classmethod
    def handle_file(cls, pathname):
        """Process the report file(s) in order to create an i/o stream.

        :param str pathname: Path to the report file.

        :raises: :class:`NotImplementedError` because this is an abstract
            method.

        """
        raise NotImplementedError(
            "A parser MUST define the `handle_file` method.")

    @classmethod
    def is_mine(cls, *args, **kwargs):
        """Check if the parser supports the tool.

        :param list args: Arguments that will be pass to the parser.
        :param dict kwargs: Arguments that will be pass to the parser.

        :raises: :class:`NotImplementedError` because this is an abstract
            method.

        """
        raise NotImplementedError("A parser MUST define the `is_mine` method.")

    @classmethod
    def check_version(cls, metadata, key='version'):
        """Checks the version in the metadata against the supported one.

        :param dict metadata: The metadata in which to find the version.
        :param str key: The :attr:`metadata` key containing the version value.

        :return: `True` if it can parse the report, `False` otherwise.
        :rtype: :class:`bool`

        """
        if metadata[key] in cls.__version__:
            return True
        return False

    def parse_metadata(self):
        """Parse the metadata of a report.

        :raises: :class:`NotImplementedError` because this is an abstract
            method.

        """
        raise NotImplementedError(
            "A parser MUST define the `parse_metadata` method.")

    def parse_report(self):
        """Parse the discoveries of a report.

        :raises: :class:`NotImplementedError` because this is an abstract
            method.

        """
        raise NotImplementedError(
            "A parser MUST define the `parse_report` method.")


class XMLParser(AbstractParser):
    """Specialized parser for XML formatted report."""

    #: str -- XMLParser only supports XML files.
    __format__ = 'xml'

    def __init__(self, pathname):
        """Initialize XMLParser.

        :param str pathname: path to the report file.

        """
        AbstractParser.__init__(self, pathname)

    @classmethod
    def handle_file(cls, pathname):
        """Specialized file handler for XML files.

        :param str pathname: path to the report file.
        :raises ValueError: if the report file has not the right extension.
        :raises LxmlError: if Lxml cannot parse the XML file.

        """
        if not pathname.endswith(cls.__format__):
            raise ValueError(
                "This parser only supports '%s' files" % cls.__format__)
        return etree.parse(pathname).getroot()


class FileParser(AbstractParser):
    """Specialized parser for general report."""

    #: str -- A file can have any extension.
    __format__ = ''

    def __init__(self, pathname):
        """Initialized FileParser.

        :param str pathname: path to the report file.

        """
        AbstractParser.__init__(self, pathname)

    @classmethod
    def handle_file(cls, pathname):
        """Specialized file handler for general files.

        :param str pathname: path to the report file.
        :raises OSError: if an error occurs when opening/reading the report
            file.
        :raises IOError: if an error occurs when opening/reading the report
            file.

        """
        with open(pathname, 'r') as f:
            return f.read()


class LineParser(AbstractParser):
    """Specialized parser for general report read line by line."""

    #: str -- A file can have any extension.
    __format__ = ''

    def __init__(self, pathname):
        """Initialized LineParser.

        :param str pathname: path to the report file.

        """
        AbstractParser.__init__(self, pathname)

    @classmethod
    def handle_file(cls, pathname, skip_empty=True):
        """Specialized file handler for general files read line by line.

        :param str pathname: path to the report file.
        :raises OSError: if an error occurs when opening/reading the report
            file.
        :raises IOError: if an error occurs when opening/reading the report
            file.

        """
        with open(pathname, 'r') as f:
            if skip_empty:
                return [line.rstrip('\n') for line in f.readlines() if line.rstrip('\n')]
            return [line.rstrip('\n') for line in f.readlines()]
