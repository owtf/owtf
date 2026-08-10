"""
owtf.plugin.harness
~~~~~~~~~~~~~~~~~~~

Plugin execution with timeout support using signals (Unix) or fallback (cross-platform).
"""
import logging
import signal

logger = logging.getLogger(__name__)


def execute_with_timeout(func, plugin, timeout=None):
    """Execute a plugin function with timeout.

    Uses SIGALRM on Unix platforms. Gracefully falls back to no timeout on Windows/macOS.

    :param func: Function to execute (e.g., runner.run_plugin)
    :param plugin: Plugin dict
    :param timeout: Timeout in seconds (default from settings)
    :return: Plugin output or None if timeout/error
    :rtype: `dict` or `None`
    """
    if timeout is None:
        from owtf.settings import PLUGIN_TIMEOUT
        timeout = PLUGIN_TIMEOUT

    try:
        # Try using SIGALRM on Unix platforms
        def timeout_handler(signum, frame):
            raise TimeoutError(f"Plugin execution timed out after {timeout}s")

        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout)

        try:
            output = func(plugin)
            return output
        finally:
            signal.alarm(0)  # Cancel alarm

    except TimeoutError as e:
        logger.warning("Plugin %s: %s", plugin.get("code"), str(e))
        return None
    except AttributeError:
        # SIGALRM not available on Windows/macOS, execute without timeout
        logger.debug("Timeout not supported on this platform, executing without timeout")
        return func(plugin)
    except Exception as e:
        logger.error("Plugin %s raised exception: %s", plugin.get("code"), str(e))
        return None
