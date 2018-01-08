"""
owtf.lib.exceptions
~~~~~~~~~~~~~~~~~~~

Declares the framework exceptions and HTTP errors
"""

import tornado.web


class FrameworkException(Exception):
    def __init__(self, value):
        self.parameter = value

    def __str__(self):
        return repr(self.parameter)


class APIError(tornado.web.HTTPError):
    """Exception for API-based errors"""

    def __init__(self, message, code=400):
        super(APIError, self).__init__(code)
        self.message = message


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
