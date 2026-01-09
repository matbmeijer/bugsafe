# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **CLI Improvements**
  - Usage examples in `--help` for all commands
  - Standardized exit codes (`ExitCode` class): 0=success, 2=bundle not found, 4=secrets found
  - Verbose mode (`-v`) for `scan` command to show skipped files
  - Config file defaults for `run` command timeout and output directory
  - Environment variable overrides: `BUGSAFE_TIMEOUT`, `BUGSAFE_FORMAT`

- **Testing**
  - Integration tests for complete workflows (run → render → audit)
  - Property-based tests using Hypothesis for redaction safety
  - Edge case tests for unicode, long lines, nested secrets
  - 458 total tests (up from 437)

- **Security**
  - ReDoS prevention with pattern complexity limits (`MAX_PATTERN_LENGTH=1000`)
  - LRU-cached pattern compilation (`compile_pattern_safely()`)
  - Audit logging for bundle creation (`bugsafe.audit` logger)

- **Type Safety**
  - `py.typed` marker for PEP 561 compliance
  - Strict type annotations throughout

### Changed

- CLI timeout option now uses config file defaults (was hardcoded 300s)
- `scan` command exit code is now 4 (was 1) for consistency
- Bundle not found errors now return exit code 2 (was 1)

### Fixed

- Config loading errors now log warnings instead of failing silently
- CLI error messages include actionable suggestions
- Graceful cleanup of partial bundles on keyboard interrupt
- URL-encoded path traversal variants in bundle reader

### Internal

- Unified exception hierarchy in `bundle/exceptions.py`
- Single source of truth for redaction reporting (SOLID compliance)
- `create_redaction_engine` exported from main package
- Version consistency check in CI workflow

## [0.1.0] - 2024-01-15

### Added

- Initial release of bugsafe
- **Capture Engine**
  - Command execution with timeout support
  - stdout/stderr capture with size limits
  - Traceback parsing for Python exceptions
  - Environment snapshot (Python version, packages, git info)
- **Redaction Engine**
  - 25+ secret patterns (AWS, GitHub, Stripe, etc.)
  - Deterministic tokenization with correlation preservation
  - Path anonymization (home directories, temp files)
  - Configurable email/IP/UUID redaction
- **Bundle Format**
  - ZIP-based `.bugbundle` format
  - Pydantic schema validation
  - Integrity verification with checksums
  - Attachment support
- **Render Engine**
  - Markdown output for humans
  - JSON export for tools
  - LLM-optimized context with token budgeting
- **CLI**
  - `bugsafe run` - Capture command execution
  - `bugsafe render` - Render bundles to Markdown/JSON
  - `bugsafe inspect` - View bundle metadata
  - `bugsafe config` - Manage configuration
- **Testing**
  - 288 tests (unit, integration, property, fuzz)
  - 85% code coverage
  - Hypothesis property tests for redaction safety

### Security

- Automatic redaction of API keys, tokens, passwords
- Salt-based tokenization (only hash stored)
- Path traversal protection in bundle reader
- No shell=True in command execution

[Unreleased]: https://github.com/matbmeijer/bugsafe/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/matbmeijer/bugsafe/releases/tag/v0.1.0
