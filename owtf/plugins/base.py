from abc import ABCMeta, abstractmethod


class Plugin(object):
    """Abstract base class definition for plugins.
    Plugins must be a subclass of Plugin and
    must define the following members.
    """
    __metaclass__ = ABCMeta

    name = None
    description = None
    author = None
    # Type is a tuple of tags.
    # For example, ('web', 'grep')
    type = None

    @abstractmethod
    def run(self):
        pass
