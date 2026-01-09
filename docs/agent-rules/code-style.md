---
description: Python code style guidelines for bugsafe
paths: src/**/*.py
---

# Python Code Style

## Type Hints

- All functions must have type hints
- Use `from __future__ import annotations` for forward references
- Use `TYPE_CHECKING` block for import-only types

## Imports

- Imports at top of file, never inline (except in functions to avoid circular imports)
- Use lazy imports in CLI commands for faster startup
- Order: stdlib, third-party, local

## Error Handling

- Use specific exception types
- Chain exceptions with `raise ... from err` or `raise ... from None`
- Log errors before re-raising when appropriate

## Naming

- snake_case for functions and variables
- PascalCase for classes
- UPPER_CASE for constants
- Prefix private methods with underscore

## Docstrings

- Use Google-style docstrings
- Document Args, Returns, Raises
- Keep docstrings concise but complete
