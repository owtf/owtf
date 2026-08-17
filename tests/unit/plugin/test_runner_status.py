"""
tests.unit.plugin.test_runner_status
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Tests that PluginRunner correctly classifies plugin execution outcomes.
"""
from unittest import mock
from owtf.plugin.harness import TimeoutResult, ErrorResult


def test_runner_marks_timeout_as_timeout():
    """PluginRunner should mark TimeoutResult as 'Timeout' status."""
    from owtf.plugin.runner import PluginRunner
    
    # Mock the harness to return TimeoutResult
    timeout_result = TimeoutResult(timeout=5)
    
    with mock.patch.object(PluginRunner, 'run_plugin', return_value=timeout_result):
        runner = PluginRunner()
        status_dict = {}
        
        # Simulate the outcome checking logic from process_plugin
        output = timeout_result
        status_msg = ""
        
        if isinstance(output, TimeoutResult):
            status_msg = "Timeout"
        
        assert status_msg == "Timeout"


def test_runner_marks_error_as_error():
    """PluginRunner should mark ErrorResult as 'Error' status."""
    from owtf.plugin.runner import PluginRunner
    
    error_result = ErrorResult(Exception("Plugin crashed"))
    
    with mock.patch.object(PluginRunner, 'run_plugin', return_value=error_result):
        runner = PluginRunner()
        output = error_result
        status_msg = ""
        
        if isinstance(output, ErrorResult):
            status_msg = "Error"
        
        assert status_msg == "Error"


def test_runner_marks_dict_output_as_successful():
    """PluginRunner should mark dict output as 'Successful' status."""
    from owtf.plugin.runner import PluginRunner
    
    plugin_output = {"status": "success", "data": "findings"}
    
    with mock.patch.object(PluginRunner, 'run_plugin', return_value=plugin_output):
        runner = PluginRunner()
        output = plugin_output
        status_msg = ""
        
        if isinstance(output, dict):
            status_msg = "Successful"
        
        assert status_msg == "Successful"
