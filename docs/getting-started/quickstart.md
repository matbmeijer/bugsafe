# Quick Start

Get up and running with bugsafe in 5 minutes.

## Capture a Crash

Run any Python command through bugsafe to capture its output:

```bash
bugsafe run -- python my_script.py
```

This creates a `.bugbundle` file containing:

- Captured stdout/stderr
- Parsed traceback
- Environment info (Python version, packages, git info)
- **All secrets automatically redacted**

## Inspect the Bundle

```bash
bugsafe inspect crash.bugbundle
```

## Render for Sharing

```bash
# Markdown for humans
bugsafe render crash.bugbundle

# JSON for tools
bugsafe render crash.bugbundle --format json

# Optimized for LLMs
bugsafe render crash.bugbundle --llm
```

## Next Steps

- [Your First Bundle](first-bundle.md) — Detailed walkthrough
- [CLI Usage](../guides/cli-usage.md) — Full CLI reference
- [Redaction Patterns](../reference/patterns.md) — What gets redacted
