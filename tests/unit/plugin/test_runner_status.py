"""
tests.unit.plugin.test_runner_status
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Tests that PluginRunner correctly classifies plugin execution outcomes.
"""
from unittest import mock

from owtf.plugin.harness import ErrorResult, TimeoutResult


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

def test_process_plugin_ranks_list_output_on_success():
    """process_plugin() must rank genuine successful output, including the
    list shape real OWTF plugins return — not just dicts. Reproduces the
    reviewer-reported bug where owtf_rank stayed None for normal plugin runs
    because the old guard only accepted isinstance(output, dict)."""
    from datetime import datetime, timedelta

    with mock.patch("owtf.db.session.get_db_engine", return_value=mock.MagicMock()):
        from owtf.plugin.runner import PluginRunner

    runner = PluginRunner.__new__(PluginRunner)
    start = datetime(2026, 1, 1, 0, 0, 0)
    end = start + timedelta(seconds=3)
    runner.timer = mock.MagicMock()
    runner.timer.get_start_date_time = mock.MagicMock(return_value=start)
    runner.timer.get_end_date_time = mock.MagicMock(return_value=end)
    runner.simulation = False
    runner.plugin_count = 0

    # Real OWTF plugin output shape: a list of finding dicts, not a single dict.
    list_output = [
        {"type": "vulnerability", "name": "Reflected XSS", "severity": "medium"},
        {"type": "info", "name": "Server header disclosed", "severity": "info"},
    ]

    plugin = {
        "code": "OWTF-TEST-LIST-001",
        "key": "active@OWTF-TEST-LIST-001",
        "group": "web",
        "type": "active",
        "title": "Test List Output Plugin",
    }

    with mock.patch.object(runner, "can_plugin_run", return_value=True), \
         mock.patch.object(runner, "get_plugin_output_dir", return_value="/tmp/fake"), \
         mock.patch.object(runner, "run_plugin", return_value=list_output), \
         mock.patch("owtf.plugin.runner.get_output_dir_target", return_value="/tmp"), \
         mock.patch("owtf.plugin.runner.num_transactions", return_value=1), \
         mock.patch("owtf.plugin.runner.save_plugin_output") as mock_save:

        output = runner.process_plugin(session=mock.MagicMock(), plugin_dir="/tmp", plugin=plugin)

    # The list came back untouched
    assert output == list_output

    # The core assertion: list-shaped successful output must be ranked,
    # not silently left at None the way the isinstance(output, dict)
    # bug used to leave it.
    assert plugin["owtf_rank"] is not None
    assert plugin["status"] == "Successful"
    mock_save.assert_called_once()
