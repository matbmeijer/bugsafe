---
title: Contributing (Legacy)
---

!!! warning "Legacy Documentation"
    This page has been superseded by the new documentation structure.
    See **[Development Setup](contributing/development-setup.md)** for the current version.

# Contributing to bugsafe

Thank you for your interest in contributing to bugsafe! This document provides guidelines for development setup and contribution workflow.

## Development Setup

### Prerequisites

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- Git

### Clone and Install

```bash
# Clone the repository
git clone https://github.com/matbmeijer/bugsafe.git
cd bugsafe

# Install dependencies with uv
uv sync

# Verify installation
uv run bugsafe --version
```

### Project Structure

```
bugsafe/
├── src/bugsafe/
│   ├── __init__.py          # Package version
│   ├── cli.py               # CLI commands
│   ├── config.py            # Configuration management
│   ├── capture/             # Command capture module
│   │   ├── runner.py        # Process execution
│   │   ├── traceback.py     # Traceback parsing
│   │   └── environment.py   # Environment collection
│   ├── redact/              # Redaction module
│   │   ├── patterns.py      # Secret patterns
│   │   ├── tokenizer.py     # Token generation
│   │   ├── path_anonymizer.py
│   │   └── engine.py        # Redaction orchestration
│   ├── bundle/              # Bundle format module
│   │   ├── schema.py        # Pydantic models
│   │   ├── writer.py        # Bundle creation
│   │   └── reader.py        # Bundle reading
│   └── render/              # Output rendering module
│       ├── markdown.py      # Markdown output
│       └── json_export.py   # JSON/LLM output
├── tests/
│   ├── unit/                # Unit tests
│   ├── integration/         # Integration tests
│   └── fuzz/                # Fuzz tests (Hypothesis)
├── docs/                    # Documentation
└── pyproject.toml           # Project configuration
```

## Development Workflow

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src/bugsafe --cov-report=term-missing

# Run specific test file
uv run pytest tests/unit/test_patterns.py

# Run with verbose output
uv run pytest -v

# Run property tests only
uv run pytest tests/unit/test_redact_properties.py
```

### Linting and Type Checking

```bash
# Type checking with mypy
uv run mypy src/

# Linting with ruff
uv run ruff check src/

# Auto-fix linting issues
uv run ruff check src/ --fix

# Format code
uv run ruff format src/
```

### Security Scanning

```bash
# Run bandit security scanner
uv run bandit -r src/bugsafe -ll
```

### Running the CLI Locally

```bash
# Run CLI commands
uv run bugsafe --help
uv run bugsafe run -- python -c "print('hello')"
uv run bugsafe inspect bug.bugbundle
```

## Code Style

### General Guidelines

- Follow [PEP 8](https://pep8.org/) style guide
- Use type hints for all function signatures
- Keep functions focused (single responsibility)
- Write docstrings for public functions and classes
- Maximum line length: 88 characters (ruff default)

### Imports

```python
# Standard library
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Third-party
import typer
from pydantic import BaseModel

# Local
from bugsafe.redact.patterns import Pattern
```

### Type Hints

```python
# Good
def process_text(text: str, max_length: int = 1000) -> str:
    ...

# Good - use | for unions (Python 3.10+)
def get_value(key: str) -> str | None:
    ...

# Good - use Annotated for CLI
def command(
    path: Annotated[Path, typer.Argument(help="File path")],
) -> None:
    ...
```

### Dataclasses and Pydantic

```python
# Use dataclasses for internal data structures
@dataclass
class CaptureResult:
    stdout: str
    stderr: str
    exit_code: int

# Use Pydantic for serialized data (JSON/bundles)
class BundleMetadata(BaseModel):
    version: str = "1.0"
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

## Adding New Features

### Adding a New Redaction Pattern

1. Add the pattern to `src/bugsafe/redact/patterns.py`:

```python
Pattern(
    name="my_new_pattern",
    regex=r"MY_PREFIX_[A-Z0-9]{32}",
    category=SecretCategory.API_KEY,
    priority=Priority.HIGH,
    description="My New Service API Key",
)
```

2. Add tests in `tests/unit/test_patterns.py`:

```python
def test_my_new_pattern_matches():
    pattern = get_pattern("my_new_pattern")
    assert pattern.matches("MY_PREFIX_ABCD1234567890ABCD1234567890AB")
```

3. Update `docs/PATTERNS.md` with the new pattern.

### Adding a New CLI Command

1. Add the command to `src/bugsafe/cli.py`:

```python
@app.command()
def my_command(
    arg: Annotated[str, typer.Argument(help="Description")],
) -> None:
    """Command description."""
    ...
```

2. Add integration tests in `tests/integration/test_cli.py`.

3. Update `README.md` CLI reference.

## Testing Guidelines

### Unit Tests

- Test one thing per test function
- Use descriptive test names: `test_<what>_<condition>_<expected>`
- Use fixtures for common setup

```python
def test_redaction_removes_aws_key():
    engine = create_redaction_engine()
    text = "key: AKIAIOSFODNN7EXAMPLE"
    result, _ = engine.redact(text)
    assert "AKIAIOSFODNN7EXAMPLE" not in result
```

### Property Tests (Hypothesis)

- Use for testing invariants
- Good for redaction safety properties

```python
@given(st.text(max_size=1000))
def test_redaction_is_idempotent(text: str):
    engine = create_redaction_engine()
    r1, _ = engine.redact(text)
    r2, _ = engine.redact(r1)
    assert r1 == r2
```

### Integration Tests

- Test complete workflows
- Use `typer.testing.CliRunner` for CLI tests

```python
def test_run_and_render_workflow(tmp_path):
    runner = CliRunner()
    bundle = tmp_path / "test.bugbundle"

    # Run command
    result = runner.invoke(app, ["run", "-o", str(bundle), "echo", "hello"])
    assert result.exit_code == 0

    # Render bundle
    result = runner.invoke(app, ["render", str(bundle)])
    assert "# Bug Report" in result.stdout
```

## Pull Request Process

1. **Fork** the repository
2. **Create a branch** for your feature: `git checkout -b feature/my-feature`
3. **Make changes** following the code style guidelines
4. **Add tests** for new functionality
5. **Run all checks**:
   ```bash
   uv run pytest
   uv run mypy src/
   uv run ruff check src/
   ```
6. **Commit** with a descriptive message
7. **Push** to your fork
8. **Open a Pull Request** with:
   - Clear description of changes
   - Link to any related issues
   - Screenshots/examples if applicable

## Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add new redaction pattern for Stripe keys
fix: handle empty traceback in parser
docs: update CLI reference in README
test: add property tests for tokenizer
refactor: simplify path anonymization logic
```

## Release Process

Releases are fully automated via GitHub Actions when a tag is pushed. Version is derived from git tags using `uv-dynamic-versioning` — no manual version updates needed.

### Creating a Release

```bash
# 1. Ensure you're on main with all changes committed
git checkout main
git pull origin main

# 2. Verify tests pass locally
uv run pytest tests/ -v
uv run mypy src/
uv run ruff check src/

# 3. Create annotated tag (triggers release pipeline)
git tag -a v0.2.0 -m "Release v0.2.0: Brief description of changes"

# 4. Push tag to trigger automation
git push origin v0.2.0
```

### What Happens Automatically

When you push a tag:

- ✅ Tests and linting run
- ✅ Package built with version from tag
- ✅ Published to PyPI (stable) or TestPyPI (pre-release)
- ✅ GitHub Release created with auto-generated notes
- ✅ Documentation deployed with version

### Pre-release Testing

For release candidates (publishes to TestPyPI only):

```bash
git tag -a v0.2.0-rc1 -m "Release candidate 1 for v0.2.0"
git push origin v0.2.0-rc1
```

### Version Format

Follow [Semantic Versioning](https://semver.org/) with `v` prefix:

| Version | Meaning |
|---------|---------|
| `v0.1.0` | Initial release |
| `v0.1.1` | Patch (bug fix) |
| `v0.2.0` | Minor (new feature, backward compatible) |
| `v1.0.0` | Major (breaking changes) |
| `v0.2.0-rc1` | Pre-release (TestPyPI only) |

### Hotfix Process

For urgent production fixes:

```bash
git checkout main
git pull origin main
# Make fix
git commit -m "fix: critical issue description"
git tag -a v0.1.1 -m "Hotfix: Critical fix description"
git push origin main v0.1.1
```

## Getting Help

- Open an issue for bugs or feature requests
- Check existing issues before creating new ones
- Join discussions for questions

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
