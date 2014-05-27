"""

    The Report class will be the summarize of the complete report provided by
    pentesting tools.

"""


import os
import fnmatch
from framework.lib.libptp.constants import RANKING_SCALE


class AbstractReport(object):
    """Abstract representation of a report provided by a pentesting tool.

        + vulns: List of Info instances

    This class will be extended for each pentesting tool. That way, each tool
    will add its own parser.

    """

    def __init__(self, vulns=None):
        """Self-explanatory."""
        self.vulns = vulns
        if self.vulns is None:
            self.vulns = []

    def __str__(self):
        return ', '.join([info.__str__() for info in self.vulns])

    def _lowest_risk(self):
        """Retrieve the ranking id of the lowest risk possible.

        According the the ranking scale, 3 represents the lowest.

        """
        return max([value for value in RANKING_SCALE.values()])

    def _highest_risk(self):
        """Retrieve the ranking id of the highest risk possible.

        According the the ranking scale, 0 represents the lowest.

        """
        return min([value for value in RANKING_SCALE.values()])

    @classmethod
    def is_mine(cls, pathname, filename=None):
        """Check if it it a report from my tool.

        Return True if it is mine, False otherwise.

        """
        return False

    @classmethod
    def check_version(cls, metadata, key='version'):
        """Checks the version from the metadata against the supported one.

        The version to test is the value of metadata[key].

        """
        if metadata[key] in cls.__version__:
            return True
        return False

    @staticmethod
    def _recursive_find(pathname='./', file_regex='*', early_break=True):
        """Find the files corresponding to `file_regex`.

        The search occurs in the directory `pathname`.

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

    def get_highest_ranking(self, *args, **kwargs):
        """Return the highest ranking of the report.

        Iterates over the list of vulnerabilities.
        If the current ranking is higher (in risk) than the current highest
        then switch them.
        If it finds the highest (in risk) ranking possible, stops.

        """
        # Be sure that the parsing already happened.
        if self.vulns is None:
            self.parser(*args, **kwargs)
        highest_possible_ranking = self._highest_risk()
        # Default highest ranking set to the lowest possible value.
        highest_ranking = self._lowest_risk()
        for vuln in self.vulns:
            if RANKING_SCALE[vuln.ranking] < RANKING_SCALE[highest_ranking]:
                highest_ranking = vuln.ranking
            # If the current highest_ranking is already the highest possible
            # one, we can stop the loop.
            if RANKING_SCALE[highest_ranking] == highest_possible_ranking:
                break
        return highest_ranking

    def parse(self):
        """Abstract parser that will parse the report of a tool."""
        raise NotImplementedError('The parser MUST be define for each tool.')
