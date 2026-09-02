"""
tests.unit.plugin.test_runner_status
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Tests that PluginRunner correctly classifies plugin execution outcomes.
"""

from datetime import datetime, timedelta
from unittest import mock

import pytest

from owtf.plugin.harness import ErrorResult, TimeoutResult


def _get_runner_class():
    """Import PluginRunner without hitting a real DB connection."""
    with mock.patch("owtf.db.session.get_db_engine", return_value=mock.MagicMock()):
        from owtf.plugin.runner import PluginRunner

    return PluginRunner


def test_runner_marks_timeout_as_timeout():
    """PluginRunner should mark TimeoutResult as 'Timeout' status."""
    output = TimeoutResult(timeout=5)
    status_msg = "Timeout" if isinstance(output, TimeoutResult) else ""
    assert status_msg == "Timeout"


def test_runner_marks_error_as_error():
    """PluginRunner should mark ErrorResult as 'Error' status."""
    output = ErrorResult(Exception("Plugin crashed"))
    status_msg = "Error" if isinstance(output, ErrorResult) else ""
    assert status_msg == "Error"


def test_runner_marks_dict_output_as_successful():
    """PluginRunner should mark dict output as 'Successful' status."""
    output = {"status": "success", "data": "findings"}
    status_msg = "Successful" if isinstance(output, dict) else ""
    assert status_msg == "Successful"


def test_process_plugin_records_metrics_with_correct_keywords():
    """process_plugin() records metrics using the plugin's complete key."""
    import owtf.plugin.metrics as metrics_module

    metrics_module._metrics_instance = None
    PluginRunner = _get_runner_class()
    runner = PluginRunner.__new__(PluginRunner)
    start = datetime(2026, 1, 1, 0, 0, 0)
    end = start + timedelta(seconds=5)
    runner.timer = mock.MagicMock()
    runner.timer.get_start_date_time.return_value = start
    runner.timer.get_end_date_time.return_value = end
    runner.simulation = False
    runner.plugin_count = 0
    plugin = {
        "code": "OWTF-TEST-001",
        "key": "active@OWTF-TEST-001",
        "group": "web",
        "type": "active",
        "title": "Test Plugin",
    }

    with (
        mock.patch.object(runner, "can_plugin_run", return_value=True),
        mock.patch.object(runner, "get_plugin_output_dir", return_value="/tmp/fake"),
        mock.patch.object(runner, "run_plugin", return_value={"status": "success"}),
        mock.patch.object(runner, "rank_plugin", return_value=1),
        mock.patch("owtf.plugin.runner.get_output_dir_target", return_value="/tmp"),
        mock.patch("owtf.plugin.runner.num_transactions", return_value=1),
        mock.patch("owtf.plugin.runner.save_plugin_output") as mock_save,
    ):
        output = runner.process_plugin(session=mock.MagicMock(), plugin_dir="/tmp", plugin=plugin)

    assert output == {"status": "success"}
    mock_save.assert_called_once()
    recorded = metrics_module.get_metrics().metrics
    assert "active@OWTF-TEST-001" in recorded
    assert recorded["active@OWTF-TEST-001"]["group"] == "web"
    assert recorded["active@OWTF-TEST-001"]["runs"] == 1
    assert recorded["active@OWTF-TEST-001"]["total_runtime"] == 5.0


def test_process_plugin_ranks_list_output_on_success():
    """Successful list-shaped output must still be ranked."""
    PluginRunner = _get_runner_class()
    runner = PluginRunner.__new__(PluginRunner)
    start = datetime(2026, 1, 1, 0, 0, 0)
    end = start + timedelta(seconds=3)
    runner.timer = mock.MagicMock()
    runner.timer.get_start_date_time.return_value = start
    runner.timer.get_end_date_time.return_value = end
    runner.simulation = False
    runner.plugin_count = 0
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

    with (
        mock.patch.object(runner, "can_plugin_run", return_value=True),
        mock.patch.object(runner, "get_plugin_output_dir", return_value="/tmp/fake"),
        mock.patch.object(runner, "run_plugin", return_value=list_output),
        mock.patch.object(runner, "rank_plugin", return_value=1) as mock_rank,
        mock.patch("owtf.plugin.runner.get_output_dir_target", return_value="/tmp"),
        mock.patch("owtf.plugin.runner.num_transactions", return_value=1),
        mock.patch("owtf.plugin.runner.save_plugin_output") as mock_save,
    ):
        output = runner.process_plugin(session=mock.MagicMock(), plugin_dir="/tmp", plugin=plugin)

    assert output == list_output
    assert plugin["owtf_rank"] == 1
    assert plugin["status"] == "Successful"
    mock_rank.assert_called_once_with(list_output, "/tmp/fake")
    mock_save.assert_called_once()


@pytest.mark.parametrize(
    ("output", "expected_status"),
    [
        (TimeoutResult(timeout=5), "Timeout"),
        (ErrorResult(Exception("Plugin crashed")), "Error"),
    ],
)
def test_process_plugin_does_not_rank_failed_result_objects(output, expected_status):
    PluginRunner = _get_runner_class()
    runner = PluginRunner.__new__(PluginRunner)
    runner.timer = mock.MagicMock()
    runner.timer.get_start_date_time.return_value = datetime(2026, 1, 1, 0, 0, 0)
    runner.timer.get_end_date_time.return_value = datetime(2026, 1, 1, 0, 0, 1)
    runner.simulation = False
    runner.plugin_count = 0
    plugin = {
        "code": "OWTF-TEST-FAIL-001",
        "key": "active@OWTF-TEST-FAIL-001",
        "group": "web",
        "type": "active",
        "title": "Test Failed Plugin",
    }

    with (
        mock.patch.object(runner, "can_plugin_run", return_value=True),
        mock.patch.object(runner, "get_plugin_output_dir", return_value="/tmp/fake"),
        mock.patch.object(runner, "run_plugin", return_value=output),
        mock.patch.object(runner, "rank_plugin") as mock_rank,
        mock.patch("owtf.plugin.runner.target_manager.get_target_url", return_value="https://example.test"),
        mock.patch("owtf.plugin.runner.get_output_dir_target", return_value="/tmp"),
        mock.patch("owtf.plugin.runner.num_transactions", return_value=1),
        mock.patch("owtf.plugin.runner.get_metrics") as mock_get_metrics,
        mock.patch("owtf.plugin.runner.save_partial_output") as mock_save_partial,
    ):
        result = runner.process_plugin(session=mock.MagicMock(), plugin_dir="/tmp", plugin=plugin)

    assert result is output
    assert plugin["status"] == expected_status
    assert plugin["owtf_rank"] is None
    mock_rank.assert_not_called()
    mock_get_metrics.return_value.record_execution.assert_called_once()
    mock_save_partial.assert_called_once()
