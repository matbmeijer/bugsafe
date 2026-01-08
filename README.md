<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/assets/logo-white.svg">
    <source media="(prefers-color-scheme: light)" srcset="docs/assets/logo.svg">
    <img src="docs/assets/logo.svg" alt="bugsafe logo" width="200" height="200">
  </picture>
</p>

<h1 align="center">bugsafe</h1>

<p align="center">
  <strong>Safe-to-share crash bundles for humans and LLMs</strong>
</p>

<p align="center">
  <a href="https://github.com/matbmeijer/bugsafe/actions/workflows/ci.yml"><img src="https://github.com/matbmeijer/bugsafe/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://badge.fury.io/py/bugsafe"><img src="https://badge.fury.io/py/bugsafe.svg" alt="PyPI version"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python 3.10+"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
  <a href="https://matbmeijer.github.io/bugsafe/"><img src="https://img.shields.io/badge/docs-latest-blue.svg" alt="Documentation"></a>
</p>

---

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

### Example Output

```text
# Bug Report: my_script.py

## Error
ValueError: Invalid API response

## Traceback
File "<PROJECT>/my_script.py", line 25, in main
    result = api.fetch(url, headers={"Authorization": <API_KEY_1>})

## Redaction Summary
- API_KEY: 2 redacted
- EMAIL: 1 redacted
```

Notice how secrets are replaced with tokens like `<API_KEY_1>` while preserving correlation.

## Documentation

📚 **[Full Documentation](https://matbmeijer.github.io/bugsafe/)**

| Section | Description |
|---------|-------------|
| [Getting Started](https://matbmeijer.github.io/bugsafe/getting-started/installation/) | Installation and first bundle |
| [CLI Reference](https://matbmeijer.github.io/bugsafe/reference/cli/) | Complete command reference |
| [API Reference](https://matbmeijer.github.io/bugsafe/reference/api/redact/) | Programmatic usage |
| [Redaction Patterns](https://matbmeijer.github.io/bugsafe/reference/patterns/) | What gets redacted |
| [Security Model](https://matbmeijer.github.io/bugsafe/concepts/security-model/) | How bugsafe protects secrets |
| [Configuration](https://matbmeijer.github.io/bugsafe/reference/configuration/) | Config file options |

## What Gets Redacted

bugsafe automatically detects and redacts:

| Category | Examples |
|----------|----------|
| **API Keys** | AWS (`AKIA...`), Google Cloud, Azure |
| **Tokens** | GitHub (`ghp_...`), GitLab, Slack, Discord |
| **Credentials** | Passwords, Basic Auth, Bearer tokens |
| **Connection Strings** | PostgreSQL, MySQL, MongoDB, Redis URLs |
| **Private Keys** | RSA, DSA, EC, OpenSSH keys |
| **Paths** | Home directories, usernames, temp files |

See [Redaction Patterns](https://matbmeijer.github.io/bugsafe/reference/patterns/) for the complete list.

## Security

bugsafe is designed to make crash reports safe to share, but:

- **Always review** bundles before sharing publicly
- **Custom secrets** may not be detected — add custom patterns if needed
- **Binary data** is not processed — only text output is redacted

See [Security Model](https://matbmeijer.github.io/bugsafe/concepts/security-model/) for details.

## Contributing

Contributions are welcome! See [Contributing Guide](https://matbmeijer.github.io/bugsafe/contributing/development-setup/) for development setup.

```bash
git clone https://github.com/matbmeijer/bugsafe.git
cd bugsafe
uv sync
uv run pytest
```

## License

MIT License. See [LICENSE](LICENSE) for details.
