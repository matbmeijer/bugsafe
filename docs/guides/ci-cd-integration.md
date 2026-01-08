# CI/CD Integration

Use bugsafe in your continuous integration pipelines.

## GitHub Actions

```yaml
name: Tests with Crash Capture

on: [push, pull_request]

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
        run: bugsafe run -o crash.bugbundle -- pytest tests/
        continue-on-error: true

      - name: Upload crash bundle
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: crash-bundle
          path: crash.bugbundle
```

## GitLab CI

```yaml
test:
  script:
    - pip install bugsafe
    - bugsafe run -o crash.bugbundle -- pytest tests/
  artifacts:
    when: on_failure
    paths:
      - crash.bugbundle
```

## Best Practices

### 1. Capture Only on Failure

Use `continue-on-error` and conditional upload to avoid storing bundles for passing tests.

### 2. Set Timeouts

Prevent hanging tests from blocking CI:

```bash
bugsafe run -t 300 -- pytest tests/
```

### 3. Attach Logs

Include relevant log files in the bundle:

```bash
bugsafe run -a app.log -a /tmp/debug.log -- pytest tests/
```

### 4. Redaction Verification

The bundle automatically redacts secrets, but verify in sensitive environments:

```bash
bugsafe inspect crash.bugbundle
```

## Next Steps

- [CLI Usage](cli-usage.md) — Full command reference
- [Security Model](../concepts/security-model.md) — How redaction works
