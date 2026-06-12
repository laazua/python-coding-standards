---
name: python-coding-standards
description: Enforces PEP8 coding standards and strict type constraints for Python development. Automatically activates during Python coding sessions.
version: 1.0.0
author: Python Standards Team
triggers:
  - "*.py"
  - "python:*"
auto_activate: true
priority: high
dependencies:
  - black>=23.0.0
  - mypy>=1.0.0
  - pylint>=3.0.0
  - isort>=5.12.0
---

# Python Coding Standards Enforcer

This skill enforces strict Python coding standards following PEP8 and mandatory type hints.

## When This Skill Activates

Automatically activates when:
- User creates or edits any `.py` file
- User asks about Python code quality
- User requests code review for Python
- User mentions Python coding standards

## Core Constraints

### 1. PEP8 Compliance (MANDATORY)

Enforce these PEP8 rules:

#### Indentation
- Use 4 spaces per indentation level (NO tabs)
- Continuation lines should align with opening delimiter or use hanging indent

#### Line Length
- Maximum 79 characters for code
- Maximum 72 characters for docstrings/comments

#### Blank Lines
- Two blank lines before top-level functions and classes
- One blank line between class methods

#### Imports
- Each import on separate line
- Order: standard library → third-party → local imports
- No wildcard imports (`from module import *`)

#### Whitespace
- No spaces inside parentheses, brackets, braces
- One space around operators
- No trailing whitespace

#### Naming Conventions
- `snake_case` for functions, variables, and modules
- `PascalCase` for classes
- `UPPER_CASE` for constants
- `_leading_underscore` for private/internal use
- `__double_leading_underscore` for name mangling

#### Comments and Docstrings
- All modules, classes, and public functions must have docstrings
- Use triple double-quotes (`"""`) for docstrings
- First line: summary, blank line, then detailed description
- Comments must be complete sentences with proper capitalization

### 2. Type Constraints (STRICT)

#### Mandatory Type Hints
Every function must have:
- Type hints for ALL parameters
- Type hint for return value
- Use `-> None` for void functions

#### Type Hint Rules
- Use `typing` module constructs for complex types
- Prefer built-in generics (`list[str]`, `dict[str, int]`) for Python 3.9+
- Use `Optional[T]` instead of `T | None` for consistency
- Use `Union[T1, T2]` for multiple allowed types
- Use `Any` sparingly and document why it's necessary
- Class methods must have `self` typed (implicitly via class type)
- Static methods and class methods must have full type hints

### 3. Code Structure

#### Module Organization
1. Shebang line (if executable)
2. Module docstring
3. `__future__` imports
4. Module-level dunder names (`__all__`, `__version__`, etc.)
5. Standard library imports
6. Third-party imports
7. Local imports
8. Module-level constants
9. Module-level classes and functions

#### Function Guidelines
- Single responsibility principle
- Maximum 50 lines per function (strongly recommended)
- Maximum 5 parameters (use dataclass or TypedDict for more)
- Prefer keyword-only arguments for functions with 3+ parameters

### 4. Error Handling
- Never use bare `except:`, always catch specific exceptions
- Use `with` statements for resource management
- Raise specific exceptions, never use bare `raise`
- Custom exceptions should inherit from `Exception`, not `BaseException`

### 5. Testing Requirements
- Unit tests for all public functions using pytest
- Test files in `tests/` directory mirroring source structure
- Test function naming: `test_<function_name>_<scenario>`
- Use fixtures over setup/teardown methods
- Aim for 80%+ code coverage

## Enforcement Commands

```bash
# Check PEP8 compliance of a file
python scripts/pep8_checker.py <filename>

# Validate type hints in a file
python scripts/type_validator.py <filename>

# Auto-format a file to comply with standards
python scripts/auto_formatter.py <filename>

# Run all checks on a file
python scripts/pep8_checker.py <filename> && python scripts/type_validator.py <filename>

# Run all checks on entire project
find . -name "*.py" -not -path "./.venv/*" -not -path "./venv/*" | while read f; do
    python scripts/pep8_checker.py "$f"
    python scripts/type_validator.py "$f"
done
```

## Configuration Files

| File | Purpose |
|------|---------|
| `config/pyproject.toml` | Black and isort configuration |
| `config/.pylintrc` | Pylint rule customization |
| `config/mypy.ini` | Mypy strict mode configuration |
| `config/.pre-commit-config.yaml` | Pre-commit hook definitions |

## Git Hooks

- **pre-commit**: Runs auto-formatter and PEP8 check on staged Python files
- **pre-push**: Runs full type validation and linting on all Python files

## Quick Start

```bash
# Install dependencies
pip install black>=23.0.0 mypy>=1.0.0 pylint>=3.0.0 isort>=5.12.0

# Install git hooks
cp hooks/pre-commit .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit
cp hooks/pre-push .git/hooks/pre-push && chmod +x .git/hooks/pre-push

# Format a file
python scripts/auto_formatter.py path/to/file.py

# Check a file
python scripts/pep8_checker.py path/to/file.py
python scripts/type_validator.py path/to/file.py
```
