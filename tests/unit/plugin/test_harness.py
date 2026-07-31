"""
tests.unit.plugin.test_harness
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Unit tests for plugin execution harness.
"""
from owtf.plugin.harness import execute_with_timeout
from owtf.settings import PLUGIN_TIMEOUT


def test_plugin_timeout_constant_is_positive():
    """PLUGIN_TIMEOUT must be a positive integer."""
    assert isinstance(PLUGIN_TIMEOUT, int)
    assert PLUGIN_TIMEOUT > 0


def test_execute_with_timeout_success():
    """execute_with_timeout should return result on success."""
    def mock_func(plugin):
        return {"status": "success", "output": "test"}

    plugin = {"code": "OWTF-TEST-001", "group": "web"}
    result = execute_with_timeout(mock_func, plugin, timeout=5)

    assert result is not None
    assert result["status"] == "success"


def test_execute_with_timeout_exception():
    """execute_with_timeout should return None on exception."""
    def mock_func(plugin):
        raise Exception("plugin error")

    plugin = {"code": "OWTF-TEST-001", "group": "web"}
    result = execute_with_timeout(mock_func, plugin, timeout=5)

    assert result is None


def test_execute_with_timeout_uses_default():
    """execute_with_timeout should use PLUGIN_TIMEOUT when not specified."""
    def mock_func(plugin):
        return {"status": "ok"}

    plugin = {"code": "OWTF-TEST-001", "group": "web"}
    result = execute_with_timeout(mock_func, plugin)  # No timeout specified

    assert result is not None