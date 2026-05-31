"""
owtf.plugin.sandbox
~~~~~~~~~~~~~~~~~~~

Isolated subprocess-based execution engine for community plugins.

Security model
--------------
Community plugins execute in a child process spawned via subprocess.  The child
process is given:
  - a configurable wall-clock timeout (default 300 s)
  - an optional memory ceiling via the `resource` module (Linux/macOS only)
  - no inherited file descriptors beyond stdin/stdout/stderr
  - a dedicated temporary working directory that is cleaned up after execution

The parent process captures stdout (JSON findings) and stderr (diagnostics)
without trusting them for execution; they are treated as opaque text.

The subprocess wrapper script (`_RUNNER_WRAPPER`) is generated at runtime and
written to a temp file so no import path tricks are needed.

Return value contract
---------------------
On success, SandboxRunner expects the child process to write a single JSON
object to stdout and exit with code 0.  Any other exit code is treated as a
plugin error, and the raw stderr is surfaced to the caller.
"""

import json
import logging
import os
import subprocess
import sys
import tempfile
import textwrap
import time
from typing import Any, Dict, Optional

from owtf.settings import (
    COMMUNITY_PLUGIN_DEFAULT_TIMEOUT,
    COMMUNITY_PLUGIN_MEMORY_LIMIT,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Wrapper script injected into the child process
# ---------------------------------------------------------------------------
# This script is the only code the child runs before importing the plugin.
# It sets the resource limit (where supported), imports the plugin by path,
# calls run(target_url), and prints JSON to stdout.
# Shell expansion attacks are impossible here because the wrapper is written
# to a temp file and executed as `python wrapper.py` — no shell involved.

_RUNNER_WRAPPER_TEMPLATE = textwrap.dedent(
    """\
    import json
    import os
    import sys
    import importlib.util

    # ---- optional memory ceiling (Linux/macOS only) ----
    try:
        import resource
        soft, hard = resource.getrlimit(resource.RLIMIT_AS)
        limit = {memory_limit}
        if limit > 0:
            new_hard = hard if hard == resource.RLIM_INFINITY else max(hard, limit)
            resource.setrlimit(resource.RLIMIT_AS, (limit, new_hard))
    except Exception:
        pass  # Windows or older kernels: silently skip

    # ---- load the plugin module from an absolute path ----
    plugin_path = {plugin_path!r}
    target_url  = {target_url!r}

    spec   = importlib.util.spec_from_file_location("_community_plugin", plugin_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    result = module.run(target_url)
    print(json.dumps(result))
    """
)


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------


class SandboxResult:
    """Carries the outcome of a sandboxed plugin run."""

    __slots__ = ("success", "output", "error", "exit_code", "elapsed_seconds", "timed_out")

    def __init__(
        self,
        success: bool,
        output: Optional[Dict[str, Any]] = None,
        error: str = "",
        exit_code: int = 0,
        elapsed_seconds: float = 0.0,
        timed_out: bool = False,
    ):
        self.success = success
        self.output = output or {}
        self.error = error
        self.exit_code = exit_code
        self.elapsed_seconds = elapsed_seconds
        self.timed_out = timed_out

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "exit_code": self.exit_code,
            "elapsed_seconds": round(self.elapsed_seconds, 3),
            "timed_out": self.timed_out,
        }


# ---------------------------------------------------------------------------
# SandboxRunner
# ---------------------------------------------------------------------------


class SandboxRunner:
    """
    Runs a community plugin file in an isolated child process.

    Usage::

        result = SandboxRunner.run(
            plugin_path="/path/to/plugin.py",
            target_url="https://example.com",
            timeout=120,
            memory_limit=134217728,  # 128 MB
        )
        if result.success:
            print(result.output)
        else:
            print("Error:", result.error)
    """

    @staticmethod
    def run(
        plugin_path: str,
        target_url: str,
        timeout: int = COMMUNITY_PLUGIN_DEFAULT_TIMEOUT,
        memory_limit: int = COMMUNITY_PLUGIN_MEMORY_LIMIT,
    ) -> SandboxResult:
        """Execute *plugin_path* against *target_url* in isolation."""

        if not os.path.isfile(plugin_path):
            return SandboxResult(
                success=False,
                error="Plugin file not found: {}".format(plugin_path),
                exit_code=-1,
            )

        wrapper_code = _RUNNER_WRAPPER_TEMPLATE.format(
            plugin_path=plugin_path,
            target_url=target_url,
            memory_limit=memory_limit,
        )

        workdir = tempfile.mkdtemp(prefix="owtf_sandbox_")
        wrapper_path = os.path.join(workdir, "_runner.py")

        try:
            with open(wrapper_path, "w", encoding="utf-8") as fh:
                fh.write(wrapper_code)

            cmd = [sys.executable, wrapper_path]

            # Isolated environment: pass through only essential variables.
            env = _build_isolated_env()

            t_start = time.monotonic()
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=workdir,
                env=env,
                close_fds=True,
            )

            timed_out = False
            try:
                stdout_bytes, stderr_bytes = proc.communicate(timeout=timeout)
            except subprocess.TimeoutExpired:
                proc.kill()
                stdout_bytes, stderr_bytes = proc.communicate()
                timed_out = True

            elapsed = time.monotonic() - t_start
            exit_code = proc.returncode

            stdout_text = stdout_bytes.decode("utf-8", errors="replace").strip()
            stderr_text = stderr_bytes.decode("utf-8", errors="replace").strip()

            if timed_out:
                logger.warning("Community plugin timed out after %ss: %s", timeout, plugin_path)
                return SandboxResult(
                    success=False,
                    error="Plugin execution timed out after {}s".format(timeout),
                    exit_code=-9,
                    elapsed_seconds=elapsed,
                    timed_out=True,
                )

            if exit_code != 0:
                logger.error(
                    "Community plugin exited with code %d: %s\nstderr: %s",
                    exit_code,
                    plugin_path,
                    stderr_text[:2000],
                )
                return SandboxResult(
                    success=False,
                    error=stderr_text[:4096] or "Plugin exited with code {}".format(exit_code),
                    exit_code=exit_code,
                    elapsed_seconds=elapsed,
                )

            # Parse JSON output from stdout
            try:
                output = json.loads(stdout_text)
            except json.JSONDecodeError as exc:
                logger.error("Plugin output is not valid JSON: %s", exc)
                return SandboxResult(
                    success=False,
                    error="Plugin output is not valid JSON: {}. Raw output: {}".format(exc, stdout_text[:500]),
                    exit_code=exit_code,
                    elapsed_seconds=elapsed,
                )

            if stderr_text:
                logger.debug("Plugin stderr: %s", stderr_text[:1000])

            return SandboxResult(
                success=True,
                output=output,
                exit_code=exit_code,
                elapsed_seconds=elapsed,
            )

        except Exception as exc:
            logger.exception("Unexpected error running community plugin: %s", exc)
            return SandboxResult(
                success=False,
                error="Internal error: {}".format(str(exc)),
                exit_code=-1,
            )
        finally:
            _cleanup_workdir(workdir)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_isolated_env() -> Dict[str, str]:
    """Return a minimal environment dict for the child process.

    We intentionally strip most environment variables to reduce the attack
    surface.  PATH is preserved so that plugins can locate tools like nuclei.
    """
    env: Dict[str, str] = {}
    for key in ("PATH", "HOME", "LANG", "LC_ALL", "LC_CTYPE", "TMPDIR", "TMP", "TEMP"):
        val = os.environ.get(key)
        if val:
            env[key] = val
    # Ensure the child can find the Python stdlib
    if "PYTHONPATH" in os.environ:
        env["PYTHONPATH"] = os.environ["PYTHONPATH"]
    # Safety: do not propagate credentials, tokens, DB passwords, etc.
    return env


def _cleanup_workdir(path: str) -> None:
    """Remove the temporary working directory and all its contents."""
    import shutil  # local import — only needed here, not in plugin code

    try:
        shutil.rmtree(path, ignore_errors=True)
    except Exception as exc:
        logger.warning("Could not clean up sandbox workdir %s: %s", path, exc)
