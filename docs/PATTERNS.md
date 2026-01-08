---
title: Redaction Patterns (Legacy)
---

!!! warning "Legacy Documentation"
    This page has been superseded by the new documentation structure.
    See **[Redaction Patterns](reference/patterns.md)** for the current version.

# Redaction Patterns

This document describes all secret patterns that bugsafe detects and redacts.

## Pattern Priorities

Patterns are organized by priority level:

| Priority | Value | Description |
|----------|-------|-------------|
| **CRITICAL** | 100 | Always redacted, highest confidence |
| **HIGH** | 80 | Strong indicators of secrets |
| **MEDIUM** | 60 | Likely secrets, some false positives possible |
| **LOW** | 40 | Network/system info, configurable |
| **OPTIONAL** | 20 | Personal info, off by default |
| **DISABLED** | 0 | High false-positive rate, must enable explicitly |

## Cloud Provider Keys

### AWS

| Pattern | Priority | Example |
|---------|----------|---------|
| `aws_access_key` | CRITICAL | `AKIAIOSFODNN7EXAMPLE` |
| `aws_secret_key` | CRITICAL | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` |

**Regex:** `AKIA[A-Z0-9]{16}`

### Google Cloud

| Pattern | Priority | Example |
|---------|----------|---------|
| `gcp_api_key` | HIGH | `AIzaSyC...` |
| `gcp_service_account` | CRITICAL | JSON with `"type": "service_account"` |

### Azure

| Pattern | Priority | Example |
|---------|----------|---------|
| `azure_storage_key` | HIGH | Base64 storage account keys |
| `azure_connection_string` | HIGH | `DefaultEndpointsProtocol=...` |

## Version Control Tokens

### GitHub

| Pattern | Priority | Example |
|---------|----------|---------|
| `github_pat` | CRITICAL | `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` |
| `github_oauth` | CRITICAL | `gho_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` |
| `github_app` | CRITICAL | `ghu_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` |
| `github_refresh` | CRITICAL | `ghr_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` |

**Regex:** `gh[pousr]_[A-Za-z0-9]{36}`

### GitLab

| Pattern | Priority | Example |
|---------|----------|---------|
| `gitlab_pat` | CRITICAL | `glpat-xxxxxxxxxxxxxxxxxxxx` |
| `gitlab_runner` | HIGH | `GR1348941...` |

### Bitbucket

| Pattern | Priority | Example |
|---------|----------|---------|
| `bitbucket_app_password` | HIGH | App passwords in Basic Auth |

## Communication Platforms

### Slack

| Pattern | Priority | Example |
|---------|----------|---------|
| `slack_token` | CRITICAL | `xoxb-...`, `xoxp-...`, `xoxa-...` |
| `slack_webhook` | HIGH | `https://hooks.slack.com/services/...` |

**Regex:** `xox[bpas]-[A-Za-z0-9-]+`

### Discord

| Pattern | Priority | Example |
|---------|----------|---------|
| `discord_token` | CRITICAL | Bot tokens, webhook URLs |
| `discord_webhook` | HIGH | `https://discord.com/api/webhooks/...` |

### Twilio

| Pattern | Priority | Example |
|---------|----------|---------|
| `twilio_api_key` | HIGH | `SK...` |
| `twilio_auth_token` | CRITICAL | 32-character hex strings |

## Payment Providers

### Stripe

| Pattern | Priority | Example |
|---------|----------|---------|
| `stripe_secret` | CRITICAL | `sk_live_...`, `sk_test_...` |
| `stripe_publishable` | MEDIUM | `pk_live_...`, `pk_test_...` |
| `stripe_restricted` | HIGH | `rk_live_...`, `rk_test_...` |

**Regex:** `[sr]k_(live|test)_[A-Za-z0-9]{24,}`

### PayPal

| Pattern | Priority | Example |
|---------|----------|---------|
| `paypal_client_id` | HIGH | Client IDs |
| `paypal_secret` | CRITICAL | Client secrets |

## Database Connection Strings

| Pattern | Priority | Example |
|---------|----------|---------|
| `postgres_url` | HIGH | `postgres://user:pass@host:5432/db` |
| `mysql_url` | HIGH | `mysql://user:pass@host:3306/db` |
| `mongodb_url` | HIGH | `mongodb://user:pass@host:27017/db` |
| `redis_url` | HIGH | `redis://:password@host:6379/0` |

**Note:** Passwords in connection strings are always redacted.

## Authentication

### JWT Tokens

| Pattern | Priority | Example |
|---------|----------|---------|
| `jwt` | HIGH | `eyJhbGciOiJIUzI1NiIs...` (3-part base64) |

**Regex:** `eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+`

### OAuth/Bearer

| Pattern | Priority | Example |
|---------|----------|---------|
| `bearer_token` | HIGH | `Authorization: Bearer xxx...` |
| `basic_auth` | HIGH | `Authorization: Basic xxx...` |

### API Keys (Generic)

| Pattern | Priority | Example |
|---------|----------|---------|
| `api_key_generic` | MEDIUM | `api_key = "sk_..."`, `API_KEY: ...` |
| `password_generic` | MEDIUM | `password = "..."`, `passwd: ...` |
| `secret_generic` | MEDIUM | `secret = "..."`, `SECRET_KEY: ...` |

## Cryptographic Keys

### Private Keys

| Pattern | Priority | Example |
|---------|----------|---------|
| `private_key_rsa` | CRITICAL | `-----BEGIN RSA PRIVATE KEY-----` |
| `private_key_dsa` | CRITICAL | `-----BEGIN DSA PRIVATE KEY-----` |
| `private_key_ec` | CRITICAL | `-----BEGIN EC PRIVATE KEY-----` |
| `private_key_openssh` | CRITICAL | `-----BEGIN OPENSSH PRIVATE KEY-----` |
| `private_key_generic` | CRITICAL | `-----BEGIN PRIVATE KEY-----` |
| `private_key_encrypted` | CRITICAL | `-----BEGIN ENCRYPTED PRIVATE KEY-----` |

**Note:** The entire key block (header to footer) is redacted.

## Network Information

### IP Addresses

| Pattern | Priority | Default |
|---------|----------|---------|
| `ip_private` | LOW | Enabled |
| `ip_public` | LOW | Enabled |

**Private ranges:** `10.x.x.x`, `172.16-31.x.x`, `192.168.x.x`, `127.x.x.x`

**Configuration:**
```toml
[redaction]
redact_ips = true  # or false to disable
```

## Personal Information

### Email Addresses

| Pattern | Priority | Default |
|---------|----------|---------|
| `email` | OPTIONAL | Enabled |

**Regex:** `[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}`

**Configuration:**
```toml
[redaction]
redact_emails = true  # or false to disable
```

### UUIDs

| Pattern | Priority | Default |
|---------|----------|---------|
| `uuid` | DISABLED | Disabled |

**Regex:** `[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}`

**Note:** UUIDs have high false-positive rate. Enable explicitly:
```toml
[redaction]
redact_uuids = true
```

## Path Anonymization

In addition to secret patterns, bugsafe anonymizes sensitive paths:

| Original | Replacement |
|----------|-------------|
| `/home/username/...` | `<USER>/...` |
| `/Users/username/...` | `<USER>/...` |
| `/tmp/...` | `<TMPDIR>/...` |
| `/var/folders/...` | `<TMPDIR>/...` |
| `.../site-packages/...` | `<SITE_PACKAGES>/...` |
| `.../.venv/...` | `<VENV>/...` |

## Token Format

When a secret is redacted, it's replaced with a token:

```
<CATEGORY_N>
```

Where:
- `CATEGORY` is the secret type (e.g., `AWS_KEY`, `GITHUB_TOKEN`)
- `N` is a sequential number for correlation

**Example:**
```
Original: API key is AKIAIOSFODNN7EXAMPLE, also AKIAIOSFODNN7EXAMPLE
Redacted: API key is <AWS_KEY_1>, also <AWS_KEY_1>
```

The same secret always gets the same token within a bundle, enabling correlation.

## Adding Custom Patterns

Custom patterns can be added via YAML configuration:

```yaml
# ~/.config/bugsafe/patterns.yaml
patterns:
  - name: my_internal_token
    regex: "MYCO_[A-Z0-9]{32}"
    category: INTERNAL_TOKEN
    priority: high
    description: "My Company Internal Token"
```

Then reference in config:
```toml
[redaction]
custom_patterns = "~/.config/bugsafe/patterns.yaml"
```

## Pattern Testing

Test patterns against sample text:

```python
from bugsafe.redact.engine import create_redaction_engine

engine = create_redaction_engine()
text = "My key is AKIAIOSFODNN7EXAMPLE"
result, report = engine.redact(text)

print(result)  # "My key is <AWS_KEY_1>"
print(report.categories)  # {"AWS_KEY": 1}
```

## False Positives

Some patterns may occasionally match non-secrets. Strategies:

1. **Review output** — Always check bundles before sharing
2. **Adjust priority** — Lower priority patterns can be disabled
3. **Disable categories** — Turn off emails, IPs, or UUIDs if needed
4. **Use `--no-redact`** — Skip redaction entirely for trusted environments
