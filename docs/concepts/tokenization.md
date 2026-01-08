# Tokenization

Tokenization is the process of replacing secrets with deterministic, non-reversible tokens.

## Token Format

```text
<CATEGORY_N>
```

- **CATEGORY** — Type of secret (e.g., `API_KEY`, `AWS_SECRET`)
- **N** — Occurrence number for correlation

## Examples

| Original | Token |
|----------|-------|
| `sk-abc123xyz` | `<API_KEY_1>` |
| `AKIA1234567890` | `<AWS_KEY_1>` |
| `ghp_xxxxxxxxxxxx` | `<GITHUB_TOKEN_1>` |

## Correlation Preservation

The same secret always produces the same token within a bundle:

```text
Input:
  API_KEY=sk-secret123
  curl -H "Authorization: Bearer sk-secret123"

Output:
  API_KEY=<API_KEY_1>
  curl -H "Authorization: Bearer <API_KEY_1>"
```

This helps understand data flow without exposing values.

## How It Works

```text
secret + salt → hash → token_id → <CATEGORY_N>
```

1. **Salt** — Unique per session, prevents cross-bundle correlation
2. **Hash** — One-way transformation (SHA-256)
3. **Token ID** — Incrementing counter per category
4. **Token** — Human-readable placeholder

## Security Properties

| Property | Guarantee |
|----------|-----------|
| Non-reversible | Cannot recover original from token |
| Deterministic | Same input → same output (per session) |
| Session-isolated | Different sessions → different tokens |
| Collision-resistant | Different inputs → different tokens |

## API Usage

```python
from bugsafe.redact.tokenizer import Tokenizer

tokenizer = Tokenizer()

# Tokenize a secret
token = tokenizer.tokenize("sk-abc123", "API_KEY")
print(token)  # <API_KEY_1>

# Same secret = same token
token2 = tokenizer.tokenize("sk-abc123", "API_KEY")
assert token == token2

# Check if string is a token
assert tokenizer.is_token("<API_KEY_1>")
```

## See Also

- [Security Model](security-model.md)
- [Redaction Patterns](../reference/patterns.md)
