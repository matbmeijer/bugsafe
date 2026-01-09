---
description: Redaction engine implementation details
paths: src/bugsafe/redact/**/*.py
---

# Redaction Engine

## Pattern Priority

- High priority patterns (API keys, tokens) run first
- Use capture groups to extract only the secret portion
- Minimum secret length: 4 characters

## Tokenization

- Tokens are deterministic within a session (same salt)
- Format: `<CATEGORY_N>` where N is occurrence order
- Token format must not match any secret patterns

## Path Anonymization

- Replace home directory with `~`
- Replace project root with `<PROJECT>`
- Preserve relative path structure

## Performance

- Use `signal.setitimer` for pattern timeout (Unix only)
- Skip patterns that don't apply based on config
- Process high-priority patterns first

## Testing Patterns

- Test both positive matches and false positive avoidance
- Include edge cases: empty strings, unicode, very long input
- Verify token determinism across multiple calls
