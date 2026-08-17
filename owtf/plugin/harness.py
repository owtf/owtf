"""
owtf.plugin.harness
~~~~~~~~~~~~~~~~~~~

Plugin execution with timeout support and retry logic using signals (Unix) or fallback (cross-platform).
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


def execute_with_timeout(func, plugin, timeout=None, max_retries=None):
    """Execute a plugin function with timeout and retry support.

    Uses SIGALRM on Unix platforms. Gracefully falls back to no timeout on Windows/macOS.
    Retries on error but NOT on timeout.

    :param func: Function to execute (e.g., module.run)
    :param plugin: Plugin dict
    :param timeout: Timeout in seconds (default from settings)
    :param max_retries: Max retries on error (default from settings)
    :return: Plugin output, TimeoutResult, ErrorResult, or None
    :rtype: `dict` or `TimeoutResult` or `ErrorResult` or `None`
    """
    if timeout is None:
        from owtf.settings import PLUGIN_TIMEOUT
        timeout = PLUGIN_TIMEOUT

    if max_retries is None:
        from owtf.settings import PLUGIN_MAX_RETRIES
        max_retries = PLUGIN_MAX_RETRIES

    last_error = None

    for attempt in range(max_retries + 1):
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
            # Don't retry on timeout - return immediately
            logger.warning("Plugin %s: %s", plugin.get("code"), str(e))
            return TimeoutResult(timeout)

        except AttributeError as e:
            # SIGALRM not available on Windows/macOS
            if "signal" in str(e).lower() or "SIGALRM" in str(e):
                logger.debug("Timeout not supported on this platform, executing without timeout")
                try:
                    return func(plugin)
                except Exception as plugin_error:
                    last_error = plugin_error
            else:
                # Plugin itself raised AttributeError
                last_error = e

        except Exception as e:
            last_error = e

        # Log retry attempt if not last attempt
        if attempt < max_retries and last_error:
            logger.warning(
                "Plugin %s failed (attempt %d/%d), retrying: %s",
                plugin.get("code"),
                attempt + 1,
                max_retries + 1,
                str(last_error)
            )

    # All retries exhausted
    if last_error:
        logger.error("Plugin %s failed after %d retries: %s", plugin.get("code"), max_retries, str(last_error))
        return ErrorResult(last_error)

    return None