# Configuration

Configure bugsafe behavior via files or environment variables.

## Configuration File

Create `.bugsafe.toml` in your project root:

```toml
[redaction]
min_priority = "medium"
redact_emails = true
redact_ips = true
redact_uuids = false

[redaction.patterns]
disabled = ["UUID"]
custom = [
    { name = "internal_token", regex = "internal-[a-f0-9]{40}", category = "INTERNAL" },
]

[output]
default_format = "markdown"
llm_max_tokens = 4000

[capture]
default_timeout = 300
max_output_size = "10MB"
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `BUGSAFE_CONFIG` | Config file path | `.bugsafe.toml` |
| `BUGSAFE_NO_REDACT` | Disable redaction | `false` |
| `BUGSAFE_MIN_PRIORITY` | Minimum pattern priority | `optional` |

## Priority Levels

| Level | Value | Patterns Included |
|-------|-------|-------------------|
| `critical` | 100 | Private keys only |
| `high` | 80 | API keys, tokens |
| `medium` | 60 | Passwords, connection strings |
| `low` | 40 | Emails, IPs |
| `optional` | 20 | UUIDs (if enabled) |

## Precedence

Configuration is applied in order (later overrides earlier):

1. Built-in defaults
2. `.bugsafe.toml` in project root
3. `~/.config/bugsafe/config.toml` (user config)
4. Environment variables
5. CLI options

## See Also

- [Redaction Patterns](patterns.md)
- [Custom Patterns](../guides/custom-patterns.md)
