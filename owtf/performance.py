"""
owtf.performance
~~~~~~~~~~~~~~~~

Performance optimizations for GSoC 2026 phases.
"""
import logging

logger = logging.getLogger(__name__)


class PerformanceOptimizer:
    """Apply performance optimizations based on metrics."""

    @staticmethod
    def optimize_based_on_metrics(metrics):
        """Analyze metrics and suggest optimizations.

        :param metrics: PluginMetrics instance
        :return: List of optimization recommendations
        """
        summary = metrics.get_summary()
        recommendations = []

        # Optimization 1: Identify slow plugins
        slow_plugins = [
            (code, m) for code, m in summary.items()
            if m['avg_runtime'] > 30  # Plugins taking > 30 seconds
        ]
        if slow_plugins:
            recommendations.append({
                "type": "slow_plugin",
                "message": f"Plugins running slow (>30s): {[p[0] for p in slow_plugins]}. Consider timeout or async execution.",
                "affected": [p[0] for p in slow_plugins]
            })

        # Optimization 2: Identify failed plugins
        failed_plugins = [
            (code, m) for code, m in summary.items()
            if m['success_rate'] < 50  # Less than 50% success
        ]
        if failed_plugins:
            recommendations.append({
                "type": "failed_plugin",
                "message": f"Plugins with low success rate (<50%): {[p[0] for p in failed_plugins]}. Check configuration or skip unreliable plugins.",
                "affected": [p[0] for p in failed_plugins]
            })

        # Optimization 3: Batch size tuning
        avg_runtime = sum(m['avg_runtime'] for m in summary.values()) / len(summary) if summary else 0
        if avg_runtime < 5:
            recommendations.append({
                "type": "batch_size",
                "message": "Plugins run quickly (<5s avg). Increase WORKER_BATCH_SIZE for better throughput.",
                "current_setting": "WORKER_BATCH_SIZE = 5",
                "suggested": "WORKER_BATCH_SIZE = 10"
            })

        # Optimization 4: Worker count tuning
        total_runs = sum(m['total_runs'] for m in summary.values())
        if total_runs > 100:
            recommendations.append({
                "type": "worker_count",
                "message": "High plugin volume (>100 runs). Consider increasing WORKER_MAX_PROCESSES.",
                "current_setting": "WORKER_MAX_PROCESSES = 8",
                "suggested": "WORKER_MAX_PROCESSES = 12"
            })

        return recommendations

    @staticmethod
    def log_optimizations(recommendations):
        """Log optimization recommendations.

        :param recommendations: List of optimization dicts
        """
        for rec in recommendations:
            logger.info(
                "OPTIMIZATION|%s|%s|%s",
                rec['type'],
                rec['message'],
                rec.get('affected', '')
            )
