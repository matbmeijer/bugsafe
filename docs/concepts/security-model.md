# Security Model

bugsafe is designed with security as a primary concern. This document explains the threat model and security controls.

## Threat Model

| Threat | Mitigation |
|--------|------------|
| API keys in output | Pattern-based detection + tokenization |
| Passwords in logs | Password pattern matching |
| Private keys | PEM header detection |
| Usernames in paths | Path anonymization |
| Correlation attacks | Salted hashing per session |

## Security Controls

### 1. Pattern-Based Redaction

25+ patterns detect common secret formats:

- AWS keys (`AKIA...`)
- GitHub tokens (`ghp_...`)
- Stripe keys (`sk_live_...`)
- Private keys (`-----BEGIN...`)
- And more

### 2. Deterministic Tokenization

Secrets are replaced with tokens like `<API_KEY_1>`:

- Same secret → same token (within bundle)
- Different sessions → different tokens
- Non-reversible (hash-based)

### 3. Path Anonymization

File paths are sanitized:

```text
/Users/john/projects/app → <PROJECT>/app
/home/john/.ssh → <USER>/.ssh
```

### 4. Salt-Based Sessions

Each bundle uses a unique salt:

- Prevents cross-bundle correlation
- Only hash stored (original discarded)
- Salt hash in metadata for verification

## What Is NOT Redacted

- Generic variable values (unless matching patterns)
- Application-specific secrets without known patterns
- Custom tokens (add via custom patterns)

## Recommendations

1. **Review before sharing** — Always inspect bundles before sharing publicly
2. **Add custom patterns** — For project-specific secrets
3. **Use configuration** — Disable patterns you don't need
4. **CI integration** — Add bugsafe to your test pipeline

## Limitations

- **Regex-based** — Unknown formats may not be detected
- **Context-free** — Cannot understand semantic meaning
- **Best-effort** — Not a guarantee of complete redaction

## See Also

- [Redaction Patterns](../reference/patterns.md)
- [Custom Patterns](../guides/custom-patterns.md)
