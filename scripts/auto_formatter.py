#!/usr/bin/env python3
"""
Automatic Python Code Formatter.

Formats Python source files to comply with PEP8 standards using
black (code formatting) and isort (import sorting).

Usage:
    python auto_formatter.py <filename>             # Format in-place
    python auto_formatter.py <filename> --check     # Check only, no changes
    python auto_formatter.py <filename> --diff      # Show diff without applying
    python auto_formatter.py <directory>            # Format all .py files in dir
"""

from __future__ import annotations

import difflib
import os
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Optional


# --- Data Classes ------------------------------------------------------------


@dataclass
class FormatResult:
    """Result of running the formatter on a file."""

    filepath: str
    success: bool = True
    was_formatted: bool = False
    diff: Optional[str] = None
    errors: list[str] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        """Return True if no formatting was needed."""
        return self.success and not self.was_formatted


# --- Formatter Class ---------------------------------------------------------


class AutoFormatter:
    """
    Formatter for Python source code.

    Applies black and isort to format code according to PEP8 standards.
    """

    # Configuration
    LINE_LENGTH: int = 79

    def __init__(self, filepath: str) -> None:
        self.filepath: str = filepath

    def format(self, check_only: bool = False) -> FormatResult:
        """
        Format a Python file.

        Args:
            check_only: If True, only check without applying changes.

        Returns:
            FormatResult with status and diff information.
        """
        result = FormatResult(filepath=self.filepath)

        if not os.path.exists(self.filepath):
            result.success = False
            result.errors.append(f"File not found: {self.filepath}")
            return result

        if not self.filepath.endswith(".py"):
            result.success = False
            result.errors.append(
                f"Not a Python file: {self.filepath}"
            )
            return result

        # Read original content for diff
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                original = f.read()
        except Exception as e:
            result.success = False
            result.errors.append(f"Cannot read file: {e}")
            return result

        # Step 1: Format with isort (import sorting)
        isort_ok = self._run_isort(check_only)

        # Step 2: Format with black (code formatting)
        black_ok = self._run_black(check_only)

        # Read formatted content
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                formatted = f.read()
        except Exception as e:
            result.success = False
            result.errors.append(f"Cannot read formatted file: {e}")
            return result

        # Generate diff
        if original != formatted:
            result.was_formatted = True
            result.diff = self._generate_diff(original, formatted)

            # Restore original if check_only
            if check_only:
                try:
                    with open(self.filepath, "w", encoding="utf-8") as f:
                        f.write(original)
                except Exception as e:
                    result.errors.append(f"Cannot restore original: {e}")

        result.success = isort_ok and black_ok and not result.errors
        return result

    def _run_isort(self, check_only: bool) -> bool:
        """Run isort on the file."""
        cmd = ["isort"]

        if check_only:
            cmd.append("--check-only")
            cmd.append("--diff")

        cmd.extend(["--profile", "black"])
        cmd.extend(["--line-length", str(self.LINE_LENGTH)])
        cmd.append(self.filepath)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0 and check_only:
                return False  # File needs formatting
            return True
        except FileNotFoundError:
            # isort not installed — this is non-fatal
            return True
        except subprocess.TimeoutExpired:
            return False

    def _run_black(self, check_only: bool) -> bool:
        """Run black on the file."""
        cmd = ["black"]

        if check_only:
            cmd.append("--check")
            cmd.append("--diff")

        cmd.extend(["--line-length", str(self.LINE_LENGTH)])
        cmd.extend(["--target-version", "py39"])
        cmd.append(self.filepath)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0 and check_only:
                return False  # File needs formatting
            return True
        except FileNotFoundError:
            # black not installed — this is non-fatal
            return True
        except subprocess.TimeoutExpired:
            return False

    def _generate_diff(self, original: str, formatted: str) -> str:
        """Generate a unified diff between original and formatted."""
        diff = difflib.unified_diff(
            original.splitlines(keepends=True),
            formatted.splitlines(keepends=True),
            fromfile=f"{self.filepath} (original)",
            tofile=f"{self.filepath} (formatted)",
        )
        return "".join(diff)


def format_directory(
    directory: str, check_only: bool = False
) -> list[FormatResult]:
    """
    Format all Python files in a directory (recursively).

    Args:
        directory: Root directory to search.
        check_only: If True, only check without applying changes.

    Returns:
        List of FormatResult for each file processed.
    """
    results: list[FormatResult] = []

    for root, dirs, files in os.walk(directory):
        # Skip virtual environments and hidden directories
        dirs[:] = [
            d
            for d in dirs
            if d not in (".venv", "venv", ".tox", ".git", "__pycache__", ".eggs")
            and not d.startswith(".")
        ]

        for filename in files:
            if filename.endswith(".py"):
                filepath = os.path.join(root, filename)
                formatter = AutoFormatter(filepath)
                result = formatter.format(check_only=check_only)
                results.append(result)

    return results


# --- Output Helpers ----------------------------------------------------------


def print_result(result: FormatResult, check_only: bool = False) -> None:
    """Print a single format result."""
    filename = os.path.basename(result.filepath)

    if not result.success:
        for err in result.errors:
            print(f"✗ {filename}: Error — {err}")
        return

    if result.was_formatted:
        if check_only:
            print(f"✗ {filename}: Needs formatting")
        else:
            print(f"↻ {filename}: Formatted")
        if result.diff:
            print(result.diff)
    else:
        print(f"✓ {filename}: Already formatted")


def print_summary(
    results: list[FormatResult], check_only: bool = False
) -> None:
    """Print a summary of all format results."""
    total = len(results)
    formatted = sum(1 for r in results if r.was_formatted)
    failed = sum(1 for r in results if not r.success)

    print(f"\n{'=' * 60}")
    print(f"Summary: {total} file(s) processed")
    if check_only:
        print(f"  {total - formatted - failed} clean")
        print(f"  {formatted} need(s) formatting")
    else:
        print(f"  {total - formatted - failed} already formatted")
        print(f"  {formatted} formatted")
    if failed:
        print(f"  {failed} failed")
    print(f"{'=' * 60}")


# --- Main -------------------------------------------------------------------


def main() -> None:
    """Run auto-formatter from the command line."""
    if len(sys.argv) < 2:
        print(
            "Usage: python auto_formatter.py <filename|directory> "
            "[--check] [--diff]"
        )
        sys.exit(1)

    target: str = sys.argv[1]
    check_only: bool = "--check" in sys.argv or "--diff" in sys.argv

    try:
        if os.path.isfile(target):
            formatter = AutoFormatter(target)
            result = formatter.format(check_only=check_only)
            print_result(result, check_only=check_only)
            sys.exit(0 if result.success else 1)

        elif os.path.isdir(target):
            results = format_directory(target, check_only=check_only)
            for r in results:
                print_result(r, check_only=check_only)
            print_summary(results, check_only=check_only)

            all_clean = all(r.success for r in results)
            sys.exit(0 if all_clean else 1)

        else:
            print(f"Error: '{target}' is not a valid file or directory.")
            sys.exit(2)

    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(3)


if __name__ == "__main__":
    main()
