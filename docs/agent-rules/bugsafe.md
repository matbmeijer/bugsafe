---
description: bugsafe crash capture and secret redaction
globs:
alwaysApply: false
---

# bugsafe Agent Instructions

bugsafe creates safe-to-share crash bundles with automatic secret redaction.

## Commands

- `bugsafe run -- <command>` — Capture crash with redaction
- `bugsafe render <bundle>` — Render to markdown
- `bugsafe render <bundle> --llm` — Render for LLM context
- `bugsafe scan <files>` — Scan for secrets
- `bugsafe audit <bundle>` — Verify redaction
- `bugsafe mcp` — Start MCP server

## Development

- `uv run pytest tests/ -v` — Run tests
- `uv run ruff check src/` — Lint
- `uv run mypy src/bugsafe/` — Type check

## MCP Tools

When MCP server is running:

- `scan_secrets` — Scan text for secrets
- `capture_crash` — Run command and capture output
- `render_bundle` — Render bundle to readable format
- `audit_bundle` — Verify redaction completeness
- `create_bundle` — Create a full bundle file

## Redaction Tokens

Secrets are replaced with tokens: `<API_KEY_1>`, `<TOKEN_2>`, etc.
Same secret = same token (correlation preserved).

## Project Structure

- `src/bugsafe/capture/` — Command execution
- `src/bugsafe/redact/` — Secret detection
- `src/bugsafe/bundle/` — Bundle format
- `src/bugsafe/render/` — Output rendering
- `src/bugsafe/mcp/` — MCP server

## Code Style

- Python 3.10+ with type hints
- Follow SOLID principles
- No legacy/backwards compatibility code
- DRY while maintaining readability
