# bugsafe Agent Instructions

bugsafe creates safe-to-share crash bundles with automatic secret redaction.

## Commands

- `bugsafe run -- <command>` — Capture crash with redaction
- `bugsafe run -t 60 -- <command>` — With custom timeout
- `bugsafe render <bundle>` — Render to markdown
- `bugsafe render <bundle> --llm` — Render for LLM context
- `bugsafe render <bundle> -f json` — Render as JSON
- `bugsafe scan <files>` — Scan for secrets (exit 4 if found)
- `bugsafe scan -v <files>` — Verbose mode (show skipped files)
- `bugsafe audit <bundle>` — Verify redaction
- `bugsafe inspect <bundle>` — View bundle metadata
- `bugsafe config --show` — Show current configuration
- `bugsafe mcp` — Start MCP server

## Exit Codes

- `0` — Success
- `1` — General error
- `2` — Bundle not found
- `3` — Validation failed
- `4` — Secrets found (scan/audit)

## Environment Variables

- `BUGSAFE_TIMEOUT` — Override default timeout (seconds)
- `BUGSAFE_FORMAT` — Override output format (md/json)

## Configuration

Config file: `~/.config/bugsafe/config.toml`

```toml
[defaults]
timeout = 300
max_output_size = 1048576

[output]
default_format = "md"
```

## Development

- `uv run pytest tests/ -v` — Run tests
- `uv run ruff check src/` — Lint
- `uv run mypy src/bugsafe/` — Type check

## MCP Tools

When MCP server is running, these tools are available:

- `scan_secrets` — Scan text for secrets
- `capture_crash` — Run command and capture output
- `render_bundle` — Render bundle to readable format
- `audit_bundle` — Verify redaction completeness
- `create_bundle` — Create a full bundle file

## MCP Configuration

Claude Desktop / Cursor / Windsurf:

```json
{"mcpServers": {"bugsafe": {"command": "uvx", "args": ["bugsafe", "mcp"]}}}
```

## Redaction Tokens

Secrets are replaced with tokens: `<API_KEY_1>`, `<TOKEN_2>`, etc.
Same secret = same token (correlation preserved).

## Code Style

- Python 3.10+ with type hints
- Follow SOLID principles
- No legacy/backwards compatibility code
- DRY while maintaining readability

## Project Structure

- `src/bugsafe/capture/` — Command execution
- `src/bugsafe/redact/` — Secret detection
- `src/bugsafe/bundle/` — Bundle format
- `src/bugsafe/render/` — Output rendering
- `src/bugsafe/mcp/` — MCP server
