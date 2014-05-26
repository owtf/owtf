"""

    The Info class will be the summary of a result form the output report
    provided by pentesting tools.

"""


class Info(object):
    """Representation of a result from a report provided by a pentesting tool.

        + name: the name of the vulnerability
        + ranking: the ranking of the vulnerability.
        + description: the description of the vulnerability.
        + kwargs: any key/value attributes the vuln might contain

    """

    def __init__(self, name=None, ranking=None, description=None, **kwargs):
        """Self-explanatory."""
        self.name = name
        self.ranking = ranking
        self.description = description
        for key, value in kwargs:
            self.key = value

    def __str__(self):
        """String representation of the Info class.

        Can be used to be encoded into a json string and saved into a database.

        """
        return str(self.__dict__)
