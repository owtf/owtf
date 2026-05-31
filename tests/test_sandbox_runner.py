"""
tests/test_sandbox_runner.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Integration tests for owtf.plugin.sandbox.SandboxRunner.

These tests actually spawn subprocesses and verify the isolation guarantees.

Run with:
    python -m pytest tests/test_sandbox_runner.py -v
"""

import os
import textwrap

from owtf.plugin.sandbox import SandboxRunner

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_plugin(tmp_path, source: str) -> str:
    p = tmp_path / "plugin.py"
    p.write_text(textwrap.dedent(source))
    return str(p)


# ---------------------------------------------------------------------------
# Tests: success cases
# ---------------------------------------------------------------------------


class TestSandboxSuccess:
    def test_simple_plugin_returns_json(self, tmp_path):
        plugin = make_plugin(
            tmp_path,
            """
            DESCRIPTION = "Simple test plugin"
            def run(target_url):
                return {"target": target_url, "status": "ok"}
            """,
        )
        result = SandboxRunner.run(plugin, "https://example.com", timeout=30)
        assert result.success
        assert result.output["target"] == "https://example.com"
        assert result.output["status"] == "ok"

    def test_elapsed_time_recorded(self, tmp_path):
        plugin = make_plugin(
            tmp_path,
            """
            import time
            DESCRIPTION = "Timing plugin"
            def run(target_url):
                time.sleep(0.1)
                return {"done": True}
            """,
        )
        result = SandboxRunner.run(plugin, "https://example.com", timeout=30)
        assert result.success
        assert result.elapsed_seconds >= 0.1

    def test_plugin_can_use_subprocess_without_shell(self, tmp_path):
        plugin = make_plugin(
            tmp_path,
            """
            import subprocess, json
            DESCRIPTION = "subprocess test"
            def run(target_url):
                r = subprocess.run(["echo", "hello"], capture_output=True, text=True)
                return {"output": r.stdout.strip()}
            """,
        )
        result = SandboxRunner.run(plugin, "https://example.com", timeout=30)
        assert result.success
        assert result.output["output"] == "hello"

    def test_exit_code_zero_on_success(self, tmp_path):
        plugin = make_plugin(
            tmp_path,
            """
            DESCRIPTION = "ok"
            def run(t): return {}
            """,
        )
        result = SandboxRunner.run(plugin, "https://x.com", timeout=30)
        assert result.exit_code == 0


# ---------------------------------------------------------------------------
# Tests: error cases
# ---------------------------------------------------------------------------


class TestSandboxErrors:
    def test_missing_file_returns_failure(self):
        result = SandboxRunner.run("/nonexistent/plugin.py", "https://example.com", timeout=10)
        assert not result.success
        assert "not found" in result.error.lower()

    def test_plugin_with_exception_returns_failure(self, tmp_path):
        plugin = make_plugin(
            tmp_path,
            """
            DESCRIPTION = "Crashing plugin"
            def run(target_url):
                raise RuntimeError("intentional crash")
            """,
        )
        result = SandboxRunner.run(plugin, "https://example.com", timeout=30)
        assert not result.success
        assert result.exit_code != 0

    def test_plugin_with_invalid_json_output_returns_failure(self, tmp_path):
        plugin = make_plugin(
            tmp_path,
            """
            DESCRIPTION = "Bad output"
            def run(target_url):
                print("this is not json")
            """,
        )
        result = SandboxRunner.run(plugin, "https://example.com", timeout=30)
        assert not result.success
        assert "not valid JSON" in result.error or "JSON" in result.error

    def test_plugin_timeout_is_enforced(self, tmp_path):
        plugin = make_plugin(
            tmp_path,
            """
            import time
            DESCRIPTION = "Infinite loop"
            def run(target_url):
                time.sleep(9999)
                return {}
            """,
        )
        result = SandboxRunner.run(plugin, "https://example.com", timeout=2)
        assert not result.success
        assert result.timed_out

    def test_syntax_error_in_plugin_returns_failure(self, tmp_path):
        plugin = make_plugin(
            tmp_path,
            """
            def broken(:
            """,
        )
        result = SandboxRunner.run(plugin, "https://example.com", timeout=15)
        assert not result.success


# ---------------------------------------------------------------------------
# Tests: isolation guarantees
# ---------------------------------------------------------------------------


class TestSandboxIsolation:
    def test_workdir_is_cleaned_up(self, tmp_path):
        """After execution, the sandbox temp dir should not persist."""
        plugin = make_plugin(
            tmp_path,
            """
            import os
            DESCRIPTION = "Path probe"
            def run(target_url):
                return {"cwd": os.getcwd()}
            """,
        )
        import tempfile

        before = set(os.listdir(tempfile.gettempdir()))
        SandboxRunner.run(plugin, "https://example.com", timeout=15)
        after = set(os.listdir(tempfile.gettempdir()))
        # Any sandbox dirs we created should be gone
        new_dirs = after - before
        sandbox_dirs = [d for d in new_dirs if d.startswith("owtf_sandbox_")]
        assert len(sandbox_dirs) == 0, "Sandbox workdir not cleaned up: {}".format(sandbox_dirs)

    def test_plugin_runs_in_separate_process(self, tmp_path):
        """The child's PID must differ from ours."""
        plugin = make_plugin(
            tmp_path,
            """
            import os
            DESCRIPTION = "PID check"
            def run(target_url):
                return {"pid": os.getpid()}
            """,
        )
        result = SandboxRunner.run(plugin, "https://example.com", timeout=15)
        assert result.success
        assert result.output["pid"] != os.getpid()
