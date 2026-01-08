# Release Process

How releases are created and published.

## Overview

Releases are **fully automated** via GitHub Actions when a tag is pushed.

## Creating a Release

```bash
# 1. Ensure you're on main with latest changes
git checkout main
git pull origin main

# 2. Verify tests pass
uv run pytest tests/ -v
uv run mypy src/
uv run ruff check src/

# 3. Create annotated tag
git tag -a v0.2.0 -m "Release v0.2.0: Brief description"

# 4. Push tag (triggers automation)
git push origin v0.2.0
```

## What Happens Automatically

When a tag is pushed:

1. ✅ Tests run on multiple Python versions
2. ✅ Package built with version from tag
3. ✅ Published to PyPI
4. ✅ GitHub Release created
5. ✅ Documentation deployed

## Version Format

Follow [Semantic Versioning](https://semver.org/):

| Version | When to Use |
|---------|-------------|
| `v0.1.1` | Bug fixes only |
| `v0.2.0` | New features (backward compatible) |
| `v1.0.0` | Breaking changes |
| `v0.2.0-rc1` | Pre-release (TestPyPI only) |

## Pre-release Testing

Test on TestPyPI before stable release:

```bash
git tag -a v0.2.0-rc1 -m "Release candidate 1"
git push origin v0.2.0-rc1
```

This publishes to TestPyPI only.

## Hotfix Process

For urgent fixes:

```bash
git checkout main
git commit -m "fix: critical issue"
git tag -a v0.1.1 -m "Hotfix: Fix description"
git push origin main v0.1.1
```

## Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

```text
feat: add new redaction pattern
fix: handle empty traceback
docs: update CLI reference
test: add property tests
```

## See Also

- [Development Setup](development-setup.md)
- [Testing](testing.md)
