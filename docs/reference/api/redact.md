# Redaction API

The redaction module provides the core functionality for detecting and redacting secrets.

## Overview

```python
from bugsafe.redact import RedactionEngine, PatternConfig

# Create engine with default settings
engine = RedactionEngine()

# Redact text
text = "API_KEY=sk-abc123xyz"
redacted, report = engine.redact(text)
print(redacted)  # API_KEY=<API_KEY_1>
print(report.get_total())  # 1
```

## RedactionEngine

Main orchestrator for secret redaction.

::: bugsafe.redact.engine.RedactionEngine
    options:
      show_source: false
      heading_level: 3
      members:
        - redact
        - verify_redaction
        - get_salt_hash
        - get_redaction_summary

## RedactionReport

Tracks all redactions performed in a session.

::: bugsafe.redact.engine.RedactionReport
    options:
      show_source: false
      heading_level: 3
      members:
        - add
        - merge
        - get_summary
        - get_total

## Pattern

Defines a secret detection pattern.

::: bugsafe.redact.patterns.Pattern
    options:
      show_source: false
      heading_level: 3

## PatternConfig

Configuration for pattern matching behavior.

::: bugsafe.redact.patterns.PatternConfig
    options:
      show_source: false
      heading_level: 3

## Tokenizer

Deterministic, correlation-preserving tokenizer.

::: bugsafe.redact.tokenizer.Tokenizer
    options:
      show_source: false
      heading_level: 3
      members:
        - tokenize
        - is_token
        - get_salt_hash
        - get_report
        - reset

## Factory Functions

::: bugsafe.redact.engine.create_redaction_engine
    options:
      show_source: false
      heading_level: 3

::: bugsafe.redact.patterns.create_custom_pattern
    options:
      show_source: false
      heading_level: 3
