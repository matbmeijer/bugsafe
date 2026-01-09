# bugsafe Examples

Runnable examples demonstrating bugsafe usage.

## Examples

| Directory | Description |
|-----------|-------------|
| `basic/` | Simple crash capture and rendering |
| `automation/` | Slack notifications, GitHub issue creation |
| `ci-cd/` | GitHub Actions and GitLab CI workflows |

## Quick Start

```bash
cd examples/basic
bugsafe run -- python crash_demo.py
bugsafe render bug.bugbundle
```

## Pre-commit Integration

Add to your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/matbmeijer/bugsafe
    rev: v0.1.0
    hooks:
      - id: bugsafe-scan
```

## pytest Integration

```bash
pytest --bugsafe-on-fail
```

Creates a bundle in `.bugsafe/` on test failure.
