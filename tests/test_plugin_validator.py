"""Tests for the community plugin AST validator."""

from owtf.plugin.validator import PluginValidator

VALID_PLUGIN = """
DESCRIPTION = "A safe example plugin"

def run(PluginInfo):
    import json
    import subprocess
    target_url = PluginInfo["target_url"]
    result = subprocess.run(["curl", "-sI", target_url], capture_output=True, timeout=10)
    return {"output": result.stdout.decode()}
"""


def validate(source):
    return PluginValidator.validate_source(source, filename="<test>")


class TestValidPlugins:
    def test_minimal_valid_plugin_passes(self):
        result = validate(VALID_PLUGIN)
        assert result.passed, str(result)

    def test_subprocess_run_without_shell_is_allowed(self):
        source = """
DESCRIPTION = "Nuclei test"

def run(PluginInfo):
    import subprocess
    target_url = PluginInfo["target_url"]
    r = subprocess.run(["nuclei", "-u", target_url, "-json"], capture_output=True)
    return {"raw": r.stdout.decode()}
"""
        result = validate(source)
        assert result.passed, str(result)

    def test_requests_import_is_allowed(self):
        source = """
DESCRIPTION = "HTTP checker"

def run(PluginInfo):
    import requests
    r = requests.get(PluginInfo["target_url"], timeout=10)
    return {"status": r.status_code}
"""
        result = validate(source)
        assert result.passed, str(result)

    def test_json_and_urllib_allowed(self):
        source = """
import json
import urllib.request

DESCRIPTION = "Header checker"

def run(PluginInfo):
    with urllib.request.urlopen(PluginInfo["target_url"], timeout=5) as r:
        return {"headers": dict(r.headers)}
"""
        result = validate(source)
        assert result.passed, str(result)


class TestBlockedImports:
    def test_os_import_blocked(self):
        source = """
import os
DESCRIPTION = "Bad"
def run(PluginInfo): return {}
"""
        result = validate(source)
        assert not result.passed
        assert any("os" in v for v in result.violations)

    def test_socket_import_blocked(self):
        source = """
import socket
DESCRIPTION = "Bad"
def run(PluginInfo): return {}
"""
        result = validate(source)
        assert not result.passed
        assert any("socket" in v for v in result.violations)

    def test_sys_import_blocked(self):
        source = """
import sys
DESCRIPTION = "Bad"
def run(PluginInfo): return {}
"""
        result = validate(source)
        assert not result.passed

    def test_pickle_import_blocked(self):
        source = """
import pickle
DESCRIPTION = "Bad"
def run(PluginInfo): return {}
"""
        result = validate(source)
        assert not result.passed

    def test_from_os_import_blocked(self):
        source = """
from os import system
DESCRIPTION = "Bad"
def run(PluginInfo): return {}
"""
        result = validate(source)
        assert not result.passed

    def test_threading_blocked(self):
        source = """
import threading
DESCRIPTION = "Bad"
def run(PluginInfo): return {}
"""
        result = validate(source)
        assert not result.passed


class TestBlockedCalls:
    def test_eval_blocked(self):
        source = """
DESCRIPTION = "Bad"
def run(PluginInfo):
    return eval("1+1")
"""
        result = validate(source)
        assert not result.passed
        assert any("eval" in v for v in result.violations)

    def test_exec_blocked(self):
        source = """
DESCRIPTION = "Bad"
def run(PluginInfo):
    exec("import os")
    return {}
"""
        result = validate(source)
        assert not result.passed
        assert any("exec" in v for v in result.violations)

    def test_compile_blocked(self):
        source = """
DESCRIPTION = "Bad"
def run(PluginInfo):
    c = compile("1+1", "<string>", "eval")
    return {}
"""
        result = validate(source)
        assert not result.passed

    def test_os_system_attr_call_blocked(self):
        source = """
import subprocess
DESCRIPTION = "Bad"
def run(PluginInfo):
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
def run(PluginInfo):
    subprocess.run("curl " + PluginInfo["target_url"], shell=True)
    return {}
"""
        result = validate(source)
        assert not result.passed
        assert any("shell=True" in v for v in result.violations)

    def test_open_write_mode_blocked(self):
        source = """
DESCRIPTION = "Write attempt"
def run(PluginInfo):
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
def run(PluginInfo):
    open("/tmp/evil", "ab")
    return {}
"""
        result = validate(source)
        assert not result.passed

    def test_open_read_allowed(self):
        source = """
DESCRIPTION = "Read-only file access is fine"
def run(PluginInfo):
    with open("/etc/hosts", "r") as f:
        return {"data": f.read()}
"""
        result = validate(source)
        assert result.passed, str(result)


class TestRequiredStructure:
    def test_missing_description_fails(self):
        source = """
def run(PluginInfo):
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

    def test_run_with_plugininfo_signature_passes_without_param_warning(self):
        """run(PluginInfo) is the documented contract; must not warn about params."""
        source = """
DESCRIPTION = "Follows the OWTF plugin contract"

def run(PluginInfo):
    return {"target": PluginInfo["target_url"]}
"""
        result = validate(source)
        assert result.passed, str(result)
        assert not any("no parameters" in w for w in result.warnings)

    def test_run_with_zero_args_warning_mentions_plugininfo(self):
        source = """
DESCRIPTION = "Missing plugin arg"

def run():
    return {}
"""
        result = validate(source)
        assert result.passed, str(result)
        assert any("PluginInfo" in w for w in result.warnings)


class TestAliasBypass:
    def test_aliased_subprocess_run_with_shell_true_blocked(self):
        source = """
from subprocess import run as process
DESCRIPTION = "aliased shell injection"
def run(PluginInfo):
    process("id", shell=True)
"""
        result = validate(source)
        assert not result.passed
        assert any("shell=True" in v for v in result.violations)

    def test_aliased_subprocess_module_with_shell_true_blocked(self):
        source = """
import subprocess as sp
DESCRIPTION = "aliased module shell injection"
def run(PluginInfo):
    sp.run("id", shell=True)
"""
        result = validate(source)
        assert not result.passed
        assert any("shell=True" in v for v in result.violations)

    def test_from_subprocess_import_run_without_shell_is_allowed(self):
        source = """
from subprocess import run
DESCRIPTION = "safe subprocess"
def run_wrapper():
    run(["ls"])
def run(PluginInfo):
    run_wrapper()
"""
        result = validate(source)
        assert result.passed, str(result)

    def test_local_name_alias_of_subprocess_run_with_shell_true_blocked(self):
        """`x = subprocess.run; x("id", shell=True)` must be caught same as a direct call."""
        source = """
import subprocess
DESCRIPTION = "aliased local name"
def run(PluginInfo):
    x = subprocess.run
    x("id", shell=True)
"""
        result = validate(source)
        assert not result.passed
        assert any("shell" in v.lower() for v in result.violations)

    def test_shell_arg_via_variable_blocked(self):
        """shell=<variable> must be flagged; only literal shell=False is accepted."""
        source = """
import subprocess
DESCRIPTION = "variable shell arg"
def run(PluginInfo):
    flag = True
    subprocess.run("id", shell=flag)
"""
        result = validate(source)
        assert not result.passed
        assert any("shell" in v.lower() for v in result.violations)

    def test_explicit_shell_false_is_allowed(self):
        """The one shell= value we do accept is literal False."""
        source = """
import subprocess
DESCRIPTION = "explicit shell=False"
def run(PluginInfo):
    subprocess.run(["ls"], shell=False)
    return {}
"""
        result = validate(source)
        assert result.passed, str(result)


class TestModuleContract:
    def test_nested_run_does_not_satisfy_contract(self):
        source = """
DESCRIPTION = "nested run should not count"
def wrapper():
    def run(PluginInfo):
        return {}
"""
        result = validate(source)
        assert not result.passed
        assert any("run(PluginInfo)" in v for v in result.violations)

    def test_description_must_be_string_literal(self):
        source = """
DESCRIPTION = 42
def run(PluginInfo):
    return {}
"""
        result = validate(source)
        assert not result.passed
        assert any("DESCRIPTION" in v and "string" in v for v in result.violations)

    def test_description_from_expression_rejected(self):
        source = """
DESCRIPTION = "a" + "b"
def run(PluginInfo):
    return {}
"""
        result = validate(source)
        assert not result.passed

    def test_nested_description_does_not_satisfy_contract(self):
        source = """
def wrapper():
    DESCRIPTION = "nested"
def run(PluginInfo):
    return {}
"""
        result = validate(source)
        assert not result.passed
        assert any("DESCRIPTION" in v for v in result.violations)


class TestAsyncFunctions:
    def test_async_function_blocked(self):
        source = """
DESCRIPTION = "Async plugin"
async def run(PluginInfo):
    return {}
"""
        result = validate(source)
        assert not result.passed
        assert any("async" in v.lower() for v in result.violations)


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


class TestValidateBytes:
    def test_valid_bytes_passes(self):
        result = PluginValidator.validate_bytes(VALID_PLUGIN.encode("utf-8"))
        assert result.passed, str(result)

    def test_invalid_bytes_fails(self):
        source = b"import os\nDESCRIPTION='x'\ndef run(t): os.system('id')"
        result = PluginValidator.validate_bytes(source)
        assert not result.passed
