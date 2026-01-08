# Development Setup

Set up your development environment for contributing to bugsafe.

## Prerequisites

- Python 3.10+
- Git
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

## Clone the Repository

```bash
git clone https://github.com/matbmeijer/bugsafe.git
cd bugsafe
```

## Install Dependencies

```bash
# With uv (recommended)
uv sync --all-extras

# With pip
pip install -e ".[dev]"
```

## Verify Installation

```bash
# Run tests
uv run pytest tests/ -v

# Run linters
uv run mypy src/
uv run ruff check src/

# Run the CLI
uv run bugsafe --version
```

## IDE Setup

### VS Code

Recommended extensions:

- Python
- Pylance
- Ruff

Settings (`.vscode/settings.json`):

```json
{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "python.analysis.typeCheckingMode": "strict",
  "ruff.enable": true
}
```

### PyCharm

1. Set interpreter to `.venv/bin/python`
2. Enable Ruff plugin
3. Enable mypy integration

## Pre-commit Hooks

```bash
uv run pre-commit install
```

This runs linting on every commit.

## Project Structure

```text
bugsafe/
├── src/bugsafe/        # Source code
│   ├── capture/        # Command execution
│   ├── redact/         # Secret redaction
│   ├── bundle/         # Bundle format
│   ├── render/         # Output rendering
│   └── cli.py          # CLI entry point
├── tests/              # Test suite
│   ├── unit/
│   ├── integration/
│   └── property/
├── docs/               # Documentation
└── pyproject.toml      # Project config
```

## Next Steps

- [Code Style](code-style.md)
- [Testing](testing.md)
- [Release Process](release-process.md)
