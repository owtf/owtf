from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from owtf.db.model_base import Model
from owtf.models.command import Command  # noqa: F401 - register relationship target
from owtf.models.grep_output import GrepOutput  # noqa: F401 - register relationship target
from owtf.models.plugin import Plugin  # noqa: F401 - register relationship target
from owtf.models.plugin_execution import PluginExecution
from owtf.models.plugin_output import PluginOutput  # noqa: F401 - register relationship target
from owtf.models.session import Session  # noqa: F401 - register relationship target
from owtf.models.target import Target  # noqa: F401 - register relationship target
from owtf.models.test_group import TestGroup as _TestGroup  # noqa: F401 - register relationship target
from owtf.models.transaction import Transaction  # noqa: F401 - register relationship target
from owtf.models.url import Url  # noqa: F401 - register relationship target
from owtf.models.work import Work  # noqa: F401 - register relationship target
from owtf.plugin.metrics import PluginMetrics
from owtf.reports.html_report import HTMLReportGenerator


def test_metrics_aggregate_records_written_by_separate_workers():
    """A fresh collector/report must see execution rows written by workers."""
    engine = create_engine("sqlite:///:memory:")
    Model.metadata.create_all(engine, tables=[PluginExecution.__table__])
    session_factory = sessionmaker(bind=engine)
    start = datetime(2026, 1, 1, 12, 0, 0)

    worker_one_session = session_factory()
    worker_two_session = session_factory()
    try:
        PluginMetrics().record_execution(
            "OWTF-TEST-001",
            "web",
            "active",
            "Successful",
            start,
            start + timedelta(seconds=2),
            session=worker_one_session,
            plugin_key="active@OWTF-TEST-001",
        )
        PluginMetrics().record_execution(
            "OWTF-TEST-001",
            "web",
            "active",
            "Error",
            start,
            start + timedelta(seconds=4),
            error="plugin failed",
            session=worker_two_session,
            plugin_key="active@OWTF-TEST-001",
        )
        worker_one_session.commit()
        worker_two_session.commit()

        reader_session = session_factory()
        try:
            summary = PluginMetrics().get_summary(session=reader_session)
            html = HTMLReportGenerator(PluginMetrics()).generate(session=reader_session)
        finally:
            reader_session.close()
    finally:
        worker_one_session.close()
        worker_two_session.close()

    assert summary["active@OWTF-TEST-001"]["code"] == "OWTF-TEST-001"
    assert summary["active@OWTF-TEST-001"]["total_runs"] == 2
    assert summary["active@OWTF-TEST-001"]["successful"] == 1
    assert summary["active@OWTF-TEST-001"]["failed"] == 1
    assert summary["active@OWTF-TEST-001"]["error_count"] == 1
    assert summary["active@OWTF-TEST-001"]["avg_runtime"] == 3
    assert "OWTF-TEST-001" in html
    assert "Total Plugins Run:</strong> 2" in html


def test_metrics_keep_same_code_in_different_plugin_types_separate():
    engine = create_engine("sqlite:///:memory:")
    Model.metadata.create_all(engine, tables=[PluginExecution.__table__])
    session = sessionmaker(bind=engine)()
    start = datetime(2026, 1, 1, 12, 0, 0)

    try:
        metrics = PluginMetrics()
        metrics.record_execution(
            "OWTF-TEST-001",
            "web",
            "active",
            "Successful",
            start,
            start + timedelta(seconds=2),
            session=session,
            plugin_key="active@OWTF-TEST-001",
        )
        metrics.record_execution(
            "OWTF-TEST-001",
            "web",
            "passive",
            "Error",
            start,
            start + timedelta(seconds=4),
            session=session,
            plugin_key="passive@OWTF-TEST-001",
        )

        summary = PluginMetrics().get_summary(session=session)
    finally:
        session.close()

    assert set(summary) == {"active@OWTF-TEST-001", "passive@OWTF-TEST-001"}
    assert summary["active@OWTF-TEST-001"]["successful"] == 1
    assert summary["active@OWTF-TEST-001"]["failed"] == 0
    assert summary["passive@OWTF-TEST-001"]["successful"] == 0
    assert summary["passive@OWTF-TEST-001"]["failed"] == 1


def test_metrics_report_cli_option_is_parsed_without_scan_targets():
    """The report action must be selectable without a target argument."""
    from owtf.lib.cli_options import parse_options

    report_path = "metrics.html"
    options = parse_options(["--metrics-report", report_path], ["web"], ["active"])

    assert options.metrics_report == report_path
    assert options.targets == []
