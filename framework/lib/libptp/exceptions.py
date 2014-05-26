"""

    Custom exceptions for PTP.

"""


class PTPError(Exception):
    """General PTP error."""
    pass


class ReportNotFoundError(PTPError):
    """General PTP error."""
    pass


class NotSupportedToolError(PTPError):
    """PTP error raised when the tool is not supported"""
    pass


class NotSupportedVersionError(PTPError):
    """PTP error raised when the version of the tool is not supported"""
    pass
