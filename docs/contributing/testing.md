# Testing

Guidelines for testing bugsafe code.

## Running Tests

```bash
# All tests
uv run pytest tests/ -v

# Specific test file
uv run pytest tests/unit/test_engine.py -v

# With coverage
uv run pytest tests/ --cov=src/bugsafe --cov-report=html
```

## Test Structure

```text
tests/
├── unit/              # Unit tests
│   ├── test_engine.py
│   ├── test_patterns.py
│   └── test_tokenizer.py
├── integration/       # Integration tests
│   └── test_cli.py
└── property/          # Property-based tests
    └── test_redaction_properties.py
```

## Writing Unit Tests

```python
import pytest
from bugsafe.redact import create_redaction_engine

class TestRedactionEngine:
    def test_redacts_api_key(self):
        engine = create_redaction_engine()
        text = "API_KEY=sk-abc123xyz"

        result, report = engine.redact(text)

        assert "sk-abc123" not in result
        assert "<API_KEY_" in result
        assert report.get_total() == 1
```

## Property-Based Tests

We use [Hypothesis](https://hypothesis.readthedocs.io/) for property testing:

```python
from hypothesis import given, strategies as st

@given(st.text())
def test_redaction_is_idempotent(text):
    engine = create_redaction_engine()
    result1, _ = engine.redact(text)
    result2, _ = engine.redact(result1)
    assert result1 == result2
```

## Test Categories

### Security Tests

Ensure secrets are properly redacted:

```python
def test_aws_key_redacted():
    engine = create_redaction_engine()
    text = "AKIAIOSFODNN7EXAMPLE"
    result, _ = engine.redact(text)
    assert "AKIA" not in result
```

### Edge Cases

Test boundary conditions:

```python
def test_empty_input():
    engine = create_redaction_engine()
    result, report = engine.redact("")
    assert result == ""
    assert report.get_total() == 0
```

## Coverage Requirements

- Minimum: 80% coverage
- New features: Must have tests
- Security code: 100% coverage

## Continuous Integration

Tests run automatically on:

- Push to `main`/`develop`
- Pull requests
- Multiple Python versions (3.10-3.13)
- Multiple OS (Linux, macOS, Windows)

## See Also

- [Development Setup](development-setup.md)
- [Code Style](code-style.md)
