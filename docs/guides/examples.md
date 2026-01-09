# Examples

Runnable examples demonstrating bugsafe in real-world scenarios.

## Basic Usage

### Crash Demo

A script that crashes with secrets in output, demonstrating redaction.

**File:** `examples/basic/crash_demo.py`

```python
"""Demo script that crashes with secrets in output."""
import os

def fetch_data(api_key: str, endpoint: str) -> dict:
    """Simulate API call that fails."""
    print(f"Connecting to {endpoint}...")
    print(f"Using API key: {api_key}")
    raise ConnectionError(f"Failed to connect to {endpoint} with key {api_key}")

def main() -> None:
    api_key = os.getenv("API_KEY", "sk-proj-abc123xyz789secret")
    endpoint = "https://api.example.com/v1/data"
    fetch_data(api_key, endpoint)

if __name__ == "__main__":
    main()
```

**Run:**

```bash
bugsafe run -- python examples/basic/crash_demo.py
bugsafe render bug.bugbundle
```

**Expected output:** The API key `sk-proj-abc123xyz789secret` is redacted to `<API_KEY_1>`.

---

## Automation

### Slack Notifications

Post crash bundles to Slack when a command fails.

**File:** `examples/automation/slack_notify.py`

**Setup:**

```bash
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
```

**Usage:**

```bash
python examples/automation/slack_notify.py "python my_script.py"
```

**How it works:**

1. Runs the command with `bugsafe run`
2. If the command fails, renders the bundle with `--llm` flag
3. Posts the redacted summary to Slack

### GitHub Issue Creation

Automatically create GitHub issues from crash bundles.

**File:** `examples/automation/github_issue.py`

**Setup:**

```bash
export GITHUB_TOKEN="ghp_..."
```

**Usage:**

```bash
python examples/automation/github_issue.py owner/repo crash.bugbundle
```

**How it works:**

1. Renders the bundle to markdown
2. Creates a GitHub issue with `bug` and `crash` labels
3. Returns the issue URL

---

## CI/CD Integration

### GitHub Actions

Complete workflow that captures crashes on test failure.

**File:** `examples/ci-cd/github-actions.yml`

```yaml
name: Tests with Crash Capture

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: |
          pip install bugsafe
          pip install -e .

      - name: Run tests with bugsafe
        id: tests
        run: bugsafe run -o crash.bugbundle -- pytest tests/ -v
        continue-on-error: true

      - name: Upload crash bundle
        if: steps.tests.outcome == 'failure'
        uses: actions/upload-artifact@v4
        with:
          name: crash-bundle
          path: crash.bugbundle
          retention-days: 7

      - name: Add bundle to job summary
        if: steps.tests.outcome == 'failure'
        run: |
          echo "## Crash Report" >> $GITHUB_STEP_SUMMARY
          bugsafe render crash.bugbundle --llm >> $GITHUB_STEP_SUMMARY

      - name: Fail if tests failed
        if: steps.tests.outcome == 'failure'
        run: exit 1
```

**Features:**

- Captures test output with bugsafe
- Uploads bundle as artifact on failure
- Adds rendered bundle to job summary
- Preserves original exit code

### GitLab CI

Minimal pipeline configuration for GitLab.

**File:** `examples/ci-cd/gitlab-ci.yml`

```yaml
stages:
  - test

test:
  stage: test
  image: python:3.12-slim

  before_script:
    - pip install bugsafe
    - pip install -e .

  script:
    - bugsafe run -o crash.bugbundle -- pytest tests/ -v

  artifacts:
    when: on_failure
    paths:
      - crash.bugbundle
    expire_in: 7 days
```

**Features:**

- Uploads bundle only on failure
- 7-day artifact retention
- Minimal configuration

---

## pytest Integration

Use the built-in pytest plugin for automatic capture.

```bash
pytest --bugsafe-on-fail
```

Creates a bundle in `.bugsafe/` directory on test failure.

**Options:**

- `--bugsafe` — Capture all test output
- `--bugsafe-on-fail` — Capture only on failure
- `--bugsafe-output <dir>` — Custom output directory

---

## Pre-commit Hook

Scan for secrets before committing.

Add to `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/matbmeijer/bugsafe
    rev: v0.1.0
    hooks:
      - id: bugsafe-scan
```

---

## See Also

- [CI/CD Integration Guide](ci-cd-integration.md)
- [LLM Integration Guide](llm-integration.md)
- [CLI Reference](../reference/cli.md)
