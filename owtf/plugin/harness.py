"""
owtf.plugin.harness
~~~~~~~~~~~~~~~~~~~

Plugin execution with timeout support using signals (Unix) or fallback (cross-platform).
"""
import logging
import signal

logger = logging.getLogger(__name__)


class TimeoutResult:
    """Indicates plugin execution timed out."""
    def __init__(self, timeout):
        self.timeout = timeout
        self.message = f"Plugin execution timed out after {timeout}s"


class ErrorResult:
    """Indicates plugin execution raised an exception."""
    def __init__(self, error):
        self.error = error
        self.message = str(error)


def execute_with_timeout(func, plugin, timeout=None):
    """Execute a plugin function with timeout.

    Uses SIGALRM on Unix platforms. Gracefully falls back to no timeout on Windows/macOS.

    :param func: Function to execute (e.g., module.run)
    :param plugin: Plugin dict
    :param timeout: Timeout in seconds (default from settings)
    :return: Plugin output, TimeoutResult, ErrorResult, or None
    :rtype: `dict` or `TimeoutResult` or `ErrorResult` or `None`
    """
    if timeout is None:
        from owtf.settings import PLUGIN_TIMEOUT
        timeout = PLUGIN_TIMEOUT

    # Try using SIGALRM on Unix platforms
    try:
        def timeout_handler(signum, frame):
            raise TimeoutError(f"Plugin execution timed out after {timeout}s")

        # Save previous handler to restore later
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout)

        try:
            output = func(plugin)
            return output
        finally:
            # Cancel alarm and restore previous handler
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)

    except TimeoutError as e:
        logger.warning("Plugin %s: %s", plugin.get("code"), str(e))
        return TimeoutResult(timeout)

    except AttributeError as e:
        # SIGALRM not available on Windows/macOS
        # Check if this is from signal module, not from plugin itself
        if "signal" in str(e).lower() or "SIGALRM" in str(e):
            logger.debug("Timeout not supported on this platform, executing without timeout")
            try:
                return func(plugin)
            except Exception as plugin_error:
                logger.error("Plugin %s raised exception: %s", plugin.get("code"), str(plugin_error))
                return ErrorResult(plugin_error)
        else:
            # Plugin itself raised AttributeError - don't retry
            logger.error("Plugin %s raised exception: %s", plugin.get("code"), str(e))
            return ErrorResult(e)

    except Exception as e:
        logger.error("Plugin %s raised exception: %s", plugin.get("code"), str(e))
        return ErrorResult(e)