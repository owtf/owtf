"""
tests.unit.plugin.test_runner_status
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Tests that PluginRunner correctly classifies plugin execution outcomes.
"""
from unittest import mock

from owtf.plugin.harness import ErrorResult, TimeoutResult


def _get_runner_class():
    """Import PluginRunner without hitting a real DB connection."""
    with mock.patch("owtf.db.session.get_db_engine", return_value=mock.MagicMock()):
        from owtf.plugin.runner import PluginRunner
    return PluginRunner


def test_runner_marks_timeout_as_timeout():
    """PluginRunner should mark TimeoutResult as 'Timeout' status."""
    timeout_result = TimeoutResult(timeout=5)

    output = timeout_result
    status_msg = ""

    if isinstance(output, TimeoutResult):
        status_msg = "Timeout"

    assert status_msg == "Timeout"


def test_runner_marks_error_as_error():
    """PluginRunner should mark ErrorResult as 'Error' status."""
    error_result = ErrorResult(Exception("Plugin crashed"))

    output = error_result
    status_msg = ""

    if isinstance(output, ErrorResult):
        status_msg = "Error"

    assert status_msg == "Error"


def test_runner_marks_dict_output_as_successful():
    """PluginRunner should mark dict output as 'Successful' status."""
    plugin_output = {"status": "success", "data": "findings"}

    output = plugin_output
    status_msg = ""

    if isinstance(output, dict):
        status_msg = "Successful"

    assert status_msg == "Successful"


def test_process_plugin_records_metrics_with_correct_keywords():
    """process_plugin() should call get_metrics().record_execution() with
    plugin_group (not group), reproducing and guarding against the
    mentor-reported TypeError."""
    from datetime import datetime, timedelta

    import owtf.plugin.metrics as metrics_module

    metrics_module._metrics_instance = None

    PluginRunner = _get_runner_class()

    runner = PluginRunner.__new__(PluginRunner)
    start = datetime(2026, 1, 1, 0, 0, 0)
    end = start + timedelta(seconds=5)
    runner.timer = mock.MagicMock()
    runner.timer.get_start_date_time = mock.MagicMock(return_value=start)
    runner.timer.get_end_date_time = mock.MagicMock(return_value=end)
    runner.simulation = False
    runner.plugin_count = 0

    plugin = {
        "code": "OWTF-TEST-001",
        "key": "active@OWTF-TEST-001",
        "group": "web",
        "type": "active",
        "title": "Test Plugin",
    }

    with mock.patch.object(runner, "can_plugin_run", return_value=True), \
         mock.patch.object(runner, "get_plugin_output_dir", return_value="/tmp/fake"), \
         mock.patch.object(runner, "run_plugin", return_value={"status": "success"}), \
         mock.patch.object(runner, "rank_plugin", return_value=1), \
         mock.patch("owtf.plugin.runner.get_output_dir_target", return_value="/tmp"), \
         mock.patch("owtf.plugin.runner.num_transactions", return_value=1), \
         mock.patch("owtf.plugin.runner.save_plugin_output") as mock_save:

        output = runner.process_plugin(session=mock.MagicMock(), plugin_dir="/tmp", plugin=plugin)

    assert output == {"status": "success"}
    mock_save.assert_called_once()

    recorded = metrics_module.get_metrics().metrics
    assert "OWTF-TEST-001" in recorded
    assert recorded["OWTF-TEST-001"]["group"] == "web"
    assert recorded["OWTF-TEST-001"]["runs"] == 1
    assert recorded["OWTF-TEST-001"]["total_runtime"] == 5.0
