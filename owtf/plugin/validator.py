"""
owtf.plugin.validator
~~~~~~~~~~~~~~~~~~~~~

AST-based static analysis for community plugin uploads. Rejects obvious
misuse (dangerous imports, eval/exec, os.system, shell=True, write-mode
open) before the file is written to disk. Not a sandbox: admin review of
the source is the actual trust boundary. This just keeps the review
queue clean.

Every community plugin must declare a module-level ``DESCRIPTION``
string and a top-level ``run(PluginInfo)`` function, matching the
built-in OWTF plugin contract.
"""

import ast
from dataclasses import dataclass, field
from typing import List

BLOCKED_IMPORTS = frozenset(
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

BLOCKED_BUILTINS = frozenset(
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

BLOCKED_ATTR_CALLS = frozenset(
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

WRITE_MODES = frozenset({"w", "wb", "a", "ab", "x", "xb", "w+", "wb+", "a+", "ab+", "r+", "rb+"})

SUBPROCESS_SHELL_CALLS = frozenset(
    {
        "subprocess.Popen",
        "subprocess.run",
        "subprocess.call",
        "subprocess.check_call",
        "subprocess.check_output",
    }
)


@dataclass
class ValidationResult:
    passed: bool
    violations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def __str__(self):
        if self.passed:
            msg = "PASSED: No violations found."
            if self.warnings:
                msg += "\nWarnings:\n" + "\n".join("  - " + w for w in self.warnings)
            return msg
        lines = ["FAILED:"] + ["  - " + v for v in self.violations]
        if self.warnings:
            lines += ["Warnings:"] + ["  - " + w for w in self.warnings]
        return "\n".join(lines)


def _check_module_contract(tree):
    """Enforce top-level DESCRIPTION string and top-level run() entry point."""
    violations = []
    warnings = []
    has_description = False
    has_run = False

    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if not (isinstance(target, ast.Name) and target.id == "DESCRIPTION"):
                    continue
                if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                    has_description = True
                else:
                    violations.append("Line {}: DESCRIPTION must be a string literal".format(node.lineno))
        elif isinstance(node, ast.FunctionDef) and node.name == "run":
            has_run = True
            args = node.args
            if len(args.args) + len(args.posonlyargs) == 0:
                warnings.append(
                    "Line {}: function 'run' has no parameters. Community plugins "
                    "should accept 'PluginInfo' (the OWTF plugin dict).".format(node.lineno)
                )

    if not has_description:
        violations.append("Missing required module-level string constant: DESCRIPTION")
    if not has_run:
        violations.append(
            "Missing required top-level function: run(PluginInfo). "
            "This is the plugin entry point and must accept the OWTF plugin dict."
        )
    return violations, warnings


class _SecurityVisitor(ast.NodeVisitor):
    def __init__(self, filename="<unknown>"):
        self.filename = filename
        self.violations = []
        self.warnings = []
        # local name -> dotted origin, e.g. "sp" -> "subprocess",
        # "process" -> "subprocess.run".
        self.aliases = {}

    def visit_Import(self, node):
        for alias in node.names:
            local = alias.asname or alias.name.split(".")[0]
            self.aliases[local] = alias.name
            root = alias.name.split(".")[0]
            if root in BLOCKED_IMPORTS:
                self.violations.append("Line {}: blocked import '{}'".format(node.lineno, alias.name))
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        module = node.module or ""
        root = module.split(".")[0]
        if root in BLOCKED_IMPORTS:
            self.violations.append("Line {}: blocked import 'from {} import ...'".format(node.lineno, module))
        for alias in node.names:
            local = alias.asname or alias.name
            self.aliases[local] = "{}.{}".format(module, alias.name) if module else alias.name
        self.generic_visit(node)

    def _resolve(self, func):
        """Return the dotted origin for a Call.func node, following import aliases."""
        if isinstance(func, ast.Name):
            return self.aliases.get(func.id, func.id)
        if isinstance(func, ast.Attribute):
            parts = [func.attr]
            cur = func.value
            while isinstance(cur, ast.Attribute):
                parts.append(cur.attr)
                cur = cur.value
            if isinstance(cur, ast.Name):
                parts.append(self.aliases.get(cur.id, cur.id))
                return ".".join(reversed(parts))
        return None

    def visit_Call(self, node):
        func = node.func
        qualified = self._resolve(func)

        if isinstance(func, ast.Name) and func.id in BLOCKED_BUILTINS:
            self.violations.append("Line {}: blocked built-in call '{}()'".format(node.lineno, func.id))

        if qualified in BLOCKED_ATTR_CALLS:
            self.violations.append("Line {}: blocked call '{}()'".format(node.lineno, qualified))

        if qualified in SUBPROCESS_SHELL_CALLS:
            for kw in node.keywords:
                if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                    self.violations.append(
                        "Line {}: subprocess called with shell=True (use a list of args)".format(node.lineno)
                    )

        if isinstance(func, ast.Name) and func.id == "open":
            self._check_open_mode(node)

        self.generic_visit(node)

    def _check_open_mode(self, node):
        for kw in node.keywords:
            if kw.arg == "mode" and isinstance(kw.value, ast.Constant) and kw.value.value in WRITE_MODES:
                self.violations.append(
                    "Line {}: open() called with write/append mode '{}' (read-only access permitted)".format(
                        node.lineno, kw.value.value
                    )
                )
        if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant) and node.args[1].value in WRITE_MODES:
            self.violations.append(
                "Line {}: open() called with write/append mode '{}' (read-only access permitted)".format(
                    node.lineno, node.args[1].value
                )
            )

    def visit_AsyncFunctionDef(self, node):
        self.violations.append("Line {}: async functions are not permitted in community plugins".format(node.lineno))
        self.generic_visit(node)

    def visit_While(self, node):
        if isinstance(node.test, ast.Constant) and node.test.value is True:
            self.warnings.append(
                "Line {}: unconditional while True loop detected; ensure plugin has a break condition".format(
                    node.lineno
                )
            )
        self.generic_visit(node)


class PluginValidator:
    """Validate a community plugin's source without executing it."""

    @staticmethod
    def validate_source(source, filename="<unknown>"):
        try:
            tree = ast.parse(source, filename=filename)
        except SyntaxError as exc:
            return ValidationResult(
                passed=False,
                violations=["SyntaxError at line {}: {}".format(exc.lineno, exc.msg)],
            )

        contract_violations, contract_warnings = _check_module_contract(tree)

        visitor = _SecurityVisitor(filename=filename)
        visitor.visit(tree)

        violations = contract_violations + visitor.violations
        warnings = contract_warnings + visitor.warnings
        return ValidationResult(passed=not violations, violations=violations, warnings=warnings)

    @staticmethod
    def validate_file(path):
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                source = fh.read()
        except OSError as exc:
            return ValidationResult(passed=False, violations=["Cannot read file: {}".format(exc)])
        return PluginValidator.validate_source(source, filename=path)

    @staticmethod
    def validate_bytes(data, filename="<upload>"):
        try:
            source = data.decode("utf-8", errors="replace")
        except Exception as exc:
            return ValidationResult(passed=False, violations=["Cannot decode plugin bytes: {}".format(exc)])
        return PluginValidator.validate_source(source, filename=filename)
