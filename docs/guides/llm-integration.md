# LLM Integration

Optimize bugsafe output for AI assistants and language models.

## Why LLM-Optimized Output?

When sharing crash reports with LLMs:

- **Token efficiency** — Remove unnecessary verbosity
- **Context preservation** — Keep essential debugging info
- **Safety** — Secrets are already redacted

## CLI Usage

```bash
bugsafe render crash.bugbundle --llm
```

Output is optimized for pasting into ChatGPT, Claude, Copilot, etc.

## Programmatic Usage

```python
from bugsafe.bundle import BugBundle
from bugsafe.render import to_llm_context

bundle = BugBundle.load("crash.bugbundle")

# Default: 4000 tokens
context = to_llm_context(bundle)

# Custom token limit
context = to_llm_context(bundle, max_tokens=8000)
```

## What's Included

The LLM context prioritizes:

1. **Error message** — The actual exception
2. **Traceback** — Stack trace with file locations
3. **Command info** — What was run
4. **Environment** — Python version, key packages

## What's Excluded

To save tokens:

- Full stdout/stderr (summarized)
- All environment variables (only relevant ones)
- Attachment contents (mentioned but not included)

## Correlation Tokens

Secrets are replaced with consistent tokens:

```text
Original: API_KEY=sk-abc123 used in requests.get(..., headers={"Authorization": sk-abc123})
Redacted: API_KEY=<API_KEY_1> used in requests.get(..., headers={"Authorization": <API_KEY_1>})
```

This helps LLMs understand that the same secret appears in multiple places.

## Next Steps

- [Tokenization](../concepts/tokenization.md) — How correlation works
- [Security Model](../concepts/security-model.md) — What gets redacted
