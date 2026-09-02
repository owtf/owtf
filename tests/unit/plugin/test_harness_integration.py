"""
tests.unit.plugin.test_harness_integration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Integration tests for plugin execution through PluginRunner with timeout support.
"""

import unittest
from unittest.mock import MagicMock, Mock

from owtf.plugin.harness import execute_with_timeout


class TestHarnessIntegration(unittest.TestCase):
    """Test harness integration with PluginRunner."""

    def test_execute_with_timeout_wraps_real_plugin_module_call(self):
        """execute_with_timeout should successfully wrap a real plugin module's run method."""
        # Mock a plugin module with a run method (like what PluginRunner gets)
        mock_plugin_module = MagicMock()
        mock_plugin_module.run = Mock(return_value={"status": "success", "output": "plugin result"})

        plugin = {"code": "OWTF-WVS-001", "group": "web", "type": "active", "key": "active@OWTF-WVS-001"}

        # Execute through harness as PluginRunner.run_plugin would
        result = execute_with_timeout(mock_plugin_module.run, plugin, timeout=10)

        # Verify execution succeeded
        self.assertIsNotNone(result)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["output"], "plugin result")
        mock_plugin_module.run.assert_called_once_with(plugin)

    def test_execute_with_timeout_handles_plugin_module_exception(self):
        """execute_with_timeout should handle exceptions from plugin module execution."""
        mock_plugin_module = MagicMock()
        mock_plugin_module.run = Mock(side_effect=RuntimeError("Plugin module failed"))

        plugin = {"code": "OWTF-WVS-001", "group": "web", "type": "active"}

        max_retries = 2
        result = execute_with_timeout(mock_plugin_module.run, plugin, timeout=10, max_retries=max_retries)

        # Should return ErrorResult on exception after retries exhausted
        from owtf.plugin.harness import ErrorResult

        self.assertIsInstance(result, ErrorResult)
        self.assertTrue(result.message)
        self.assertEqual(mock_plugin_module.run.call_count, max_retries + 1)

    def test_execute_with_timeout_with_plugin_runner_flow(self):
        """Test timeout with the flow PluginRunner.run_plugin uses."""
        # Simulate PluginRunner's flow: get_module().run(plugin)
        mock_module_instance = MagicMock()
        mock_module_instance.run = Mock(return_value={"status": "ok", "data": []})

        plugin = {"code": "OWTF-TEST-001", "group": "web"}

        # This is what PluginRunner.run_plugin does:
        # plugin_output = execute_with_timeout(module.run, plugin)
        result = execute_with_timeout(mock_module_instance.run, plugin)

        self.assertIsNotNone(result)
        self.assertEqual(result["status"], "ok")


if __name__ == "__main__":
    unittest.main()
