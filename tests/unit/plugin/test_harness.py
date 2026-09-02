"""
tests.unit.plugin.test_harness
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Unit tests for plugin execution harness with timeout support.
"""
import signal
import time

from owtf.plugin.harness import ErrorResult, TimeoutResult, execute_with_timeout


def test_successful_execution_returns_output():
    """Successful plugin execution should return actual output."""
    def mock_plugin_func(plugin):
        return {"status": "success", "output": "test data"}

    plugin = {"code": "TEST-001"}
    result = execute_with_timeout(mock_plugin_func, plugin, timeout=5)

    assert isinstance(result, dict)
    assert result["status"] == "success"
    assert result["output"] == "test data"


def test_timeout_returns_timeout_result():
    """Plugin execution that times out should return TimeoutResult."""
    def slow_plugin_func(plugin):
        time.sleep(10)  # Sleep longer than timeout
        return {"status": "success"}

    plugin = {"code": "TEST-002"}
    result = execute_with_timeout(slow_plugin_func, plugin, timeout=1)

    assert isinstance(result, TimeoutResult)
    assert result.timeout == 1
    assert "timed out" in result.message.lower()


def test_exception_returns_error_result():
    """Plugin execution that raises exception should return ErrorResult."""
    def error_plugin_func(plugin):
        raise ValueError("Plugin failed")

    plugin = {"code": "TEST-003"}
    result = execute_with_timeout(error_plugin_func, plugin, timeout=5)

    assert isinstance(result, ErrorResult)
    assert "Plugin failed" in result.message


def test_plugin_attribute_error_returns_error_result():
    """Plugin's own AttributeError should return ErrorResult, not retry."""
    def plugin_with_attr_error(plugin):
        # Plugin raises its own AttributeError
        obj = None
        obj.nonexistent_method()  # This raises AttributeError

    plugin = {"code": "TEST-004"}
    result = execute_with_timeout(plugin_with_attr_error, plugin, timeout=5)

    assert isinstance(result, ErrorResult)
    # Should NOT retry - should catch and return error


def test_sigalrm_handler_restored():
    """Previous SIGALRM handler should be restored after execution."""
    def custom_handler(signum, frame):
        pass

    # Set a custom handler
    old_handler = signal.signal(signal.SIGALRM, custom_handler)

    def normal_plugin_func(plugin):
        return {"status": "success"}

    plugin = {"code": "TEST-005"}
    execute_with_timeout(normal_plugin_func, plugin, timeout=5)

    # Handler should be restored
    current_handler = signal.signal(signal.SIGALRM, old_handler)
    assert current_handler == custom_handler

    # Restore original
    signal.signal(signal.SIGALRM, old_handler)


def test_uses_default_timeout_from_settings():
    """Should use PLUGIN_TIMEOUT from settings if not specified."""
    def quick_plugin(plugin):
        return {"status": "success"}

    plugin = {"code": "TEST-006"}
    # Should not raise error - should use default timeout
    result = execute_with_timeout(quick_plugin, plugin)

    assert isinstance(result, dict)
    assert result["status"] == "success"


def test_retry_on_error():
    """Plugin should retry on error up to max_retries."""
    attempt_count = [0]

    def failing_plugin_func(plugin):
        attempt_count[0] += 1
        if attempt_count[0] < 2:
            raise ValueError("Plugin failed")
        return {"status": "success"}

    plugin = {"code": "TEST-007"}
    result = execute_with_timeout(failing_plugin_func, plugin, timeout=5, max_retries=2)

    assert isinstance(result, dict)
    assert result["status"] == "success"
    assert attempt_count[0] == 2


def test_no_retry_on_timeout():
    """Plugin should NOT retry on timeout."""
    attempt_count = [0]

    def slow_plugin_func(plugin):
        attempt_count[0] += 1
        import time
        time.sleep(10)

    plugin = {"code": "TEST-008"}
    result = execute_with_timeout(slow_plugin_func, plugin, timeout=1, max_retries=2)

    assert isinstance(result, TimeoutResult)
    assert attempt_count[0] == 1


def test_exhausts_retries_and_returns_error():
    """Plugin should return ErrorResult after exhausting all retries."""
    def always_failing_plugin(plugin):
        raise RuntimeError("Persistent failure")

    plugin = {"code": "TEST-009"}
    result = execute_with_timeout(always_failing_plugin, plugin, timeout=5, max_retries=2)

    assert isinstance(result, ErrorResult)
    assert "Persistent failure" in result.message

def test_plugin_abort_exception_bubbles_up():
    """PluginAbortException should bubble up, not be caught or retried."""
    import pytest

    from owtf.lib.exceptions import PluginAbortException

    def plugin_that_aborts(plugin):
        raise PluginAbortException("Plugin aborted by user")

    plugin = {"code": "TEST-ABORT"}
    with pytest.raises(PluginAbortException):
        execute_with_timeout(plugin_that_aborts, plugin, timeout=5, max_retries=2)


def test_unreachable_target_exception_bubbles_up():
    """UnreachableTargetException should bubble up, not be caught or retried."""
    import pytest

    from owtf.lib.exceptions import UnreachableTargetException

    def plugin_unreachable(plugin):
        raise UnreachableTargetException("Target not reachable")

    plugin = {"code": "TEST-UNREACHABLE"}
    with pytest.raises(UnreachableTargetException):
        execute_with_timeout(plugin_unreachable, plugin, timeout=5, max_retries=2)


def test_framework_abort_exception_bubbles_up():
    """FrameworkAbortException should bubble up, not be caught or retried."""
    import pytest

    from owtf.lib.exceptions import FrameworkAbortException

    def plugin_framework_abort(plugin):
        raise FrameworkAbortException("Framework abort requested")

    plugin = {"code": "TEST-FRAMEWORK"}
    with pytest.raises(FrameworkAbortException):
        execute_with_timeout(plugin_framework_abort, plugin, timeout=5, max_retries=2)
