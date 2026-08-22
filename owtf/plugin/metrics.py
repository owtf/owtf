"""
owtf.plugin.metrics
~~~~~~~~~~~~~~~~~~~

Plugin execution metrics collection, persistence, and reporting.
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class PluginMetrics:
    """Collect per-plugin execution metrics and optionally persist each event."""

    def __init__(self):
        self.metrics = {}  # plugin_code -> metrics dict

    @staticmethod
    def _new_metric(plugin_group, plugin_type):
        return {
            "group": plugin_group,
            "type": plugin_type,
            "runs": 0,
            "successful": 0,
            "aborted": 0,
            "unreachable": 0,
            "failed": 0,
            "timeouts": 0,
            "total_runtime": 0.0,
            "min_runtime": float("inf"),
            "max_runtime": 0.0,
            "errors": [],
        }

    @staticmethod
    def _add_execution(metrics, plugin_code, plugin_group, plugin_type, status, start_time, end_time, error=None):
        if plugin_code not in metrics:
            metrics[plugin_code] = PluginMetrics._new_metric(plugin_group, plugin_type)

        metric = metrics[plugin_code]
        metric["runs"] += 1
        if status == "Successful":
            metric["successful"] += 1
        elif status in ("Aborted", "Aborted (by user)", "Aborted (Framework Exit)"):
            metric["aborted"] += 1
        elif status == "Unreachable Target":
            metric["unreachable"] += 1
        elif status == "Error":
            metric["failed"] += 1
        elif status == "Timeout":
            metric["timeouts"] += 1

        if start_time and end_time:
            runtime = (end_time - start_time).total_seconds()
            metric["total_runtime"] += runtime
            metric["min_runtime"] = min(metric["min_runtime"], runtime)
            metric["max_runtime"] = max(metric["max_runtime"], runtime)

        if error:
            metric["errors"].append(str(error))

    def record_execution(
        self,
        plugin_code,
        plugin_group,
        plugin_type,
        status,
        start_time,
        end_time,
        error=None,
        session=None,
    ):
        """Record one execution, persisting it when a worker session is supplied.

        The database record is deliberately an event row rather than an aggregate
        row.  This makes concurrent worker writes independent and lets reporting
        aggregate every execution after workers have exited.
        """
        self._add_execution(
            self.metrics,
            plugin_code,
            plugin_group,
            plugin_type,
            status,
            start_time,
            end_time,
            error,
        )

        if session is not None:
            from owtf.models.plugin_execution import PluginExecution

            session.add(
                PluginExecution(
                    plugin_code=plugin_code,
                    plugin_group=plugin_group,
                    plugin_type=plugin_type,
                    status=status,
                    start_time=start_time,
                    end_time=end_time,
                    error=str(error) if error else None,
                )
            )
            # Commit before output persistence/deduplication.  A duplicate save
            # intentionally returns early, but the execution must still count.
            session.commit()

        self._log_execution(plugin_code, plugin_group, status, start_time, end_time)

    @classmethod
    def _summary_from_rows(cls, rows):
        metrics = {}
        for row in rows:
            cls._add_execution(
                metrics,
                row.plugin_code,
                row.plugin_group,
                row.plugin_type,
                row.status,
                row.start_time,
                row.end_time,
                row.error,
            )
        return cls._summary_from_metrics(metrics)

    @staticmethod
    def _summary_from_metrics(metrics):
        summary = {}
        for code, metric in metrics.items():
            summary[code] = {
                "group": metric["group"],
                "type": metric["type"],
                "total_runs": metric["runs"],
                "success_rate": (metric["successful"] / metric["runs"] * 100) if metric["runs"] > 0 else 0,
                "successful": metric["successful"],
                "aborted": metric["aborted"],
                "unreachable": metric["unreachable"],
                "failed": metric["failed"],
                "timeouts": metric["timeouts"],
                "avg_runtime": (metric["total_runtime"] / metric["runs"]) if metric["runs"] > 0 else 0,
                "min_runtime": metric["min_runtime"] if metric["min_runtime"] != float("inf") else 0,
                "max_runtime": metric["max_runtime"],
                "error_count": len(metric["errors"]),
            }
        return summary

    def _log_execution(self, plugin_code, plugin_group, status, start_time, end_time):
        """Log execution in structured format for parsing."""
        if start_time and end_time:
            duration = (end_time - start_time).total_seconds()
        else:
            duration = 0
        log_line = f"METRIC|{datetime.now().isoformat()}|{plugin_code}|{plugin_group}|{status}|{duration:.2f}s"
        logger.info(log_line)

    def get_summary(self, session=None):
        """Return metrics from memory or aggregate persisted worker events.

        Passing a session is the report/API path.  It intentionally ignores the
        caller's in-memory dictionary so a parent process sees all worker runs.
        """
        if session is not None:
            from owtf.models.plugin_execution import PluginExecution

            return self._summary_from_rows(session.query(PluginExecution).all())
        return self._summary_from_metrics(self.metrics)

    def get_dashboard(self, session=None):
        """Get metrics in dashboard format."""
        summary = self.get_summary(session=session)
        if not summary:
            return "No plugin executions recorded."

        lines = ["Plugin Execution Metrics", "=" * 80]
        lines.append(f"{'Plugin':<25} {'Runs':<6} {'Success':<10} {'Avg Time':<12} {'Errors':<8}")
        lines.append("-" * 80)

        for code in sorted(summary.keys()):
            metric = summary[code]
            lines.append(
                f"{code:<25} {metric['total_runs']:<6} {metric['success_rate']:.1f}%     "
                f"{metric['avg_runtime']:.2f}s       {metric['error_count']:<8}"
            )

        return "\n".join(lines)

    def get_recommendations(self):
        """Get performance recommendations based on in-memory metrics."""
        from owtf.performance import PerformanceOptimizer

        return PerformanceOptimizer.optimize_based_on_metrics(self)


# Kept for callers that use the lightweight in-process collector directly.
_metrics_instance = None


def get_metrics():
    """Get or create the process-local metrics collector."""
    global _metrics_instance
    if _metrics_instance is None:
        _metrics_instance = PluginMetrics()
    return _metrics_instance
