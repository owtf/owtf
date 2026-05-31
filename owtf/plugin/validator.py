"""
owtf.plugin.validator
~~~~~~~~~~~~~~~~~~~~~

AST-based static analysis for community plugin uploads.

Security model
--------------
Community plugins run in an isolated subprocess (SandboxRunner), but we still
want to reject obviously malicious code *before* it touches disk.  This module
performs a best-effort static analysis; it is NOT a sandbox and cannot catch
every possible attack, but it raises the bar significantly.

Rules
-----
Blocked imports
  os, sys, socket, importlib, shutil, ctypes, multiprocessing, threading,
  signal, resource, pickle, shelve, marshal, pty, termios, tty, fcntl

Blocked built-in calls
  eval, exec, compile, __import__, execfile

Blocked attribute calls
  os.system, os.popen, os.exec*, os.fork, os.kill, os.remove, os.unlink,
  os.rmdir, os.chmod, os.chown, socket.socket, subprocess.Popen with shell=True

Blocked write-mode open()
  open(path, "w"), open(path, "wb"), etc.

Required structure
  - A module-level string constant DESCRIPTION
  - A top-level function named run(target_url)
"""

import ast
from dataclasses import dataclass, field
from typing import List

# ---------------------------------------------------------------------------
# Configuration: what is blocked / required
# ---------------------------------------------------------------------------

BLOCKED_IMPORTS: frozenset = frozenset(
    {
        "os",
        "sys",
        "socket",
        "importlib",
        "shutil",
        "ctypes",
        "multiprocessing",
        "threading",
        "signal",
        "resource",
        "pickle",
        "shelve",
        "marshal",
        "pty",
        "termios",
        "tty",
        "fcntl",
        "builtins",
        "gc",
        "inspect",
        "_thread",
        "code",
        "codeop",
    }
)

BLOCKED_BUILTINS: frozenset = frozenset(
    {
        "eval",
        "exec",
        "compile",
        "__import__",
        "execfile",
        "input",
        "breakpoint",
    }
)

BLOCKED_ATTR_CALLS: frozenset = frozenset(
    {
        "os.system",
        "os.popen",
        "os.execv",
        "os.execve",
        "os.execvp",
        "os.execvpe",
        "os.exec",
        "os.fork",
        "os.forkpty",
        "os.kill",
        "os.killpg",
        "os.remove",
        "os.unlink",
        "os.rmdir",
        "os.removedirs",
        "os.chmod",
        "os.chown",
        "os.chroot",
        "os.setuid",
        "os.setgid",
        "socket.socket",
        "socket.create_connection",
        "socket.create_server",
    }
)

# open() mode arguments that imply file creation / modification
WRITE_MODES: frozenset = frozenset({"w", "wb", "a", "ab", "x", "xb", "w+", "wb+", "a+", "ab+", "r+", "rb+"})


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------


@dataclass
class ValidationResult:
    passed: bool
    violations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        if self.passed:
            msg = "PASSED: No violations found."
            if self.warnings:
                msg += "\nWarnings:\n" + "\n".join("  - " + w for w in self.warnings)
            return msg
        lines = ["FAILED:"] + ["  - " + v for v in self.violations]
        if self.warnings:
            lines += ["Warnings:"] + ["  - " + w for w in self.warnings]
        return "\n".join(lines)

    def as_dict(self) -> dict:
        return {
            "passed": self.passed,
            "violations": self.violations,
            "warnings": self.warnings,
        }


# ---------------------------------------------------------------------------
# Visitor
# ---------------------------------------------------------------------------


class _SecurityVisitor(ast.NodeVisitor):
    """Single-pass AST visitor that accumulates all violations."""

    def __init__(self, filename: str = "<unknown>"):
        self.filename = filename
        self.violations: List[str] = []
        self.warnings: List[str] = []
        self._has_run_func = False
        self._has_description = False

    # ------------------------------------------------------------------
    # Import checking
    # ------------------------------------------------------------------

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            root = alias.name.split(".")[0]
            if root in BLOCKED_IMPORTS:
                self.violations.append("Line {}: blocked import '{}'".format(node.lineno, alias.name))
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        root = module.split(".")[0]
        if root in BLOCKED_IMPORTS:
            self.violations.append("Line {}: blocked import 'from {} import ...'".format(node.lineno, module))
        self.generic_visit(node)

    # ------------------------------------------------------------------
    # Call checking
    # ------------------------------------------------------------------

    def visit_Call(self, node: ast.Call) -> None:
        func = node.func

        # --- Blocked built-ins: eval(...), exec(...) ---
        if isinstance(func, ast.Name) and func.id in BLOCKED_BUILTINS:
            self.violations.append("Line {}: blocked built-in call '{}()'".format(node.lineno, func.id))

        # --- Blocked attribute calls: os.system(...) etc. ---
        elif isinstance(func, ast.Attribute):
            try:
                full = ast.unparse(func)
            except AttributeError:
                full = ""
            if full in BLOCKED_ATTR_CALLS:
                self.violations.append("Line {}: blocked call '{}()'".format(node.lineno, full))

            # subprocess.Popen / subprocess.run / subprocess.call with shell=True
            if func.attr in ("Popen", "run", "call", "check_call", "check_output"):
                for kw in node.keywords:
                    if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                        self.violations.append(
                            "Line {}: subprocess called with shell=True (forbidden — use a list of args)".format(
                                node.lineno
                            )
                        )

        # --- open() with write mode ---
        if isinstance(func, ast.Name) and func.id == "open":
            self._check_open_mode(node)

        self.generic_visit(node)

    def _check_open_mode(self, node: ast.Call) -> None:
        # Keyword: open(path, mode="w")
        for kw in node.keywords:
            if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                if kw.value.value in WRITE_MODES:
                    self.violations.append(
                        "Line {}: open() called with write/append mode '{}' (read-only access permitted)".format(
                            node.lineno, kw.value.value
                        )
                    )
        # Positional: open(path, "w")
        if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
            if node.args[1].value in WRITE_MODES:
                self.violations.append(
                    "Line {}: open() called with write/append mode '{}' (read-only access permitted)".format(
                        node.lineno, node.args[1].value
                    )
                )

    # ------------------------------------------------------------------
    # Structure checking (DESCRIPTION, run function)
    # ------------------------------------------------------------------

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "DESCRIPTION":
                self._has_description = True
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        if node.name == "run":
            self._has_run_func = True
            # Warn if run() has no parameters (should accept target_url)
            args = node.args
            total_args = len(args.args) + len(args.posonlyargs)
            if total_args == 0:
                self.warnings.append(
                    "Line {}: function 'run' has no parameters — community plugins should accept 'target_url'".format(
                        node.lineno
                    )
                )
        self.generic_visit(node)

    # Async functions are forbidden — too easy to hide async shellcode
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.violations.append("Line {}: async functions are not permitted in community plugins".format(node.lineno))
        self.generic_visit(node)

    # Detect class-based fork-bomb patterns or infinite loops (best-effort)
    def visit_While(self, node: ast.While) -> None:
        if isinstance(node.test, ast.Constant) and node.test.value is True:
            self.warnings.append(
                "Line {}: unconditional while True loop detected — ensure plugin has a break condition".format(
                    node.lineno
                )
            )
        self.generic_visit(node)

    def finalize(self) -> None:
        if not self._has_description:
            self.violations.append("Missing required module-level constant: DESCRIPTION (string)")
        if not self._has_run_func:
            self.violations.append("Missing required function: run(target_url) — this is the plugin entry point")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


class PluginValidator:
    """
    Validates a community plugin's source code via AST static analysis.

    Usage::

        result = PluginValidator.validate_source(source_code)
        if not result.passed:
            for v in result.violations:
                print(v)

        result = PluginValidator.validate_file("/path/to/plugin.py")
    """

    @staticmethod
    def validate_source(source: str, filename: str = "<unknown>") -> ValidationResult:
        """Parse and analyse *source* without executing it."""
        try:
            tree = ast.parse(source, filename=filename)
        except SyntaxError as exc:
            return ValidationResult(
                passed=False,
                violations=["SyntaxError at line {}: {}".format(exc.lineno, exc.msg)],
            )

        visitor = _SecurityVisitor(filename=filename)
        visitor.visit(tree)
        visitor.finalize()

        passed = len(visitor.violations) == 0
        return ValidationResult(
            passed=passed,
            violations=visitor.violations,
            warnings=visitor.warnings,
        )

    @staticmethod
    def validate_file(path: str) -> ValidationResult:
        """Read *path* from disk and validate it."""
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                source = fh.read()
        except OSError as exc:
            return ValidationResult(
                passed=False,
                violations=["Cannot read file: {}".format(exc)],
            )
        return PluginValidator.validate_source(source, filename=path)

    @staticmethod
    def validate_bytes(data: bytes, filename: str = "<upload>") -> ValidationResult:
        """Validate raw bytes (e.g. from an HTTP multipart upload)."""
        try:
            source = data.decode("utf-8", errors="replace")
        except Exception as exc:
            return ValidationResult(
                passed=False,
                violations=["Cannot decode plugin bytes: {}".format(exc)],
            )
        return PluginValidator.validate_source(source, filename=filename)
