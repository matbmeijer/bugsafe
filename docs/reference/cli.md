# CLI Reference

Complete reference for all bugsafe commands and options.

## Global Options

```bash
bugsafe [OPTIONS] COMMAND [ARGS]...
```

| Option | Description |
|--------|-------------|
| `--version` | Show version and exit |
| `--help` | Show help and exit |

## bugsafe run

Capture command execution and create a bundle.

```bash
bugsafe run [OPTIONS] -- COMMAND [ARGS]...
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `-o, --output` | PATH | Auto-generated | Output bundle path |
| `-t, --timeout` | INTEGER | None | Command timeout in seconds |
| `-a, --attach` | PATH | None | Attach file (repeatable) |
| `--no-redact` | FLAG | False | Disable redaction |

## bugsafe render

Render a bundle to various formats.

```bash
bugsafe render [OPTIONS] BUNDLE_PATH
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `-f, --format` | CHOICE | markdown | Output format: `markdown`, `json` |
| `--llm` | FLAG | False | Optimize for LLM context |
| `-o, --output` | PATH | stdout | Write to file |

## bugsafe inspect

View bundle metadata.

```bash
bugsafe inspect BUNDLE_PATH
```

## bugsafe config

Manage configuration.

```bash
bugsafe config COMMAND
```

### Subcommands

| Command | Description |
|---------|-------------|
| `show` | Display current configuration |
| `set KEY VALUE` | Set a configuration value |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Command timeout |
| 3 | Bundle read error |
