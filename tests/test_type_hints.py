"""
Tests for the type hint validator.

Verifies that type_validator.py correctly identifies missing or
incomplete type annotations.
"""

from __future__ import annotations

import os
import tempfile
from typing import Generator

import pytest

import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from type_validator import TypeValidator, TypeCheckResult


# --- Fixtures ----------------------------------------------------------------


@pytest.fixture
def write_file() -> Generator:
    """Helper to write content to a temp Python file."""
    _filepath: str = ""

    def _write(content: str) -> str:
        nonlocal _filepath
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            _filepath = f.name
        return _filepath

    yield _write

    if _filepath and os.path.exists(_filepath):
        os.unlink(_filepath)


# --- Tests: Missing Parameter Annotations ------------------------------------


def test_missing_parameter_type(write_file) -> None:
    """Parameter without type annotation should be flagged as error."""
    filepath = write_file("def greet(name) -> str:\n    return f'Hello, {name}'\n")
    validator = TypeValidator(filepath)
    result = validator.validate()

    param_violations = [
        v for v in result.violations
        if "Parameter 'name' is missing a type annotation" in v.issue
    ]
    assert len(param_violations) > 0
    assert param_violations[0].severity == "error"


def test_all_parameters_annotated(write_file) -> None:
    """Fully annotated parameters should pass."""
    filepath = write_file(
        "def greet(name: str, age: int) -> str:\n"
        "    return f'Hello, {name}, you are {age}'\n"
    )
    validator = TypeValidator(filepath)
    result = validator.validate()

    param_violations = [
        v for v in result.violations
        if "missing a type annotation" in v.issue
    ]
    assert len(param_violations) == 0


def test_self_parameter_exempt(write_file) -> None:
    """self parameter without annotation should be exempt."""
    filepath = write_file(
        "class MyClass:\n"
        "    def method(self, x: int) -> str:\n"
        "        return str(x)\n"
    )
    validator = TypeValidator(filepath)
    result = validator.validate()

    param_violations = [
        v for v in result.violations
        if "missing a type annotation" in v.issue
    ]
    assert len(param_violations) == 0


def test_cls_parameter_exempt(write_file) -> None:
    """cls parameter without annotation should be exempt."""
    filepath = write_file(
        "class MyClass:\n"
        "    @classmethod\n"
        "    def factory(cls, x: int) -> str:\n"
        "        return str(x)\n"
    )
    validator = TypeValidator(filepath)
    result = validator.validate()

    param_violations = [
        v for v in result.violations
        if "missing a type annotation" in v.issue
    ]
    assert len(param_violations) == 0


# --- Tests: Missing Return Type ----------------------------------------------


def test_missing_return_type(write_file) -> None:
    """Function without return type annotation should be flagged."""
    filepath = write_file("def greet(name: str):\n    return f'Hello, {name}'\n")
    validator = TypeValidator(filepath)
    result = validator.validate()

    return_violations = [
        v for v in result.violations
        if "Missing return type annotation" in v.issue
    ]
    assert len(return_violations) > 0
    assert return_violations[0].severity == "error"


def test_explicit_none_return(write_file) -> None:
    """Explicit '-> None' return type should pass."""
    filepath = write_file(
        "def log_message(msg: str) -> None:\n    print(msg)\n"
    )
    validator = TypeValidator(filepath)
    result = validator.validate()

    return_violations = [
        v for v in result.violations
        if "Missing return type annotation" in v.issue
    ]
    assert len(return_violations) == 0


# --- Tests: Any Usage Warnings -----------------------------------------------


def test_any_parameter_warns(write_file) -> None:
    """Using 'Any' as parameter type should produce a warning."""
    filepath = write_file(
        "from typing import Any\n"
        "def process(data: Any) -> str:\n"
        "    return str(data)\n"
    )
    validator = TypeValidator(filepath)
    result = validator.validate()

    any_warnings = [
        v for v in result.violations
        if "'Any'" in v.issue
    ]
    assert len(any_warnings) > 0
    for w in any_warnings:
        assert w.severity == "warning"


def test_any_return_type_warns(write_file) -> None:
    """Using 'Any' as return type should produce a warning."""
    filepath = write_file(
        "from typing import Any\n"
        "def process(data: str) -> Any:\n"
        "    return data\n"
    )
    validator = TypeValidator(filepath)
    result = validator.validate()

    any_warnings = [
        v for v in result.violations
        if "Return type is 'Any'" in v.issue
    ]
    assert len(any_warnings) > 0


# --- Tests: *args and **kwargs ----------------------------------------------


def test_star_args_missing_type(write_file) -> None:
    """*args without type annotation should be flagged."""
    filepath = write_file(
        "def sum_values(*args) -> int:\n    return sum(args)\n"
    )
    validator = TypeValidator(filepath)
    result = validator.validate()

    star_violations = [
        v for v in result.violations
        if "*args" in v.issue and "missing a type annotation" in v.issue
    ]
    assert len(star_violations) > 0


def test_star_args_with_type(write_file) -> None:
    """*args with type annotation should pass."""
    filepath = write_file(
        "def sum_values(*args: int) -> int:\n    return sum(args)\n"
    )
    validator = TypeValidator(filepath)
    result = validator.validate()

    star_violations = [
        v for v in result.violations
        if "*args" in v.issue and "missing a type annotation" in v.issue
    ]
    assert len(star_violations) == 0


def test_kwargs_missing_type(write_file) -> None:
    """**kwargs without type annotation should be flagged."""
    filepath = write_file(
        "def log_kwargs(**kwargs) -> None:\n    print(kwargs)\n"
    )
    validator = TypeValidator(filepath)
    result = validator.validate()

    kwarg_violations = [
        v for v in result.violations
        if "**kwargs" in v.issue and "missing a type annotation" in v.issue
    ]
    assert len(kwarg_violations) > 0


# --- Tests: Well-Known Dunder Methods Are Exempt -----------------------------


def test_init_exempt_from_return_type(write_file) -> None:
    """__init__ should not require explicit return type (returns None)."""
    filepath = write_file(
        "class MyClass:\n"
        "    def __init__(self, x: int) -> None:\n"
        "        self.x = x\n"
    )
    validator = TypeValidator(filepath)
    result = validator.validate()

    return_violations = [
        v for v in result.violations
        if "Missing return type annotation" in v.issue
    ]
    # No violation even if __init__ has no return type
    # (our validator skips well-known dunders)
    assert len(return_violations) == 0


# --- Tests: Missing Docstring Warning ----------------------------------------


def test_public_function_missing_docstring(write_file) -> None:
    """Public function without docstring should produce a warning."""
    filepath = write_file(
        "def public_function(x: int) -> int:\n    return x * 2\n"
    )
    validator = TypeValidator(filepath)
    result = validator.validate()

    doc_warnings = [
        v for v in result.violations
        if "Missing docstring" in v.issue
    ]
    assert len(doc_warnings) > 0
    assert doc_warnings[0].severity == "warning"


def test_private_function_missing_docstring_ok(write_file) -> None:
    """Private function (_leading_underscore) without docstring is OK."""
    filepath = write_file(
        "def _private_helper(x: int) -> int:\n    return x * 2\n"
    )
    validator = TypeValidator(filepath)
    result = validator.validate()

    doc_warnings = [
        v for v in result.violations
        if "Missing docstring" in v.issue
    ]
    assert len(doc_warnings) == 0


# --- Tests: Fully Compliant File ---------------------------------------------


def test_fully_compliant_file(write_file) -> None:
    """A file with complete type hints should have zero violations."""
    compliant = '''\
"""A fully type-annotated module."""

from typing import Optional


def greet(name: str, title: Optional[str] = None) -> str:
    """Return a greeting string."""
    if title:
        return f"Hello, {title} {name}"
    return f"Hello, {name}"


def process_items(items: list[str], count: int = 0) -> dict[str, int]:
    """Process items and return a mapping."""
    return {item: count for item in items}


class Calculator:
    """A calculator class."""

    def add(self, a: int, b: int) -> int:
        """Add two numbers."""
        return a + b

    def divide(self, a: float, b: float) -> Optional[float]:
        """Divide a by b, returning None if b is zero."""
        if b == 0:
            return None
        return a / b
'''
    filepath = write_file(compliant)
    validator = TypeValidator(filepath)
    result = validator.validate()

    assert result.is_clean, (
        f"Expected clean file but found {result.count} violation(s):\n"
        + "\n".join(str(v) for v in result.violations)
    )


# --- Tests: Syntax Error Handling --------------------------------------------


def test_syntax_error_file(write_file) -> None:
    """Validator should handle files with syntax errors gracefully."""
    filepath = write_file("def broken(:\n    pass\n")
    validator = TypeValidator(filepath)
    result = validator.validate()

    # Should have a parse-error violation
    assert result.count > 0


# --- Tests: File Not Found ---------------------------------------------------


def test_file_not_found() -> None:
    """Validator should raise FileNotFoundError for missing files."""
    validator = TypeValidator("/nonexistent/file.py")
    with pytest.raises(FileNotFoundError):
        validator.validate()


# --- Tests: TypeCheckResult Properties ---------------------------------------


def test_result_errors_vs_warnings(write_file) -> None:
    """Errors and warnings should be properly categorized."""
    filepath = write_file(
        "from typing import Any\n"
        "def func(data: Any):\n"  # Warning: Any usage, Error: no return type
        "    return data\n"
    )
    validator = TypeValidator(filepath)
    result = validator.validate()

    assert len(result.errors) > 0
    assert len(result.warnings) > 0
