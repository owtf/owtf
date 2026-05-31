"""
tests/test_plugin_validator.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Unit tests for owtf.plugin.validator.PluginValidator.

Run with:
    python -m pytest tests/test_plugin_validator.py -v
"""

from owtf.plugin.validator import PluginValidator

# ---------------------------------------------------------------------------
# Fixtures: minimal valid plugin
# ---------------------------------------------------------------------------

VALID_PLUGIN = """
DESCRIPTION = "A safe example plugin"

def run(target_url):
    import json
    import subprocess
    result = subprocess.run(["curl", "-sI", target_url], capture_output=True, timeout=10)
    return {"output": result.stdout.decode()}
"""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def validate(source: str):
    return PluginValidator.validate_source(source, filename="<test>")


# ---------------------------------------------------------------------------
# Tests: valid plugins
# ---------------------------------------------------------------------------


class TestValidPlugins:
    def test_minimal_valid_plugin_passes(self):
        result = validate(VALID_PLUGIN)
        assert result.passed, str(result)

    def test_subprocess_run_without_shell_is_allowed(self):
        source = """
DESCRIPTION = "Nuclei test"

def run(target_url):
    import subprocess
    r = subprocess.run(["nuclei", "-u", target_url, "-json"], capture_output=True)
    return {"raw": r.stdout.decode()}
"""
        result = validate(source)
        assert result.passed, str(result)

    def test_requests_import_is_allowed(self):
        source = """
DESCRIPTION = "HTTP checker"

def run(target_url):
    import requests
    r = requests.get(target_url, timeout=10)
    return {"status": r.status_code}
"""
        result = validate(source)
        assert result.passed, str(result)

    def test_json_and_urllib_allowed(self):
        source = """
import json
import urllib.request

DESCRIPTION = "Header checker"

def run(target_url):
    with urllib.request.urlopen(target_url, timeout=5) as r:
        return {"headers": dict(r.headers)}
"""
        result = validate(source)
        assert result.passed, str(result)


# ---------------------------------------------------------------------------
# Tests: blocked imports
# ---------------------------------------------------------------------------


class TestBlockedImports:
    def test_os_import_blocked(self):
        source = """
import os
DESCRIPTION = "Bad"
def run(target_url): return {}
"""
        result = validate(source)
        assert not result.passed
        assert any("os" in v for v in result.violations)

    def test_socket_import_blocked(self):
        source = """
import socket
DESCRIPTION = "Bad"
def run(target_url): return {}
"""
        result = validate(source)
        assert not result.passed
        assert any("socket" in v for v in result.violations)

    def test_sys_import_blocked(self):
        source = """
import sys
DESCRIPTION = "Bad"
def run(target_url): return {}
"""
        result = validate(source)
        assert not result.passed

    def test_pickle_import_blocked(self):
        source = """
import pickle
DESCRIPTION = "Bad"
def run(target_url): return {}
"""
        result = validate(source)
        assert not result.passed

    def test_from_os_import_blocked(self):
        source = """
from os import system
DESCRIPTION = "Bad"
def run(target_url): return {}
"""
        result = validate(source)
        assert not result.passed

    def test_threading_blocked(self):
        source = """
import threading
DESCRIPTION = "Bad"
def run(target_url): return {}
"""
        result = validate(source)
        assert not result.passed


# ---------------------------------------------------------------------------
# Tests: blocked calls
# ---------------------------------------------------------------------------


class TestBlockedCalls:
    def test_eval_blocked(self):
        source = """
DESCRIPTION = "Bad"
def run(target_url):
    return eval("1+1")
"""
        result = validate(source)
        assert not result.passed
        assert any("eval" in v for v in result.violations)

    def test_exec_blocked(self):
        source = """
DESCRIPTION = "Bad"
def run(target_url):
    exec("import os")
    return {}
"""
        result = validate(source)
        assert not result.passed
        assert any("exec" in v for v in result.violations)

    def test_compile_blocked(self):
        source = """
DESCRIPTION = "Bad"
def run(target_url):
    c = compile("1+1", "<string>", "eval")
    return {}
"""
        result = validate(source)
        assert not result.passed

    def test_os_system_attr_call_blocked(self):
        source = """
import subprocess
DESCRIPTION = "Bad"
def run(target_url):
    import os
    os.system("ls")
    return {}
"""
        result = validate(source)
        assert not result.passed

    def test_subprocess_shell_true_blocked(self):
        source = """
import subprocess
DESCRIPTION = "Shell injection risk"
def run(target_url):
    subprocess.run("curl " + target_url, shell=True)
    return {}
"""
        result = validate(source)
        assert not result.passed
        assert any("shell=True" in v for v in result.violations)

    def test_open_write_mode_blocked(self):
        source = """
DESCRIPTION = "Write attempt"
def run(target_url):
    with open("/etc/passwd", "w") as f:
        f.write("pwned")
    return {}
"""
        result = validate(source)
        assert not result.passed
        assert any("write" in v.lower() or "mode" in v.lower() for v in result.violations)

    def test_open_append_mode_blocked(self):
        source = """
DESCRIPTION = "Append attempt"
def run(target_url):
    open("/tmp/evil", "ab")
    return {}
"""
        result = validate(source)
        assert not result.passed

    def test_open_read_allowed(self):
        source = """
DESCRIPTION = "Read-only file access is fine"
def run(target_url):
    with open("/etc/hosts", "r") as f:
        return {"data": f.read()}
"""
        result = validate(source)
        assert result.passed, str(result)


# ---------------------------------------------------------------------------
# Tests: missing required structure
# ---------------------------------------------------------------------------


class TestRequiredStructure:
    def test_missing_description_fails(self):
        source = """
def run(target_url):
    return {}
"""
        result = validate(source)
        assert not result.passed
        assert any("DESCRIPTION" in v for v in result.violations)

    def test_missing_run_function_fails(self):
        source = """
DESCRIPTION = "No run function"
def something_else():
    return {}
"""
        result = validate(source)
        assert not result.passed
        assert any("run" in v for v in result.violations)

    def test_both_missing_fails(self):
        source = """
x = 1
"""
        result = validate(source)
        assert not result.passed
        assert len(result.violations) >= 2

    def test_syntax_error_returns_failure(self):
        source = "def run(:"  # broken syntax
        result = validate(source)
        assert not result.passed
        assert any("SyntaxError" in v or "syntax" in v.lower() for v in result.violations)


# ---------------------------------------------------------------------------
# Tests: async functions
# ---------------------------------------------------------------------------


class TestAsyncFunctions:
    def test_async_function_blocked(self):
        source = """
DESCRIPTION = "Async plugin"
async def run(target_url):
    return {}
"""
        result = validate(source)
        assert not result.passed
        assert any("async" in v.lower() for v in result.violations)


# ---------------------------------------------------------------------------
# Tests: validate_file helper
# ---------------------------------------------------------------------------


class TestValidateFile:
    def test_file_not_found(self, tmp_path):
        result = PluginValidator.validate_file(str(tmp_path / "nonexistent.py"))
        assert not result.passed
        assert any("Cannot read" in v or "No such" in v for v in result.violations)

    def test_valid_file_passes(self, tmp_path):
        p = tmp_path / "ok.py"
        p.write_text(VALID_PLUGIN)
        result = PluginValidator.validate_file(str(p))
        assert result.passed, str(result)


# ---------------------------------------------------------------------------
# Tests: validate_bytes
# ---------------------------------------------------------------------------


class TestValidateBytes:
    def test_valid_bytes_passes(self):
        result = PluginValidator.validate_bytes(VALID_PLUGIN.encode("utf-8"))
        assert result.passed, str(result)

    def test_invalid_bytes_fails(self):
        source = b"import os\nDESCRIPTION='x'\ndef run(t): os.system('id')"
        result = PluginValidator.validate_bytes(source)
        assert not result.passed
