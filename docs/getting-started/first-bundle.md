# Your First Bundle

This tutorial walks you through creating, inspecting, and sharing your first bug bundle.

## Prerequisites

- bugsafe installed (`pip install bugsafe`)
- A Python script that produces an error

## Step 1: Create a Failing Script

Create a file `demo.py`:

```python
import os

def connect_to_api():
    api_key = os.environ.get("API_KEY", "sk-test-abc123xyz789")
    print(f"Connecting with key: {api_key}")
    raise ConnectionError("Failed to connect to API")

if __name__ == "__main__":
    connect_to_api()
```

## Step 2: Capture the Crash

```bash
bugsafe run -- python demo.py
```

Output:

```
📦 Bundle created: demo_20240115_143022.bugbundle
   Redacted: 1 secret (API_KEY_1)
```

## Step 3: Inspect the Bundle

```bash
bugsafe inspect demo_20240115_143022.bugbundle
```

Notice how the API key has been replaced with `<API_KEY_1>`.

## Step 4: Render for Sharing

```bash
bugsafe render demo_20240115_143022.bugbundle
```

The output is safe to paste in GitHub issues, Slack, or send to an LLM.

## What Was Redacted?

bugsafe automatically detected and replaced:

- The API key `sk-test-abc123xyz789` → `<API_KEY_1>`
- Any matching secrets in environment variables
- Sensitive file paths

## Next Steps

- [Custom Patterns](../guides/custom-patterns.md) — Add your own redaction rules
- [LLM Integration](../guides/llm-integration.md) — Optimize output for AI assistants
