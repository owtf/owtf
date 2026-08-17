"""
tests.unit.plugin.test_harness
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Unit tests for plugin execution harness with timeout support.
"""
import signal
import time
from owtf.plugin.harness import execute_with_timeout, TimeoutResult, ErrorResult
from owtf.settings import PLUGIN_TIMEOUT


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
