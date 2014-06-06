"""

    The Info class will be the summary of a result form the output report
    provided by pentesting tools.

"""


class Info(dict):
    """Representation of a result from a report provided by a pentesting tool.

        + name: the name of the vulnerability
        + ranking: the ranking of the vulnerability.
        + description: the description of the vulnerability.
        + kwargs: any key/value attributes the vuln might contain

    """
    __getattr__= dict.__getitem__
    __setattr__= dict.__setitem__
    __delattr__= dict.__delitem__

    def __init__(self, name=None, ranking=None, description=None, **kwargs):
        """Self-explanatory."""
        self.name = name
        self.ranking = ranking
        self.description = description
        for key, value in kwargs.items():
            self[key] = value
