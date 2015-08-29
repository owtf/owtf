#!/usr/bin/env python
"""
Declares the framework exceptions.
"""


class FrameworkException(Exception):
    def __init__(self, value):
        self.parameter = value

    def __str__(self):
        return repr(self.parameter)


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
