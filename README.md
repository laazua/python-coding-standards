# Python Coding Standards

A comprehensive Python coding standards enforcement toolkit that ensures PEP8 compliance, strict type hinting, and consistent code formatting across your projects.

## Overview

This skill provides automated tooling to enforce Python coding best practices:

- **PEP8 Compliance** — Automated checking of indentation, line length, whitespace, naming conventions, and import ordering
- **Strict Type Validation** — Mandatory type hints on all functions with mypy integration
- **Auto-formatting** — One-command formatting via black and isort
- **Git Hooks** — Pre-commit and pre-push hooks to catch issues before they reach the repository

## Installation

### 1. Install Dependencies

```bash
pip install black>=23.0.0 mypy>=1.0.0 pylint>=3.0.0 isort>=5.12.0
```

### 2. Install Git Hooks (Optional)

```bash
cp hooks/pre-commit .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit
cp hooks/pre-push .git/hooks/pre-push && chmod +x .git/hooks/pre-push
```

### 3. Copy Configuration Files to Your Project

```bash
cp config/pyproject.toml <your-project>/
cp config/.pylintrc <your-project>/
cp config/mypy.ini <your-project>/
cp config/.pre-commit-config.yaml <your-project>/
```

## Usage

### Check a Single File

```bash
# PEP8 compliance check
python scripts/pep8_checker.py path/to/file.py

# Type hint validation
python scripts/type_validator.py path/to/file.py
```

### Auto-format a File

```bash
python scripts/auto_formatter.py path/to/file.py
```

### Check an Entire Project

```bash
# Run on all Python files (excluding virtual environments)
find . -name "*.py" -not -path "./.venv/*" -not -path "./venv/*" -not -path "./.tox/*" | while read f; do
    python scripts/pep8_checker.py "$f"
    python scripts/type_validator.py "$f"
done
```

### Run Tests

```bash
python -m pytest tests/ -v
```

## Standards Enforced

### PEP8 Rules
- 4-space indentation (no tabs)
- 79-character line limit (72 for docstrings/comments)
- Proper blank line spacing
- Ordered imports (stdlib → third-party → local)
- No wildcard imports
- `snake_case` naming for functions/variables
- `PascalCase` naming for classes
- `UPPER_CASE` naming for constants

### Type Hints
- Mandatory type annotations on ALL function parameters
- Mandatory return type annotations
- Consistent use of `typing` module constructs
- `Optional[T]` for nullable types
- `Union[T1, T2]` for multi-type parameters

## File Structure

```
python-coding-standards/
├── SKILL.md                    # Main rule definitions
├── README.md                   # Usage guide (this file)
├── scripts/
│   ├── __init__.py
│   ├── pep8_checker.py         # PEP8 compliance checker
│   ├── type_validator.py       # Type hint validator
│   └── auto_formatter.py       # Automatic formatter (black + isort)
├── config/
│   ├── .pylintrc               # Pylint configuration
│   ├── .pre-commit-config.yaml # Pre-commit hook config
│   ├── pyproject.toml          # Black + isort configuration
│   └── mypy.ini                # Mypy strict mode settings
├── hooks/
│   ├── pre-commit              # Pre-commit git hook
│   └── pre-push                # Pre-push git hook
└── tests/
    ├── test_pep8_compliance.py # Tests for PEP8 checker
    └── test_type_hints.py      # Tests for type validator
```

## License

MIT
