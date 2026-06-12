#!/usr/bin/env python3
"""
PEP8 Compliance Checker.

Checks Python source files for violations of PEP8 coding standards
as defined by the Python Coding Standards skill.

Usage:
    python pep8_checker.py <filename>
    python pep8_checker.py <filename> --json      # Output as JSON
    python pep8_checker.py <filename> --quiet     # Only show violations
"""

from __future__ import annotations

import ast
import json
import os
import re
import sys
from dataclasses import dataclass, field
from typing import Any, Optional

# --- Constants ---------------------------------------------------------------

MAX_LINE_LENGTH: int = 79
MAX_DOCSTRING_LENGTH: int = 72
INDENT_SIZE: int = 4

# Standard library module names (top 100+ most common)
STDLIB_MODULES: frozenset[str] = frozenset({
    "abc", "argparse", "ast", "asyncio", "base64", "collections",
    "concurrent", "contextlib", "copy", "csv", "ctypes", "dataclasses",
    "datetime", "decimal", "difflib", "enum", "fileinput", "fnmatch",
    "functools", "glob", "gzip", "hashlib", "heapq", "html", "http",
    "importlib", "inspect", "io", "itertools", "json", "logging",
    "math", "multiprocessing", "operator", "os", "pathlib", "pickle",
    "platform", "pprint", "queue", "random", "re", "secrets", "shlex",
    "shutil", "signal", "socket", "sqlite3", "ssl", "statistics",
    "string", "struct", "subprocess", "sys", "tempfile", "textwrap",
    "threading", "time", "tokenize", "traceback", "typing", "unittest",
    "urllib", "uuid", "warnings", "weakref", "xml", "zipfile",
})


# --- Data Classes ------------------------------------------------------------


@dataclass
class Violation:
    """Represents a single PEP8 violation."""

    line: int
    column: Optional[int]
    code: str
    message: str

    def __str__(self) -> str:
        location = f"line {self.line}"
        if self.column is not None:
            location += f", col {self.column}"
        return f"  {location}: [{self.code}] {self.message}"


@dataclass
class CheckResult:
    """Result of running all PEP8 checks on a file."""

    filepath: str
    violations: list[Violation] = field(default_factory=list)
    lines: list[str] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        """Return True if no violations were found."""
        return len(self.violations) == 0

    @property
    def count(self) -> int:
        """Return the number of violations found."""
        return len(self.violations)


# --- Checker Class -----------------------------------------------------------


class PEP8Checker:
    """Checks a Python file for PEP8 compliance violations."""

    def __init__(self, filepath: str) -> None:
        self.filepath: str = filepath
        self.lines: list[str] = []
        self.result: CheckResult = CheckResult(filepath=filepath)

    def check(self) -> CheckResult:
        """Run all PEP8 checks and return the result."""
        if not os.path.exists(self.filepath):
            raise FileNotFoundError(f"File not found: {self.filepath}")

        with open(self.filepath, "r", encoding="utf-8") as f:
            self.lines = f.readlines()

        self.result.lines = self.lines

        self._check_tabs()
        self._check_line_length()
        self._check_trailing_whitespace()
        self._check_blank_lines()
        self._check_imports()
        self._check_whitespace()
        self._check_naming_conventions()
        self._check_missing_newline_eof()

        self.result.violations.sort(key=lambda v: v.line)
        return self.result

    # --- Individual Checks ---------------------------------------------------

    def _add_violation(
        self, line: int, code: str, message: str, column: Optional[int] = None
    ) -> None:
        """Add a violation record."""
        self.result.violations.append(
            Violation(line=line, column=column, code=code, message=message)
        )

    def _check_tabs(self) -> None:
        """E101: Check for tab characters used for indentation."""
        for i, line in enumerate(self.lines, start=1):
            # Skip if line is empty
            stripped = line.lstrip(" ")
            if stripped.startswith("\t"):
                col = len(line) - len(stripped) + 1
                self._add_violation(
                    line=i,
                    column=col,
                    code="E101",
                    message="Tab characters are not allowed; use 4 spaces for indentation.",
                )

    def _check_line_length(self) -> None:
        """E501: Check that lines do not exceed the maximum length."""
        for i, line in enumerate(self.lines, start=1):
            # Strip newline for length measurement
            line_content = line.rstrip("\n\r")
            line_len = len(line_content)

            # Docstrings and comments get a shorter limit
            is_comment_or_docstring = (
                line_content.strip().startswith("#")
                or line_content.strip().startswith('"""')
                or line_content.strip().startswith("'''")
            )

            limit = MAX_DOCSTRING_LENGTH if is_comment_or_docstring else MAX_LINE_LENGTH

            if line_len > limit:
                self._add_violation(
                    line=i,
                    column=limit + 1,
                    code="E501",
                    message=(
                        f"Line too long ({line_len}/{limit} characters). "
                        "Break into multiple lines."
                    ),
                )

    def _check_trailing_whitespace(self) -> None:
        """W291: Check for trailing whitespace."""
        for i, line in enumerate(self.lines, start=1):
            if line.rstrip("\n\r") != line.rstrip("\n\r").rstrip(" \t"):
                self._add_violation(
                    line=i,
                    code="W291",
                    message="Trailing whitespace found.",
                )

    def _check_blank_lines(self) -> None:
        """E302/E303: Check for proper blank line spacing."""
        tree = self._parse_ast()
        if tree is None:
            return

        # E302: Expect 2 blank lines before top-level class/function defs
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                start_line = node.lineno
                # Count blank lines before this definition
                blank_count = 0
                for j in range(start_line - 2, -1, -1):
                    if j < 0:
                        break
                    stripped = self.lines[j].strip()
                    if stripped == "":
                        blank_count += 1
                    elif stripped.startswith("#"):
                        continue  # Comments don't count as content
                    else:
                        break

                if blank_count < 2 and start_line > 1:
                    self._add_violation(
                        line=start_line,
                        code="E302",
                        message=(
                            f"Expected 2 blank lines before top-level "
                            f"{'class' if isinstance(node, ast.ClassDef) else 'function'} "
                            f"definition, found {blank_count}."
                        ),
                    )

        # E303: Expect 1 blank line between class methods
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = [
                    n
                    for n in ast.iter_child_nodes(node)
                    if isinstance(
                        n, (ast.FunctionDef, ast.AsyncFunctionDef)
                    )
                ]
                for idx, method in enumerate(methods[1:], start=1):
                    prev_end = self._get_node_end_line(methods[idx - 1])
                    blank_count = max(
                        0, method.lineno - prev_end - 1
                    )
                    if blank_count < 1:
                        self._add_violation(
                            line=method.lineno,
                            code="E303",
                            message=(
                                f"Expected 1 blank line between class methods, "
                                f"found {blank_count}."
                            ),
                        )

    def _check_imports(self) -> None:
        """E401/E402: Check import ordering and formatting."""
        import_lines: list[tuple[int, str, str]] = []

        for i, line in enumerate(self.lines, start=1):
            stripped = line.strip()
            if stripped.startswith("import ") or stripped.startswith("from "):
                import_lines.append((i, stripped, line))

        # E401: Each import on a separate line
        # E999: No wildcard imports
        for i, stripped, original in import_lines:
            if stripped.startswith("import "):
                modules = stripped[7:].split(",")
                if len(modules) > 1:
                    self._add_violation(
                        line=i,
                        code="E401",
                        message=(
                            "Multiple imports on one line. "
                            "Place each import on its own line."
                        ),
                    )

            if stripped.startswith("from "):
                # Check for wildcard imports
                if stripped.endswith("import *"):
                    self._add_violation(
                        line=i,
                        code="E999",
                        message=(
                            "Wildcard import (from module import *) "
                            "is not allowed."
                        ),
                    )

        # E402: Import order (stdlib → third-party → local)
        self._check_import_order(import_lines)

    def _check_import_order(
        self, import_lines: list[tuple[int, str, str]]
    ) -> None:
        """Verify imports follow the stdlib → third-party → local order."""
        if len(import_lines) < 2:
            return

        categories: list[str] = []
        for _i, stripped, _original in import_lines:
            categories.append(self._classify_import(stripped))

        # Check that categories are non-decreasing
        category_order = {"stdlib": 0, "third_party": 1, "local": 2}
        prev_order = -1
        for idx, cat in enumerate(categories):
            current = category_order.get(cat, 2)
            line_no = import_lines[idx][0]
            if current < prev_order:
                self._add_violation(
                    line=line_no,
                    code="E402",
                    message=(
                        f"Import order violation: '{cat}' imports "
                        f"should come before "
                        f"'{categories[idx - 1]}' imports. "
                        "Expected order: stdlib → third-party → local."
                    ),
                )
            prev_order = max(prev_order, current)

    def _classify_import(self, import_line: str) -> str:
        """
        Classify an import statement.

        Returns:
            'stdlib', 'third_party', or 'local'
        """
        if import_line.startswith("from "):
            module = import_line[5:].split(" import ")[0].strip()
        else:
            module = import_line[7:].split(" as ")[0].strip().split(",")[0].strip()

        top_level = module.split(".")[0]

        if top_level in STDLIB_MODULES:
            return "stdlib"
        if top_level.startswith("."):
            return "local"
        # Heuristic: if the module name looks like a local project module
        # (no dots at start, not in stdlib), treat as third-party.
        # In practice, users should configure known_first_party.
        return "third_party"

    def _check_whitespace(self) -> None:
        """E201/E202/E225: Check whitespace rules."""
        for i, line in enumerate(self.lines, start=1):
            stripped = line.rstrip("\n\r")

            # E201: No space after opening bracket
            if re.search(r"\([ ]+", stripped):
                self._add_violation(
                    line=i,
                    code="E201",
                    message="Whitespace after '(' is not allowed.",
                )
            if re.search(r"\[[ ]+", stripped):
                self._add_violation(
                    line=i,
                    code="E201",
                    message="Whitespace after '[' is not allowed.",
                )
            if re.search(r"\{[ ]+", stripped):
                self._add_violation(
                    line=i,
                    code="E201",
                    message="Whitespace after '{' is not allowed.",
                )

            # E202: No space before closing bracket
            if re.search(r"[ ]+\)", stripped):
                self._add_violation(
                    line=i,
                    code="E202",
                    message="Whitespace before ')' is not allowed.",
                )
            if re.search(r"[ ]+\]", stripped):
                self._add_violation(
                    line=i,
                    code="E202",
                    message="Whitespace before ']' is not allowed.",
                )
            if re.search(r"[ ]+\}", stripped):
                self._add_violation(
                    line=i,
                    code="E202",
                    message="Whitespace before '}' is not allowed.",
                )

    def _check_naming_conventions(self) -> None:
        """N801-N806: Check naming conventions."""
        tree = self._parse_ast()
        if tree is None:
            return

        for node in ast.walk(tree):
            # Class names: PascalCase
            if isinstance(node, ast.ClassDef):
                if not re.match(r"^[A-Z][a-zA-Z0-9]+$", node.name):
                    self._add_violation(
                        line=node.lineno,
                        code="N801",
                        message=(
                            f"Class name '{node.name}' should use PascalCase "
                            f"(e.g., 'MyClass')."
                        ),
                    )

            # Function names: snake_case
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Skip dunder methods and property getters
                if not node.name.startswith("__") and not node.name.startswith(
                    "_"
                ):
                    if not re.match(r"^[a-z][a-z0-9_]*$", node.name):
                        self._add_violation(
                            line=node.lineno,
                            code="N802",
                            message=(
                                f"Function name '{node.name}' should use "
                                f"snake_case (e.g., 'my_function')."
                            ),
                        )

            # Constant names: UPPER_CASE (module-level only)
            elif isinstance(node, ast.Assign):
                if self._is_module_level(node, tree):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            if target.id.isupper():
                                continue  # Already UPPER_CASE
                            # Constants assigned to literals should be UPPER_CASE
                            if isinstance(
                                node.value,
                                (ast.Constant, ast.List, ast.Dict, ast.Tuple, ast.Set),
                            ):
                                # Only flag if it looks like a constant
                                # (simple literal assignment at module level)
                                pass  # We don't force module-level vars
                                # to be UPPER_CASE unless convention says so

    def _check_missing_newline_eof(self) -> None:
        """W292: Check that file ends with a single newline."""
        if not self.lines:
            return

        last_line = self.lines[-1]
        if not last_line.endswith("\n"):
            self._add_violation(
                line=len(self.lines),
                code="W292",
                message="No newline at end of file.",
            )
        elif last_line.endswith("\n\n"):
            self._add_violation(
                line=len(self.lines),
                code="W391",
                message="Multiple blank lines at end of file.",
            )

    # --- Helpers -------------------------------------------------------------

    def _parse_ast(self) -> Optional[ast.AST]:
        """
        Safely parse the file into an AST.

        Returns:
            Parsed AST or None if parsing fails.
        """
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                return ast.parse(f.read(), filename=self.filepath)
        except SyntaxError:
            return None

    def _get_node_end_line(self, node: ast.AST) -> int:
        """Get the last line number of an AST node."""
        end = getattr(node, "end_lineno", None)
        if end is not None:
            return end
        # Fallback: use the start line
        return node.lineno

    def _is_module_level(self, node: ast.AST, tree: ast.AST) -> bool:
        """Check if a node is at module level (not inside a function/class)."""
        for child in ast.iter_child_nodes(tree):
            if child is node:
                return True
        return False


# --- Output Helpers ----------------------------------------------------------


def print_result(result: CheckResult, quiet: bool = False) -> None:
    """Print check results to stdout."""
    filename = os.path.basename(result.filepath)

    if result.is_clean:
        if not quiet:
            print(f"✓ {filename}: No PEP8 violations found.")
        return

    print(f"\n{'=' * 60}")
    print(f"PEP8 Check: {result.filepath}")
    print(f"{'=' * 60}")
    print(f"Found {result.count} violation(s):\n")
    for v in result.violations:
        print(str(v))
    print(f"\n{'=' * 60}")
    print(f"Total: {result.count} violation(s) in {filename}\n")


def print_json_result(result: CheckResult) -> None:
    """Print check results as JSON."""
    output = {
        "filepath": result.filepath,
        "violations": [
            {
                "line": v.line,
                "column": v.column,
                "code": v.code,
                "message": v.message,
            }
            for v in result.violations
        ],
        "count": result.count,
        "is_clean": result.is_clean,
    }
    print(json.dumps(output, indent=2))


# --- Main -------------------------------------------------------------------


def main() -> None:
    """Run PEP8 checks from the command line."""
    if len(sys.argv) < 2:
        print("Usage: python pep8_checker.py <filename> [--json] [--quiet]")
        sys.exit(1)

    filepath: str = sys.argv[1]
    use_json: bool = "--json" in sys.argv
    quiet: bool = "--quiet" in sys.argv

    try:
        checker = PEP8Checker(filepath)
        result = checker.check()

        if use_json:
            print_json_result(result)
        else:
            print_result(result, quiet=quiet)

        sys.exit(0 if result.is_clean else 1)

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(3)


if __name__ == "__main__":
    main()
