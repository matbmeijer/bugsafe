# Programmatic API

Use bugsafe directly in your Python code for custom integrations.

## Basic Usage

```python
from bugsafe.redact import create_redaction_engine

# Create a redaction engine
engine = create_redaction_engine()

# Redact text
text = "API key: sk-abc123xyz"
redacted, report = engine.redact(text)

print(redacted)  # "API key: <API_KEY_1>"
print(report.get_total())  # 1
```

## Capture and Bundle

```python
from bugsafe.capture import capture_command
from bugsafe.bundle import create_bundle

# Capture a command
result = capture_command(["python", "my_script.py"], timeout=60)

# Create a bundle
bundle = create_bundle(result)

# Save to file
bundle.save("crash.bugbundle")
```

## Custom Patterns

```python
from bugsafe.redact import create_redaction_engine
from bugsafe.redact.patterns import create_custom_pattern, PatternConfig

# Create a custom pattern
my_pattern = create_custom_pattern(
    name="my_token",
    regex=r"myapp-[a-z0-9]{32}",
    category="MY_TOKEN",
)

# Configure with custom pattern
config = PatternConfig(custom_patterns=[my_pattern])
engine = create_redaction_engine(config=config)
```

## Render Output

```python
from bugsafe.bundle import BugBundle
from bugsafe.render import to_markdown, to_json, to_llm_context

# Load a bundle
bundle = BugBundle.load("crash.bugbundle")

# Render in different formats
markdown = to_markdown(bundle)
json_output = to_json(bundle)
llm_context = to_llm_context(bundle, max_tokens=4000)
```

## Next Steps

- [API Reference](../reference/api/redact.md) — Full API documentation
- [Custom Patterns](custom-patterns.md) — Advanced pattern configuration
