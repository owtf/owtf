"""
Regression coverage for the real PluginRunner.process_plugin execution path.
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch


def test_process_plugin_records_metrics_before_saving_output(tmp_path):
    """process_plugin must record metrics with plugin_group and still save output."""
    import owtf.db.session as db_session

    fake_default_session = MagicMock(name="default_session")
    with patch.object(db_session, "get_scoped_session", return_value=fake_default_session):
        from owtf.plugin.runner import PluginRunner

    session = MagicMock(name="execution_session")
    metrics = MagicMock(name="metrics")
    start = datetime(2026, 1, 1, 12, 0, 0)
    end = start + timedelta(seconds=2)
    plugin = {
        "key": "active@OWTF-TEST-001",
        "code": "OWTF-TEST-001",
        "group": "web",
        "type": "active",
        "title": "Test plugin",
        "file": "test_plugin.py",
        "start": None,
    }
    output = {"status": "success", "findings": []}
    runner = PluginRunner()
    runner.plugin_group = "web"
    runner.force_overwrite = False
    runner.simulation = False
    runner.only_plugins_list = []
    runner.except_plugins_list = []
    runner.timer = MagicMock()
    runner.timer.get_start_date_time.return_value = start
    runner.timer.get_end_date_time.return_value = end
    runner.rank_plugin = MagicMock(return_value=-1)

    with (
        patch("owtf.managers.poutput.plugin_already_run", return_value=False),
        patch("owtf.plugin.runner.get_types_for_plugin_group", return_value=["active"]),
        patch.object(runner, "run_plugin", return_value=output),
        patch.object(runner, "get_plugin_output_dir", return_value=str(tmp_path)),
        patch("owtf.plugin.runner.get_output_dir_target", return_value=str(tmp_path)),
        patch("owtf.plugin.runner.target_manager.get_target_url", return_value="https://example.test"),
        patch("owtf.plugin.runner.get_metrics", return_value=metrics),
        patch("owtf.plugin.runner.save_plugin_output") as save_output,
    ):
        result = runner.process_plugin(session=session, plugin_dir="/plugins/web", plugin=plugin)

    assert result == output
    metrics.record_execution.assert_called_once_with(
        plugin_code="OWTF-TEST-001",
        plugin_group="web",
        plugin_type="active",
        status="Successful",
        start_time=start,
        end_time=end,
        error=None,
        session=session,
    )
    save_output.assert_called_once_with(session=session, plugin=plugin, output=output)
    assert plugin["status"] == "Successful"
    assert plugin["owtf_rank"] == -1
