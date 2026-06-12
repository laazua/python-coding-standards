"""
Tests for the PEP8 compliance checker.

Verifies that pep8_checker.py correctly identifies PEP8 violations.
"""

from __future__ import annotations

import os
import tempfile
from typing import Generator

import pytest

# Import the checker module
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from pep8_checker import PEP8Checker, CheckResult


# --- Fixtures ----------------------------------------------------------------


@pytest.fixture
def temp_py_file() -> Generator[str, None, None]:
    """Create a temporary .py file for testing."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as f:
        filepath = f.name
    yield filepath
    os.unlink(filepath)


@pytest.fixture
def write_file() -> Generator:
    """Helper to write content to a temp file."""
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


# --- Tests: Tabs -------------------------------------------------------------


def test_tabs_not_allowed(write_file) -> None:
    """E101: Tabs should be flagged as violations."""
    filepath = write_file("def my_function():\n\tpass\n")
    checker = PEP8Checker(filepath)
    result = checker.check()

    tab_violations = [v for v in result.violations if v.code == "E101"]
    assert len(tab_violations) > 0
    assert "tab" in tab_violations[0].message.lower()


def test_spaces_allowed(write_file) -> None:
    """4-space indentation should pass."""
    filepath = write_file("def my_function():\n    pass\n")
    checker = PEP8Checker(filepath)
    result = checker.check()

    tab_violations = [v for v in result.violations if v.code == "E101"]
    assert len(tab_violations) == 0


# --- Tests: Line Length ------------------------------------------------------


def test_line_too_long(write_file) -> None:
    """E501: Lines over 79 characters should be flagged."""
    long_line = "x = " + "'" + "a" * 80 + "'\n"
    filepath = write_file(long_line)
    checker = PEP8Checker(filepath)
    result = checker.check()

    length_violations = [v for v in result.violations if v.code == "E501"]
    assert len(length_violations) > 0


def test_line_under_limit(write_file) -> None:
    """Lines under 79 characters should pass."""
    short_line = "x = '" + "a" * 60 + "'\n"
    filepath = write_file(short_line)
    checker = PEP8Checker(filepath)
    result = checker.check()

    length_violations = [v for v in result.violations if v.code == "E501"]
    assert len(length_violations) == 0


# --- Tests: Trailing Whitespace ----------------------------------------------


def test_trailing_whitespace(write_file) -> None:
    """W291: Trailing whitespace should be flagged."""
    filepath = write_file("x = 1   \ny = 2\n")
    checker = PEP8Checker(filepath)
    result = checker.check()

    trailing = [v for v in result.violations if v.code == "W291"]
    assert len(trailing) > 0


def test_no_trailing_whitespace(write_file) -> None:
    """Clean lines should pass."""
    filepath = write_file("x = 1\ny = 2\n")
    checker = PEP8Checker(filepath)
    result = checker.check()

    trailing = [v for v in result.violations if v.code == "W291"]
    assert len(trailing) == 0


# --- Tests: Blank Lines ------------------------------------------------------


def test_top_level_function_missing_blank_lines(write_file) -> None:
    """E302: Top-level functions need 2 blank lines before them."""
    filepath = write_file("import os\ndef my_function():\n    pass\n")
    checker = PEP8Checker(filepath)
    result = checker.check()

    blank_violations = [v for v in result.violations if v.code == "E302"]
    assert len(blank_violations) > 0


def test_top_level_function_with_blank_lines(write_file) -> None:
    """Top-level functions with 2 blank lines should pass."""
    filepath = write_file("import os\n\n\ndef my_function():\n    pass\n")
    checker = PEP8Checker(filepath)
    result = checker.check()

    blank_violations = [v for v in result.violations if v.code == "E302"]
    assert len(blank_violations) == 0


# --- Tests: Wildcard Imports -------------------------------------------------


def test_wildcard_import_flagged(write_file) -> None:
    """E999: Wildcard imports should be flagged."""
    filepath = write_file("from os import *\n")
    checker = PEP8Checker(filepath)
    result = checker.check()

    wildcard = [v for v in result.violations if v.code == "E999"]
    assert len(wildcard) > 0


def test_normal_import_allowed(write_file) -> None:
    """Normal imports should pass."""
    filepath = write_file("import os\nfrom sys import argv\n")
    checker = PEP8Checker(filepath)
    result = checker.check()

    wildcard = [v for v in result.violations if v.code == "E999"]
    assert len(wildcard) == 0


# --- Tests: Missing Newline at EOF -------------------------------------------


def test_missing_newline_eof(write_file) -> None:
    """W292: Missing newline at end of file should be flagged."""
    filepath = write_file("x = 1")
    checker = PEP8Checker(filepath)
    result = checker.check()

    eof_violations = [v for v in result.violations if v.code == "W292"]
    assert len(eof_violations) > 0


def test_newline_at_eof_passes(write_file) -> None:
    """Files ending with newline should pass."""
    filepath = write_file("x = 1\n")
    checker = PEP8Checker(filepath)
    result = checker.check()

    eof_violations = [v for v in result.violations if v.code == "W292"]
    assert len(eof_violations) == 0


# --- Tests: Naming Conventions -----------------------------------------------


def test_class_name_pascalcase(write_file) -> None:
    """N801: Class names should be PascalCase."""
    filepath = write_file("class my_class:\n    pass\n")
    checker = PEP8Checker(filepath)
    result = checker.check()

    naming = [v for v in result.violations if v.code == "N801"]
    assert len(naming) > 0


def test_class_name_valid_passes(write_file) -> None:
    """PascalCase class names should pass."""
    filepath = write_file("class MyClass:\n    pass\n")
    checker = PEP8Checker(filepath)
    result = checker.check()

    naming = [v for v in result.violations if v.code == "N801"]
    assert len(naming) == 0


# --- Tests: Whitespace -------------------------------------------------------


def test_space_after_open_paren(write_file) -> None:
    """E201: Space after '(' should be flagged."""
    filepath = write_file("x = ( 'hello')\n")
    checker = PEP8Checker(filepath)
    result = checker.check()

    whitespace = [v for v in result.violations if v.code == "E201"]
    assert len(whitespace) > 0


def test_space_before_close_paren(write_file) -> None:
    """E202: Space before ')' should be flagged."""
    filepath = write_file("x = ('hello' )\n")
    checker = PEP8Checker(filepath)
    result = checker.check()

    whitespace = [v for v in result.violations if v.code == "E202"]
    assert len(whitespace) > 0


# --- Tests: Clean File -------------------------------------------------------


def test_clean_file_passes(write_file) -> None:
    """A fully compliant file should have zero violations."""
    clean_code = '''\
"""A clean module."""


def clean_function(param1: str, param2: int) -> str:
    """Return the string representation."""
    return f"{param1}: {param2}"


class CleanClass:
    """A clean class."""

    def method_one(self) -> None:
        """Do nothing."""
        pass

    def method_two(self) -> str:
        """Return a string."""
        return "hello"
'''
    filepath = write_file(clean_code)
    checker = PEP8Checker(filepath)
    result = checker.check()

    assert result.is_clean, (
        f"Expected clean file but found {result.count} violation(s):\n"
        + "\n".join(str(v) for v in result.violations)
    )


# --- Tests: File Not Found ---------------------------------------------------


def test_file_not_found() -> None:
    """Checker should raise FileNotFoundError for missing files."""
    checker = PEP8Checker("/nonexistent/file.py")
    with pytest.raises(FileNotFoundError):
        checker.check()


# --- Tests: CheckResult Properties -------------------------------------------


def test_check_result_is_clean() -> None:
    """CheckResult.is_clean should return True when no violations."""
    result = CheckResult(filepath="test.py")
    assert result.is_clean is True


def test_check_result_count() -> None:
    """CheckResult.count should return the number of violations."""
    result = CheckResult(filepath="test.py")
    assert result.count == 0


# --- Tests: Module-level ViolationCodes --------------------------------------


def test_violation_sorting(write_file) -> None:
    """Violations should be sorted by line number."""
    filepath = write_file("x = ( 'hello' )\n\tpass\n")
    checker = PEP8Checker(filepath)
    result = checker.check()

    # Verify violations are sorted by line
    for i in range(len(result.violations) - 1):
        assert (
            result.violations[i].line <= result.violations[i + 1].line
        )
