# Custom Patterns

Add your own redaction patterns for project-specific secrets.

## Creating a Pattern

```python
from bugsafe.redact.patterns import create_custom_pattern, Priority

pattern = create_custom_pattern(
    name="my_internal_token",
    regex=r"internal-[a-f0-9]{40}",
    category="INTERNAL_TOKEN",
    priority=Priority.HIGH,
    description="Internal service tokens",
)
```

## Pattern Components

| Field | Description |
|-------|-------------|
| `name` | Unique identifier |
| `regex` | Python regular expression |
| `category` | Token category (appears in output as `<CATEGORY_N>`) |
| `priority` | Detection priority (higher = checked first) |
| `capture_group` | Which regex group contains the secret (0 = full match) |

## Priority Levels

| Priority | Value | Use Case |
|----------|-------|----------|
| `CRITICAL` | 100 | Must never leak (private keys) |
| `HIGH` | 80 | API keys, tokens |
| `MEDIUM` | 60 | Passwords, connection strings |
| `LOW` | 40 | Email addresses, IPs |
| `OPTIONAL` | 20 | Context-dependent |

## Using Custom Patterns

```python
from bugsafe.redact import create_redaction_engine
from bugsafe.redact.patterns import PatternConfig

config = PatternConfig(
    custom_patterns=[my_pattern],
    min_priority=Priority.MEDIUM,  # Skip LOW patterns
)

engine = create_redaction_engine(config=config)
```

## Configuration File

Create `.bugsafe.toml` in your project:

```toml
[patterns]
custom = [
    { name = "internal_token", regex = "internal-[a-f0-9]{40}", category = "INTERNAL" },
]
disabled = ["EMAIL"]  # Disable email redaction
```

## Next Steps

- [Redaction Patterns Reference](../reference/patterns.md) — All built-in patterns
- [Security Model](../concepts/security-model.md) — How redaction works
