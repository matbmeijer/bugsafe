# Redaction Patterns

Complete list of built-in secret detection patterns.

## Pattern Categories

### Cloud Provider Keys

| Pattern | Category | Priority | Example |
|---------|----------|----------|---------|
| AWS Access Key | `AWS_KEY` | Critical | `AKIA...` |
| AWS Secret Key | `AWS_SECRET` | Critical | `wJalr...` |
| GCP API Key | `GCP_KEY` | High | `AIza...` |
| Azure Connection String | `AZURE_CONN` | High | `DefaultEndpointsProtocol=...` |

### Version Control

| Pattern | Category | Priority | Example |
|---------|----------|----------|---------|
| GitHub Token | `GITHUB_TOKEN` | Critical | `ghp_...`, `gho_...` |
| GitLab Token | `GITLAB_TOKEN` | High | `glpat-...` |
| Bitbucket Token | `BITBUCKET_TOKEN` | High | `ATBB...` |

### Communication Platforms

| Pattern | Category | Priority | Example |
|---------|----------|----------|---------|
| Slack Token | `SLACK_TOKEN` | High | `xoxb-...`, `xoxp-...` |
| Discord Token | `DISCORD_TOKEN` | High | `NjE...` |
| Twilio SID | `TWILIO_SID` | High | `AC...` |

### Payment Providers

| Pattern | Category | Priority | Example |
|---------|----------|----------|---------|
| Stripe API Key | `STRIPE_KEY` | Critical | `sk_live_...`, `sk_test_...` |
| PayPal Client ID | `PAYPAL_ID` | High | Long alphanumeric |

### Database

| Pattern | Category | Priority | Example |
|---------|----------|----------|---------|
| PostgreSQL URL | `DB_URL` | High | `postgresql://user:pass@host/db` |
| MongoDB URL | `MONGO_URL` | High | `mongodb://...` |
| Redis URL | `REDIS_URL` | High | `redis://...` |

### Authentication

| Pattern | Category | Priority | Example |
|---------|----------|----------|---------|
| JWT | `JWT` | High | `eyJ...` |
| Bearer Token | `BEARER` | High | `Bearer ...` |
| Basic Auth | `BASIC_AUTH` | High | `Basic ...` |

### Cryptographic

| Pattern | Category | Priority | Example |
|---------|----------|----------|---------|
| Private Key | `PRIVATE_KEY` | Critical | `-----BEGIN RSA PRIVATE KEY-----` |
| SSH Key | `SSH_KEY` | Critical | `-----BEGIN OPENSSH PRIVATE KEY-----` |

### Personal Information

| Pattern | Category | Priority | Example |
|---------|----------|----------|---------|
| Email | `EMAIL` | Low | `user@example.com` |
| IP Address | `IP` | Low | `192.168.1.1` |
| UUID | `UUID` | Optional | `550e8400-e29b-...` |

## Token Format

Redacted secrets are replaced with tokens:

```text
<CATEGORY_N>
```

Where:
- `CATEGORY` — Pattern category (e.g., `AWS_KEY`)
- `N` — Occurrence number (for correlation)

## Disabling Patterns

```python
from bugsafe.redact.patterns import PatternConfig

config = PatternConfig(
    disabled_patterns={"EMAIL", "UUID"},
    redact_emails=False,
    redact_ips=False,
)
```

## See Also

- [Custom Patterns](../guides/custom-patterns.md)
- [Security Model](../concepts/security-model.md)
