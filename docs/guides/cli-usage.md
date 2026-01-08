# CLI Usage

Comprehensive guide to using the bugsafe command-line interface.

## Commands Overview

| Command | Description |
|---------|-------------|
| `bugsafe run` | Capture command execution and create a bundle |
| `bugsafe render` | Render a bundle to Markdown, JSON, or LLM context |
| `bugsafe inspect` | View bundle metadata and summary |
| `bugsafe config` | Manage configuration |

## bugsafe run

Capture a command's output and create a redacted bundle.

```bash
bugsafe run [OPTIONS] -- COMMAND [ARGS]...
```

### Options

| Option | Description |
|--------|-------------|
| `-o, --output PATH` | Output bundle path |
| `-t, --timeout SECONDS` | Command timeout (default: no timeout) |
| `-a, --attach PATH` | Attach additional files |
| `--no-redact` | Disable redaction (not recommended) |

### Examples

```bash
# Basic usage
bugsafe run -- python my_script.py

# With output path
bugsafe run -o crash.bugbundle -- python my_script.py

# With timeout
bugsafe run -t 60 -- python long_running.py

# Attach log files
bugsafe run -a app.log -a config.yaml -- python my_script.py
```

## bugsafe render

Render a bundle in different formats.

```bash
bugsafe render [OPTIONS] BUNDLE_PATH
```

### Options

| Option | Description |
|--------|-------------|
| `-f, --format FORMAT` | Output format: `markdown`, `json` |
| `--llm` | Optimize for LLM context |
| `-o, --output PATH` | Write to file instead of stdout |

### Examples

```bash
# Markdown output (default)
bugsafe render crash.bugbundle

# JSON output
bugsafe render crash.bugbundle --format json

# LLM-optimized
bugsafe render crash.bugbundle --llm

# Save to file
bugsafe render crash.bugbundle -o report.md
```

## bugsafe inspect

View bundle metadata without full rendering.

```bash
bugsafe inspect BUNDLE_PATH
```

## bugsafe config

Manage bugsafe configuration.

```bash
# Show current config
bugsafe config show

# Set a value
bugsafe config set key value
```

## Next Steps

- [Programmatic API](programmatic-api.md) — Use bugsafe in Python code
- [CLI Reference](../reference/cli.md) — Complete option reference
