---
title: Security Model (Legacy)
---

!!! warning "Legacy Documentation"
    This page has been superseded by the new documentation structure.
    See **[Security Model](concepts/security-model.md)** for the current version.

# Security Model

This document describes the security model, assumptions, and limitations of bugsafe.

## Overview

bugsafe is designed to create **safe-to-share** crash bundles by automatically redacting sensitive information from command output. The goal is to enable developers to share debugging information without exposing secrets.

## Security Goals

1. **Prevent secret leakage** - Remove API keys, tokens, passwords, and other sensitive data
2. **Preserve debugging utility** - Keep enough information to diagnose issues
3. **Deterministic correlation** - Same secret → same token for traceability
4. **Non-reversible** - Cannot recover original secrets from tokens

## Threat Model

### In Scope

| Threat | Mitigation |
|--------|------------|
| API keys in output | Pattern matching for 25+ secret formats |
| Database credentials | Connection string patterns |
| Private keys | PEM header/footer detection |
| Email addresses | Email pattern matching (configurable) |
| IP addresses | IPv4/IPv6 patterns (configurable) |
| File paths | Path anonymization (home, user, temp dirs) |
| Environment variables | Blocklist of sensitive variables |

### Out of Scope

| Threat | Reason |
|--------|--------|
| Custom secret formats | Users must add custom patterns |
| Secrets in binary data | Only text is processed |
| Side-channel attacks | Not designed for adversarial use |
| Encrypted secrets | Cannot detect encrypted data |

## Security Architecture

### Redaction Pipeline

```
Input Text
    │
    ▼
┌─────────────────┐
│ Pattern Matching│ ← 25+ regex patterns
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Tokenization   │ ← Deterministic, salted
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Path Anonymizer │ ← Replace sensitive paths
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Verification   │ ← Check for remaining secrets
└────────┬────────┘
         │
         ▼
   Redacted Output
```

### Salt Handling

- Each redaction session uses a cryptographically random salt
- Only the SHA-256 hash of the salt is stored in the bundle
- The salt itself is never persisted
- Same salt = same tokens (for correlation within a bundle)

### Pattern Priorities

| Priority | Category | Examples |
|----------|----------|----------|
| CRITICAL | Private keys, credentials | PEM keys, passwords |
| HIGH | API keys, tokens | AWS, GitHub, Slack tokens |
| MEDIUM | Generic secrets | api_key=, password= patterns |
| LOW | Network info | IP addresses |
| OPTIONAL | Personal info | Email addresses |
| DISABLED | High false-positive | UUIDs |

## Security Controls

### Input Validation

- Command arguments passed directly (no shell interpretation)
- Bundle paths validated for traversal attacks
- ZIP entries checked for path traversal (`../`)
- Maximum file sizes enforced

### Output Sanitization

- All text output passes through redaction engine
- Environment variables filtered through blocklist
- File paths anonymized to remove usernames

### Timeout Protection

- Regex patterns have configurable timeout (default: 100ms)
- Prevents catastrophic backtracking DoS
- Timed-out patterns logged as warnings

## Limitations

### False Negatives (Missed Secrets)

bugsafe may miss secrets in these cases:

1. **Custom formats** - Proprietary token formats not in pattern list
2. **Obfuscated secrets** - Base64-encoded or encrypted secrets
3. **Context-dependent** - Secrets only identifiable by context
4. **New patterns** - Recently introduced token formats

**Mitigation:** Always review bundles before sharing. Use `bugsafe inspect` to check redaction summary.

### False Positives

bugsafe may incorrectly redact:

1. **UUID-like IDs** - Disabled by default
2. **Email-like strings** - Configurable
3. **IP-like numbers** - Configurable
4. **Long alphanumeric strings** - May match generic patterns

**Mitigation:** Use `--no-redact` for trusted environments or adjust pattern configuration.

## Security Checklist

Before sharing a bundle, verify:

- [ ] Run `bugsafe inspect <bundle>` to review redaction summary
- [ ] Check that expected secret categories were detected
- [ ] Review redacted output for any remaining sensitive data
- [ ] Consider audience before sharing (internal vs public)

## Incident Response

If you discover a secret was not redacted:

1. **Delete** the shared bundle immediately
2. **Rotate** the exposed credential
3. **Report** the pattern gap (see Contributing)
4. **Update** your bugsafe version

## Reporting Security Issues

Please report security vulnerabilities via:

1. GitHub Security Advisories (preferred)
2. Email to maintainers (for critical issues)

Do NOT open public issues for security vulnerabilities.

## Compliance Notes

- bugsafe processes data locally; no external services
- No telemetry or data collection
- Bundles are self-contained files you control
- Salt hashes cannot be used to recover secrets

## Version History

| Version | Security Changes |
|---------|-----------------|
| 0.1.0 | Initial security model |
