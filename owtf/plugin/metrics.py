"""
owtf.plugin.metrics
~~~~~~~~~~~~~~~~~~~

Plugin execution metrics collection and reporting.
"""
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class PluginMetrics:
    """Collect and store per-plugin execution metrics."""

    def __init__(self):
        self.metrics = {}  # plugin_code -> metrics dict

    def record_execution(self, plugin_code, plugin_group, plugin_type, status, start_time, end_time, error=None):
        """Record a plugin execution.

        :param plugin_code: Plugin code (e.g., "OWTF-WVS-001")
        :param plugin_group: Plugin group (e.g., "web")
        :param plugin_type: Plugin type (e.g., "active")
        :param status: Execution status ("Successful", "Aborted", "Unreachable", etc.)
        :param start_time: Execution start datetime
        :param end_time: Execution end datetime
        :param error: Error message if failed (optional)
        """
        if plugin_code not in self.metrics:
            self.metrics[plugin_code] = {
                "group": plugin_group,
                "type": plugin_type,
                "runs": 0,
                "successful": 0,
                "aborted": 0,
                "unreachable": 0,
                "total_runtime": 0.0,
                "min_runtime": float('inf'),
                "max_runtime": 0.0,
                "errors": [],
            }

        m = self.metrics[plugin_code]
        m["runs"] += 1

        # Track status
        if status == "Successful":
            m["successful"] += 1
        elif status in ("Aborted", "Aborted (by user)"):
            m["aborted"] += 1
        elif status == "Unreachable Target":
            m["unreachable"] += 1

        # Calculate runtime
        if start_time and end_time:
            runtime = (end_time - start_time).total_seconds()
            m["total_runtime"] += runtime
            m["min_runtime"] = min(m["min_runtime"], runtime)
            m["max_runtime"] = max(m["max_runtime"], runtime)

        # Track errors
        if error:
            m["errors"].append(error)

        # Structured logging
        self._log_execution(plugin_code, plugin_group, status, start_time, end_time)

    def _log_execution(self, plugin_code, plugin_group, status, start_time, end_time):
        """Log execution in structured format for parsing.

        Format: METRIC|timestamp|plugin_code|group|status|duration_seconds
        """
        if start_time and end_time:
            duration = (end_time - start_time).total_seconds()
        else:
            duration = 0

        log_line = f"METRIC|{datetime.now().isoformat()}|{plugin_code}|{plugin_group}|{status}|{duration:.2f}s"
        logger.info(log_line)

    def get_summary(self):
        """Get metrics summary for all plugins.

        :return: Dictionary of metrics by plugin code
        :rtype: `dict`
        """
        summary = {}
        for code, m in self.metrics.items():
            summary[code] = {
                "group": m["group"],
                "type": m["type"],
                "total_runs": m["runs"],
                "success_rate": (m["successful"] / m["runs"] * 100) if m["runs"] > 0 else 0,
                "successful": m["successful"],
                "aborted": m["aborted"],
                "unreachable": m["unreachable"],
                "avg_runtime": (m["total_runtime"] / m["runs"]) if m["runs"] > 0 else 0,
                "min_runtime": m["min_runtime"] if m["min_runtime"] != float('inf') else 0,
                "max_runtime": m["max_runtime"],
                "error_count": len(m["errors"]),
            }
        return summary

    def get_dashboard(self):
        """Get metrics in dashboard format.

        :return: Formatted string for display
        :rtype: `str`
        """
        summary = self.get_summary()
        if not summary:
            return "No plugin executions recorded."

        lines = ["Plugin Execution Metrics", "=" * 80]
        lines.append(f"{'Plugin':<25} {'Runs':<6} {'Success':<10} {'Avg Time':<12} {'Errors':<8}")
        lines.append("-" * 80)

        for code in sorted(summary.keys()):
            m = summary[code]
            avg_time = f"{m['avg_runtime']:.2f}s"
            success = f"{m['success_rate']:.1f}%"
            lines.append(
                f"{code:<25} {m['total_runs']:<6} {success:<10} {avg_time:<12} {m['error_count']:<8}"
            )

        return "\n".join(lines)

    def get_recommendations(self):
        """Get performance recommendations based on metrics.
        
        :return: List of optimization recommendations
        :rtype: `list`
        """
        from owtf.performance import PerformanceOptimizer
        return PerformanceOptimizer.optimize_based_on_metrics(self)

# Global metrics instance
_metrics_instance = None


def get_metrics():
    """Get or create global metrics instance.

    :return: PluginMetrics instance
    :rtype: PluginMetrics
    """
    global _metrics_instance
    if _metrics_instance is None:
        _metrics_instance = PluginMetrics()
    return _metrics_instance
