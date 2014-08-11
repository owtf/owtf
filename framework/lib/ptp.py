"""

.. module:: ptp
    :synopsis: PTP library.

.. moduleauthor:: Tao Sauvage

"""


from framework.lib.libptp.exceptions import NotSupportedToolError
from framework.lib.libptp.constants import UNKNOWN
from framework.lib.libptp.tools.arachni.report import ArachniReport
from framework.lib.libptp.tools.skipfish.report import SkipfishReport
from framework.lib.libptp.tools.w3af.report import W3AFReport
from framework.lib.libptp.tools.wapiti.report import WapitiReport
from framework.lib.libptp.tools.metasploit.report import MetasploitReport
from framework.lib.libptp.tools.dirbuster.report import DirbusterReport
from framework.lib.libptp.tools.nmap.report import NmapReport


class PTP(object):

    """PTP class definition aiming to help users to use `libptp`.

    Example::

        ptp = PTP()
        ptp.parse(path_to_report)

    """

    #: Dictionary linking the tools to their report classes.
    supported = {
        'arachni': ArachniReport,
        'skipfish': SkipfishReport,
        'w3af': W3AFReport,
        'wapiti': WapitiReport,
        'metasploit': MetasploitReport,
        'dirbuster': DirbusterReport,
        'nmap': NmapReport,}

    def __init__(self, tool_name=None):
        self.tool_name = tool_name
        self.report = None

    def __str__(self):
        return self.report.__str__()

    def parse(self, *args, **kwargs):
        """Parse a tool report.

        :param pathname: The path to the report.
        :type pathname: str.
        :raises: NotSupportedToolError

        :returns: list -- The list of dictionaries of the results found in the
                  report.

        """
        if self.tool_name is None:
            try:
                supported = self.supported.itervalues()
            except AttributeError:  # Python3 then.
                supported = self.supported.values()
            for tool in supported:
                try:
                    if tool.is_mine(*args, **kwargs):
                        self.report = tool
                        break
                except TypeError:
                    pass
        else:
            self.report = self.supported.get(self.tool_name)
        if self.report is None:
            raise NotSupportedToolError('This tool is not supported by PTP.')
        self.report = self.report()  # Instantiate the report class.
        return self.report.parse(*args, **kwargs)

    def get_highest_ranking(self):
        """Retrieve the highest ranked vulnerability level from the report.

        :returns: int -- The highest ranked vulnerability level.

        .. note::

            The `level` starts from `0` to `n` where `n` represents the highest
            risk.

        """
        if self.report:
            return self.report.get_highest_ranking()
        return UNKNOWN
