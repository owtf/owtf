"""
owtf.lib.exceptions
~~~~~~~~~~~~~~~~~~~
Declares the framework exceptions and HTTP errors
"""
try:
    from http.client import responses
except ImportError:
    from httplib import responses

import tornado.web


class FrameworkException(Exception):

    def __init__(self, value):
        self.parameter = value

    def __repr__(self):
        return self.parameter


class APIError(tornado.web.HTTPError):
    """Equivalent to ``RequestHandler.HTTPError`` except for in name"""


def api_assert(condition, *args, **kwargs):
    """Assertion to fail with if not ``condition``
    Asserts that ``condition`` is ``True``, else raises an ``APIError``
    with the provided ``args`` and ``kwargs``
    :type  condition: bool
    """
    if not condition:
        raise APIError(*args, **kwargs)


class FrameworkAbortException(FrameworkException):
    pass


class PluginAbortException(FrameworkException):
    pass


class UnreachableTargetException(FrameworkException):
    pass


class UnresolvableTargetException(FrameworkException):
    pass


class DBIntegrityException(FrameworkException):
    pass


class InvalidTargetReference(FrameworkException):
    pass


class InvalidSessionReference(FrameworkException):
    pass


class InvalidTransactionReference(FrameworkException):
    pass


class InvalidParameterType(FrameworkException):
    pass


class InvalidWorkerReference(FrameworkException):
    pass


class InvalidErrorReference(FrameworkException):
    pass


class InvalidWorkReference(FrameworkException):
    pass


class InvalidConfigurationReference(FrameworkException):
    pass


class InvalidUrlReference(FrameworkException):
    pass


class InvalidActionReference(FrameworkException):
    pass


class InvalidMessageReference(FrameworkException):
    pass


class InvalidMappingReference(FrameworkException):
    pass


class DatabaseNotRunningException(Exception):
    pass


class PluginException(Exception):
    pass


class PluginsDirectoryDoesNotExist(PluginException):
    """The specified plugin directory does not exist."""


class PluginsAlreadyLoaded(PluginException):
    """`load_plugins()` called twice."""
