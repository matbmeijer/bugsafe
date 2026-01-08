# How It Works

bugsafe creates safe-to-share crash bundles by capturing, redacting, and packaging debugging information.

## Pipeline Overview

```text
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Capture   │ -> │   Redact    │ -> │   Bundle    │ -> │   Render    │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

## 1. Capture

When you run `bugsafe run -- python script.py`:

1. **Command execution** — Spawns the command as a subprocess
2. **Output capture** — Collects stdout and stderr
3. **Traceback parsing** — Extracts Python exception details
4. **Environment snapshot** — Captures Python version, packages, git info

## 2. Redact

Before storing anything:

1. **Pattern matching** — Scans text for 25+ secret patterns
2. **Tokenization** — Replaces secrets with deterministic tokens
3. **Path anonymization** — Removes usernames from file paths
4. **Correlation preservation** — Same secret = same token

## 3. Bundle

Creates a `.bugbundle` file (ZIP format):

```text
crash.bugbundle
├── manifest.json      # Metadata and checksums
├── traceback.json     # Parsed exception
├── environment.json   # System info
├── output.txt         # Captured stdout/stderr
└── attachments/       # Additional files
```

## 4. Render

Outputs the bundle in various formats:

- **Markdown** — Human-readable for GitHub issues
- **JSON** — Machine-readable for tools
- **LLM Context** — Token-optimized for AI assistants

## Key Principles

### Privacy by Default

All sensitive data is redacted before storage. The original secrets are never written to disk.

### Correlation Preservation

The same secret produces the same token within a bundle:

```text
API_KEY=sk-abc123 → <API_KEY_1>
headers={"auth": "sk-abc123"} → headers={"auth": "<API_KEY_1>"}
```

This helps debuggers understand relationships without exposing the actual values.

### Non-Reversible

Tokens cannot be reversed to the original value. Only a salted hash is stored for verification.

## See Also

- [Security Model](security-model.md)
- [Tokenization](tokenization.md)
- [Bundle Format](bundle-format.md)
