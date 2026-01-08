---
title: bugsafe - Safe-to-share crash bundles for Python
description: Automatically redact secrets from Python crash reports. Share debugging info without exposing API keys, tokens, or passwords.
---

# bugsafe

**Safe-to-share crash bundles for humans and LLMs.**

bugsafe captures Python crashes and creates redacted, shareable bug reports. It automatically removes API keys, tokens, passwords, and other secrets while preserving the information needed to debug issues.

## Features

- **Automatic secret redaction** — 25+ patterns for API keys, tokens, passwords, connection strings
- **Correlation preservation** — Same secret → same token throughout the bundle
- **Path anonymization** — Removes usernames and sensitive paths
- **Rich environment capture** — Python version, packages, git info, environment variables
- **Multiple output formats** — Markdown for humans, JSON for tools, LLM-optimized context
- **Zero configuration** — Works out of the box with sensible defaults

## Quick Start

### Installation

```bash
pip install bugsafe
```

### Capture a Crash

```bash
bugsafe run -- python my_script.py
```

### Render for Sharing

```bash
# Markdown for humans
bugsafe render crash.bugbundle

# Optimized for LLMs
bugsafe render crash.bugbundle --llm
```

## Example Output

```text
# Bug Report: demo.py

## Error
ConnectionError: Failed to connect to <API_HOST_1>

## Traceback
File "<PROJECT>/app.py", line 42, in connect
    response = requests.get(url, headers={"Authorization": <API_KEY_1>})

## Environment
- Python: 3.12.0
- Platform: linux
- Packages: requests==2.31.0, pydantic==2.5.0
```

Notice how secrets are replaced with tokens like `<API_KEY_1>` while preserving correlation.

## Next Steps

<div class="grid cards" markdown>

- :material-download: **[Installation](getting-started/installation.md)**

    Get bugsafe installed in your environment

- :material-rocket-launch: **[Quick Start](getting-started/quickstart.md)**

    Create your first crash bundle in 5 minutes

- :material-shield-check: **[Security Model](concepts/security-model.md)**

    Learn how bugsafe protects your secrets

- :material-api: **[API Reference](reference/api/redact.md)**

    Use bugsafe programmatically

</div>
