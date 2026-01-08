# Code Style

Guidelines for writing consistent, maintainable code.

## Formatting

We use [Ruff](https://docs.astral.sh/ruff/) for formatting:

```bash
# Format code
uv run ruff format src/

# Check formatting
uv run ruff format --check src/
```

## Linting

```bash
# Run linter
uv run ruff check src/

# Auto-fix issues
uv run ruff check --fix src/
```

## Type Checking

We use [mypy](https://mypy.readthedocs.io/) with strict mode:

```bash
uv run mypy src/
```

All public functions must have type annotations.

## Docstrings

Use Google-style docstrings:

```python
def redact(text: str, patterns: list[Pattern]) -> tuple[str, Report]:
    """Redact sensitive information from text.

    Args:
        text: The text to redact.
        patterns: List of patterns to apply.

    Returns:
        Tuple of (redacted_text, report).

    Raises:
        RedactionError: If redaction fails.
    """
```

## Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Classes | PascalCase | `RedactionEngine` |
| Functions | snake_case | `create_bundle` |
| Constants | UPPER_SNAKE | `DEFAULT_TIMEOUT` |
| Private | _prefix | `_internal_method` |

## Imports

Use `ruff` to sort imports:

```python
# Standard library
import os
from pathlib import Path

# Third-party
import typer
from pydantic import BaseModel

# Local
from bugsafe.redact import RedactionEngine
```

## Error Handling

- Use specific exception types
- Provide helpful error messages
- Log warnings for non-fatal issues

```python
class RedactionError(Exception):
    """Raised when redaction fails."""

def redact(text: str) -> str:
    if not text:
        raise RedactionError("Cannot redact empty text")
```

## Testing

Every new feature needs tests. See [Testing](testing.md).

## See Also

- [Development Setup](development-setup.md)
- [Testing](testing.md)
