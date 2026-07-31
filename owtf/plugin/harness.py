"""
owtf.plugin.harness
~~~~~~~~~~~~~~~~~~~

Plugin execution with timeout support.
"""
import logging
import multiprocessing

logger = logging.getLogger(__name__)


def execute_with_timeout(func, plugin, timeout=None):
    """Execute a plugin function with timeout.

    Uses multiprocessing to enforce timeout cross-platform (Windows + Unix).
    If timeout is exceeded, the process is terminated and None is returned.

    :param func: Function to execute (e.g., runner.run_plugin)
    :param plugin: Plugin dict
    :param timeout: Timeout in seconds (default from settings)
    :return: Plugin output or None if timeout
    :rtype: `dict` or `None`
    """
    if timeout is None:
        from owtf.settings import PLUGIN_TIMEOUT
        timeout = PLUGIN_TIMEOUT

    # Run function in separate process
    q = multiprocessing.Queue()

    def wrapper():
        try:
            result = func(plugin)
            q.put(("success", result))
        except Exception as e:
            q.put(("error", str(e)))

    proc = multiprocessing.Process(target=wrapper)
    proc.start()
    proc.join(timeout=timeout)

    if proc.is_alive():
        # Timeout occurred
        proc.terminate()
        proc.join()
        logger.warning(
            "Plugin %s timed out after %d seconds",
            plugin.get("code"),
            timeout,
        )
        return None

    # Get result from queue
    try:
        status, result = q.get_nowait()
        if status == "success":
            return result
        else:
            logger.error("Plugin %s raised exception: %s", plugin.get("code"), result)
            return None
    except Exception:
        return None