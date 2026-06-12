#!/usr/bin/env python3
"""
Type Hint Validator.

Validates that all functions in a Python file have complete type hints
as required by the Python Coding Standards skill.

Usage:
    python type_validator.py <filename>
    python type_validator.py <filename> --json       # Output as JSON
    python type_validator.py <filename> --strict     # Also check variables
"""

from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Any, Optional

# --- Data Classes ------------------------------------------------------------


@dataclass
class TypeViolation:
    """Represents a single type hint violation."""

    line: int
    function_name: str
    issue: str
    severity: str = "error"  # "error" or "warning"

    def __str__(self) -> str:
        prefix = "ERROR" if self.severity == "error" else "WARNING"
        return (
            f"  line {self.line} [{prefix}] "
            f"'{self.function_name}': {self.issue}"
        )


@dataclass
class TypeCheckResult:
    """Result of running type validation on a file."""

    filepath: str
    violations: list[TypeViolation] = field(default_factory=list)

    @property
    def errors(self) -> list[TypeViolation]:
        """Return only error-level violations."""
        return [v for v in self.violations if v.severity == "error"]

    @property
    def warnings(self) -> list[TypeViolation]:
        """Return only warning-level violations."""
        return [v for v in self.violations if v.severity == "warning"]

    @property
    def is_clean(self) -> bool:
        """Return True if no violations were found."""
        return len(self.violations) == 0

    @property
    def count(self) -> int:
        """Return the total number of violations."""
        return len(self.violations)


# --- Validator Class ---------------------------------------------------------


class TypeValidator:
    """
    Validates type hints in Python functions.

    Checks that:
    - All function parameters have type annotations
    - All functions have return type annotations
    - Return type is explicit (not missing)
    """

    # Methods that are exempt from type checking
    EXEMPT_METHODS: frozenset[str] = frozenset({
        "__init_subclass__",
        "__class_getitem__",
    })

    def __init__(self, filepath: str) -> None:
        self.filepath: str = filepath
        self.result: TypeCheckResult = TypeCheckResult(filepath=filepath)

    def validate(self) -> TypeCheckResult:
        """Run type validation and return the result."""
        if not os.path.exists(self.filepath):
            raise FileNotFoundError(f"File not found: {self.filepath}")

        with open(self.filepath, "r", encoding="utf-8") as f:
            source = f.read()

        tree = self._parse_ast(source)
        if tree is None:
            self.result.violations.append(
                TypeViolation(
                    line=0,
                    function_name="<file>",
                    issue="Cannot parse file — syntax error.",
                    severity="error",
                )
            )
            return self.result

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._check_function(node, tree)

        self.result.violations.sort(key=lambda v: v.line)
        return self.result

    def _check_function(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef, tree: ast.AST
    ) -> None:
        """Check a single function definition for type hints."""
        func_name: str = node.name

        # Skip exempt methods
        if func_name in self.EXEMPT_METHODS:
            return

        # Skip special methods that have well-known signatures
        if self._is_well_known_dunder(func_name):
            return

        # Determine full name for class methods
        full_name = self._get_full_name(node, tree)

        # Check if the function has a docstring (warning, not error)
        if ast.get_docstring(node) is None and not func_name.startswith("_"):
            # Functions with decorators like @property may not need docstrings
            if not self._has_property_decorator(node):
                self.result.violations.append(
                    TypeViolation(
                        line=node.lineno,
                        function_name=full_name,
                        issue="Missing docstring.",
                        severity="warning",
                    )
                )

        # --- Parameter Type Annotations ---
        args = node.args

        # Check all positional arguments (excluding self/cls)
        all_args: list[ast.arg] = []
        all_args.extend(args.args)
        all_args.extend(args.posonlyargs)
        all_args.extend(args.kwonlyargs)

        for arg in all_args:
            arg_name: str = arg.arg

            # Skip 'self' and 'cls' (conventionally typed implicitly)
            if arg_name in ("self", "cls"):
                continue

            if arg.annotation is None:
                self.result.violations.append(
                    TypeViolation(
                        line=arg.lineno,
                        function_name=full_name,
                        issue=f"Parameter '{arg_name}' is missing a type annotation.",
                        severity="error",
                    )
                )
            elif isinstance(arg.annotation, ast.Name) and arg.annotation.id == "Any":
                self.result.violations.append(
                    TypeViolation(
                        line=arg.lineno,
                        function_name=full_name,
                        issue=(
                            f"Parameter '{arg_name}' uses 'Any' — "
                            "consider using a more specific type."
                        ),
                        severity="warning",
                    )
                )

        # Check *args
        if args.vararg is not None:
            if args.vararg.annotation is None:
                self.result.violations.append(
                    TypeViolation(
                        line=args.vararg.lineno,
                        function_name=full_name,
                        issue=f"*args parameter '{args.vararg.arg}' "
                        "is missing a type annotation.",
                        severity="error",
                    )
                )

        # Check **kwargs
        if args.kwarg is not None:
            if args.kwarg.annotation is None:
                self.result.violations.append(
                    TypeViolation(
                        line=args.kwarg.lineno,
                        function_name=full_name,
                        issue=f"**kwargs parameter '{args.kwarg.arg}' "
                        "is missing a type annotation.",
                        severity="error",
                    )
                )

        # --- Return Type Annotations ---
        if node.returns is None:
            self.result.violations.append(
                TypeViolation(
                    line=node.lineno,
                    function_name=full_name,
                    issue="Missing return type annotation. Use '-> None' "
                    "if the function returns nothing.",
                    severity="error",
                )
            )
        elif (
            isinstance(node.returns, ast.Name)
            and node.returns.id == "Any"
        ):
            self.result.violations.append(
                TypeViolation(
                    line=node.lineno,
                    function_name=full_name,
                    issue="Return type is 'Any' — consider using "
                    "a more specific type.",
                    severity="warning",
                )
            )

    def _is_well_known_dunder(self, name: str) -> bool:
        """Check if this is a well-known dunder method with conventional types."""
        well_known: frozenset[str] = frozenset({
            "__init__",
            "__new__",
            "__del__",
            "__repr__",
            "__str__",
            "__bytes__",
            "__format__",
            "__lt__",
            "__le__",
            "__eq__",
            "__ne__",
            "__gt__",
            "__ge__",
            "__hash__",
            "__bool__",
            "__getattr__",
            "__setattr__",
            "__delattr__",
            "__dir__",
            "__getitem__",
            "__setitem__",
            "__delitem__",
            "__len__",
            "__iter__",
            "__next__",
            "__contains__",
            "__add__",
            "__sub__",
            "__mul__",
            "__truediv__",
            "__floordiv__",
            "__mod__",
            "__pow__",
            "__enter__",
            "__exit__",
            "__aenter__",
            "__aexit__",
            "__await__",
            "__aiter__",
            "__anext__",
            "__call__",
            "__copy__",
            "__deepcopy__",
            "__getstate__",
            "__setstate__",
            "__reduce__",
            "__fspath__",
        })
        return name in well_known

    def _has_property_decorator(self, node: ast.FunctionDef) -> bool:
        """Check if the function has a @property or related decorator."""
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name) and decorator.id in (
                "property",
                "cached_property",
            ):
                return True
        return False

    def _get_full_name(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef, tree: ast.AST
    ) -> str:
        """Get the full qualified name including class if applicable."""
        for parent in ast.walk(tree):
            if isinstance(parent, ast.ClassDef):
                for child in ast.iter_child_nodes(parent):
                    if child is node:
                        return f"{parent.name}.{node.name}"
        return node.name

    def _parse_ast(self, source: str) -> Optional[ast.AST]:
        """Safely parse source code into an AST."""
        try:
            return ast.parse(source, filename=self.filepath)
        except SyntaxError:
            return None


# --- Mypy Integration --------------------------------------------------------


def run_mypy(filepath: str) -> list[str]:
    """
    Run mypy as an external type checker.

    Args:
        filepath: Path to the Python file.

    Returns:
        List of mypy output lines.
    """
    try:
        result = subprocess.run(
            ["mypy", "--strict", filepath],
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = result.stdout.strip() + result.stderr.strip()
        if output:
            return output.split("\n")
        return []
    except FileNotFoundError:
        return ["[INFO] mypy is not installed — skipping external type check."]
    except subprocess.TimeoutExpired:
        return ["[WARNING] mypy timed out."]


# --- Output Helpers ----------------------------------------------------------


def print_result(
    result: TypeCheckResult, mypy_output: Optional[list[str]] = None
) -> None:
    """Print validation results to stdout."""
    filename = os.path.basename(result.filepath)

    if result.is_clean and not mypy_output:
        print(f"✓ {filename}: All type hints present.")
        return

    print(f"\n{'=' * 60}")
    print(f"Type Validation: {result.filepath}")
    print(f"{'=' * 60}")

    if result.violations:
        print(f"Found {result.count} violation(s):\n")
        for v in result.violations:
            print(str(v))
        print()

    if mypy_output:
        print("─" * 60)
        print("Mypy external check:")
        print("─" * 60)
        for line in mypy_output:
            print(f"  {line}")

    errors = result.errors
    if errors:
        print(f"\n{'=' * 60}")
        print(f"Total: {len(errors)} error(s), {len(result.warnings)} warning(s)")
        print(f"File: {filename}\n")


def print_json_result(
    result: TypeCheckResult, mypy_output: Optional[list[str]] = None
) -> None:
    """Print validation results as JSON."""
    output: dict[str, Any] = {
        "filepath": result.filepath,
        "violations": [
            {
                "line": v.line,
                "function_name": v.function_name,
                "issue": v.issue,
                "severity": v.severity,
            }
            for v in result.violations
        ],
        "count": result.count,
        "is_clean": result.is_clean,
        "mypy_output": mypy_output or [],
    }
    print(json.dumps(output, indent=2))


# --- Main -------------------------------------------------------------------


def main() -> None:
    """Run type validation from the command line."""
    if len(sys.argv) < 2:
        print("Usage: python type_validator.py <filename> [--json] [--mypy]")
        sys.exit(1)

    filepath: str = sys.argv[1]
    use_json: bool = "--json" in sys.argv
    use_mypy: bool = "--mypy" in sys.argv

    try:
        validator = TypeValidator(filepath)
        result = validator.validate()

        mypy_output: Optional[list[str]] = None
        if use_mypy:
            mypy_output = run_mypy(filepath)

        if use_json:
            print_json_result(result, mypy_output)
        else:
            print_result(result, mypy_output)

        sys.exit(0 if result.is_clean else 1)

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(3)


if __name__ == "__main__":
    main()
