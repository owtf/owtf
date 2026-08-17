"""
owtf.reports.html_report
~~~~~~~~~~~~~~~~~~~~~~~~

HTML report generation with CVSS severity grouping and plugin metrics.
"""
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class HTMLReportGenerator:
    """Generate HTML reports with metrics and findings."""

    def __init__(self, metrics):
        """Initialize report generator.

        :param metrics: PluginMetrics instance
        """
        self.metrics = metrics

    def generate(self, title="OWTF Security Report", output_file=None):
        """Generate HTML report.

        :param title: Report title
        :param output_file: Output file path (optional)
        :return: HTML string
        """
        summary = self.metrics.get_summary() if self.metrics else {}
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
        .section {{ background: white; margin: 20px 0; padding: 20px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        table {{ width: 100%; border-collapse: collapse; }}
        th {{ background: #34495e; color: white; padding: 10px; text-align: left; }}
        td {{ padding: 10px; border-bottom: 1px solid #ecf0f1; }}
        tr:hover {{ background: #f9f9f9; }}
        .metric-box {{ display: inline-block; margin: 10px; padding: 15px; background: #ecf0f1; border-radius: 5px; }}
        .success {{ color: #27ae60; font-weight: bold; }}
        .warning {{ color: #f39c12; font-weight: bold; }}
        .error {{ color: #e74c3c; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{title}</h1>
        <p>Generated: {timestamp}</p>
    </div>

    <div class="section">
        <h2>Execution Summary</h2>
        <div>
            <div class="metric-box">
                <strong>Total Plugins Run:</strong> {sum(m['total_runs'] for m in summary.values())}
            </div>
            <div class="metric-box">
                <strong>Successful:</strong> <span class="success">{sum(m['successful'] for m in summary.values())}</span>
            </div>
            <div class="metric-box">
                <strong>Failed/Aborted:</strong> <span class="error">{sum(m['aborted'] + m['unreachable'] for m in summary.values())}</span>
            </div>
            <div class="metric-box">
                <strong>Average Success Rate:</strong> {self._avg_success_rate(summary):.1f}%
            </div>
        </div>
    </div>

    <div class="section">
        <h2>Per-Plugin Metrics</h2>
        <table>
            <thead>
                <tr>
                    <th>Plugin Code</th>
                    <th>Tool (Group)</th>
                    <th>Plugin Type</th>
                    <th>Runs</th>
                    <th>Success Rate</th>
                    <th>Avg Runtime</th>
                    <th>Errors</th>
                </tr>
            </thead>
            <tbody>
                {self._generate_plugin_rows(summary)}
            </tbody>
        </table>
    </div>

    <div class="section">
        <h2>Performance Metrics</h2>
        <p><strong>Total Plugin Execution Time:</strong> {self._total_runtime(summary):.2f}s</p>
        <p><strong>Fastest Plugin:</strong> {self._fastest_plugin(summary)}</p>
        <p><strong>Slowest Plugin:</strong> {self._slowest_plugin(summary)}</p>
    </div>
</body>
</html>"""

        if output_file:
            with open(output_file, 'w') as f:
                f.write(html)
            logger.info("Report saved to: %s", output_file)

        return html

    def _generate_plugin_rows(self, summary):
        """Generate table rows for plugins."""
        rows = []
        for code in sorted(summary.keys()):
            m = summary[code]
            success_class = "success" if m['success_rate'] >= 80 else "warning" if m['success_rate'] >= 50 else "error"
            rows.append(f"""
                <tr>
                    <td>{code}</td>
                    <td>{m['group']}</td>
                    <td>{m['type']}</td>
                    <td>{m['total_runs']}</td>
                    <td><span class="{success_class}">{m['success_rate']:.1f}%</span></td>
                    <td>{m['avg_runtime']:.2f}s</td>
                    <td>{m['error_count']}</td>
                </tr>
            """)
        return "".join(rows)

    def _avg_success_rate(self, summary):
        """Calculate average success rate."""
        if not summary:
            return 0
        rates = [m['success_rate'] for m in summary.values()]
        return sum(rates) / len(rates)

    def _total_runtime(self, summary):
        """Calculate total runtime."""
        return sum(m['avg_runtime'] * m['total_runs'] for m in summary.values())

    def _fastest_plugin(self, summary):
        """Find fastest plugin."""
        if not summary:
            return "N/A"
        fastest = min(summary.items(), key=lambda x: x[1]['min_runtime'])
        return f"{fastest[0]} ({fastest[1]['min_runtime']:.2f}s)"

    def _slowest_plugin(self, summary):
        """Find slowest plugin."""
        if not summary:
            return "N/A"
        slowest = max(summary.items(), key=lambda x: x[1]['max_runtime'])
        return f"{slowest[0]} ({slowest[1]['max_runtime']:.2f}s)"
