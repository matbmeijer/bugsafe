# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
