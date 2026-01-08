"""Pattern registry - Secret detection patterns for redaction."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import IntEnum


class Priority(IntEnum):
    """Pattern priority levels."""

    CRITICAL = 100
    HIGH = 90
    MEDIUM = 80
    LOW = 70
    OPTIONAL = 60
    DISABLED = 0


@dataclass(frozen=True)
class Pattern:
    """A secret detection pattern.

    Attributes:
        name: Unique identifier for the pattern.
        regex: Compiled regular expression.
        category: Category for token naming (e.g., AWS_KEY, EMAIL).
        priority: Pattern priority (higher = more important).
        capture_group: Which regex group contains the secret (0 = full match).
        description: Human-readable description.
    """

    name: str
    regex: re.Pattern[str]
    category: str
    priority: int = Priority.HIGH
    capture_group: int = 0
    description: str = ""

    def __hash__(self) -> int:
        return hash(self.name)


@dataclass
class PatternConfig:
    """Configuration for pattern matching.

    Attributes:
        enabled_patterns: Set of pattern names to enable (None = all).
        disabled_patterns: Set of pattern names to disable.
        custom_patterns: Additional custom patterns.
        min_priority: Minimum priority threshold.
        redact_emails: Whether to redact email addresses.
        redact_ips: Whether to redact IP addresses.
        redact_uuids: Whether to redact UUIDs.
    """

    enabled_patterns: set[str] | None = None
    disabled_patterns: set[str] = field(default_factory=set)
    custom_patterns: list[Pattern] = field(default_factory=list)
    min_priority: int = Priority.OPTIONAL
    redact_emails: bool = True
    redact_ips: bool = True
    redact_uuids: bool = False


def _compile(pattern: str, flags: int = 0) -> re.Pattern[str]:
    """Compile regex pattern with error handling."""
    return re.compile(pattern, flags)


# High-Priority Patterns (P100) - Always Redact
_HIGH_PRIORITY_PATTERNS: list[Pattern] = [
    Pattern(
        name="aws_access_key",
        regex=_compile(r"AKIA[0-9A-Z]{16}"),
        category="AWS_KEY",
        priority=Priority.CRITICAL,
        description="AWS Access Key ID",
    ),
    Pattern(
        name="aws_secret_key",
        regex=_compile(
            r"(?<![A-Za-z0-9/+=])[A-Za-z0-9/+=]{40}(?![A-Za-z0-9/+=])"
        ),
        category="AWS_SECRET",
        priority=Priority.HIGH,
        description="AWS Secret Access Key (context-dependent)",
    ),
    Pattern(
        name="aws_session_token",
        regex=_compile(r"FwoGZX[A-Za-z0-9/+=]{100,}"),
        category="AWS_TOKEN",
        priority=Priority.CRITICAL,
        description="AWS Session Token",
    ),
    Pattern(
        name="github_token",
        regex=_compile(r"gh[pousr]_[A-Za-z0-9_]{36,255}"),
        category="GITHUB_TOKEN",
        priority=Priority.CRITICAL,
        description="GitHub Personal Access Token",
    ),
    Pattern(
        name="github_oauth",
        regex=_compile(r"gho_[A-Za-z0-9]{36}"),
        category="GITHUB_TOKEN",
        priority=Priority.CRITICAL,
        description="GitHub OAuth Token",
    ),
    Pattern(
        name="gitlab_token",
        regex=_compile(r"glpat-[A-Za-z0-9_-]{20,}"),
        category="GITLAB_TOKEN",
        priority=Priority.CRITICAL,
        description="GitLab Personal Access Token",
    ),
    Pattern(
        name="slack_token",
        regex=_compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
        category="SLACK_TOKEN",
        priority=Priority.CRITICAL,
        description="Slack Bot/User Token",
    ),
    Pattern(
        name="slack_webhook",
        regex=_compile(
            r"https://hooks\.slack\.com/services/T[A-Z0-9]+/B[A-Z0-9]+/[A-Za-z0-9]+"
        ),
        category="SLACK_WEBHOOK",
        priority=Priority.CRITICAL,
        description="Slack Webhook URL",
    ),
    Pattern(
        name="discord_webhook",
        regex=_compile(
            r"https://discord(?:app)?\.com/api/webhooks/\d+/[A-Za-z0-9_-]+"
        ),
        category="DISCORD_WEBHOOK",
        priority=Priority.CRITICAL,
        description="Discord Webhook URL",
    ),
    Pattern(
        name="private_key_block",
        regex=_compile(
            r"-----BEGIN\s+(?:[A-Z\s]+)?PRIVATE\s+KEY-----"
            r"[\s\S]*?"
            r"-----END\s+(?:[A-Z\s]+)?PRIVATE\s+KEY-----",
            re.MULTILINE,
        ),
        category="PRIVATE_KEY",
        priority=Priority.CRITICAL,
        description="Private Key Block (PEM format)",
    ),
    Pattern(
        name="azure_connection_string",
        regex=_compile(
            r"DefaultEndpointsProtocol=https?;"
            r"AccountName=[^;]+;"
            r"AccountKey=[A-Za-z0-9+/=]+",
            re.IGNORECASE,
        ),
        category="AZURE_KEY",
        priority=Priority.CRITICAL,
        description="Azure Storage Connection String",
    ),
    Pattern(
        name="gcp_api_key",
        regex=_compile(r"AIza[0-9A-Za-z_-]{35}"),
        category="GCP_KEY",
        priority=Priority.CRITICAL,
        description="Google Cloud API Key",
    ),
    Pattern(
        name="stripe_secret_key",
        regex=_compile(r"sk_live_[A-Za-z0-9]{24,}"),
        category="STRIPE_KEY",
        priority=Priority.CRITICAL,
        description="Stripe Secret Key",
    ),
    Pattern(
        name="stripe_restricted_key",
        regex=_compile(r"rk_live_[A-Za-z0-9]{24,}"),
        category="STRIPE_KEY",
        priority=Priority.CRITICAL,
        description="Stripe Restricted Key",
    ),
    Pattern(
        name="npm_token",
        regex=_compile(r"npm_[A-Za-z0-9]{36}"),
        category="NPM_TOKEN",
        priority=Priority.CRITICAL,
        description="NPM Auth Token",
    ),
    Pattern(
        name="pypi_token",
        regex=_compile(r"pypi-AgE[A-Za-z0-9_-]{50,}"),
        category="PYPI_TOKEN",
        priority=Priority.CRITICAL,
        description="PyPI API Token",
    ),
    Pattern(
        name="sendgrid_key",
        regex=_compile(r"SG\.[A-Za-z0-9_-]{22}\.[A-Za-z0-9_-]{43}"),
        category="SENDGRID_KEY",
        priority=Priority.CRITICAL,
        description="SendGrid API Key",
    ),
    Pattern(
        name="twilio_key",
        regex=_compile(r"SK[a-f0-9]{32}"),
        category="TWILIO_KEY",
        priority=Priority.CRITICAL,
        description="Twilio API Key",
    ),
    Pattern(
        name="mailchimp_key",
        regex=_compile(r"[a-f0-9]{32}-us\d{1,2}"),
        category="MAILCHIMP_KEY",
        priority=Priority.CRITICAL,
        description="Mailchimp API Key",
    ),
]

# Medium-Priority Patterns (P80-90) - Redact with Context
_MEDIUM_PRIORITY_PATTERNS: list[Pattern] = [
    Pattern(
        name="jwt",
        regex=_compile(
            r"eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]+"
        ),
        category="JWT",
        priority=Priority.HIGH,
        description="JSON Web Token",
    ),
    Pattern(
        name="bearer_token",
        regex=_compile(r"(?i)bearer\s+([A-Za-z0-9_-]{20,})"),
        category="BEARER_TOKEN",
        priority=Priority.HIGH,
        capture_group=1,
        description="Bearer Authorization Token",
    ),
    Pattern(
        name="basic_auth",
        regex=_compile(r"(?i)basic\s+([A-Za-z0-9+/=]{20,})"),
        category="BASIC_AUTH",
        priority=Priority.HIGH,
        capture_group=1,
        description="Basic Authorization Header",
    ),
    Pattern(
        name="connection_string_postgres",
        regex=_compile(
            r"postgres(?:ql)?://[^\s\"'<>]+",
            re.IGNORECASE,
        ),
        category="CONNECTION_STRING",
        priority=Priority.HIGH,
        description="PostgreSQL Connection String",
    ),
    Pattern(
        name="connection_string_mysql",
        regex=_compile(r"mysql://[^\s\"'<>]+", re.IGNORECASE),
        category="CONNECTION_STRING",
        priority=Priority.HIGH,
        description="MySQL Connection String",
    ),
    Pattern(
        name="connection_string_mongodb",
        regex=_compile(
            r"mongodb(?:\+srv)?://[^\s\"'<>]+",
            re.IGNORECASE,
        ),
        category="CONNECTION_STRING",
        priority=Priority.HIGH,
        description="MongoDB Connection String",
    ),
    Pattern(
        name="connection_string_redis",
        regex=_compile(r"redis://[^\s\"'<>]+", re.IGNORECASE),
        category="CONNECTION_STRING",
        priority=Priority.HIGH,
        description="Redis Connection String",
    ),
    Pattern(
        name="api_key_generic",
        regex=_compile(
            r"(?i)(api[_-]?key|apikey|access[_-]?token|auth[_-]?token)"
            r"[\"'\s:=]+[\"']?([A-Za-z0-9_-]{16,})[\"']?"
        ),
        category="API_KEY",
        priority=Priority.MEDIUM,
        capture_group=2,
        description="Generic API Key in config",
    ),
    Pattern(
        name="password_field",
        regex=_compile(
            r"(?i)(password|passwd|pwd|secret)"
            r"[\"'\s:=]+[\"']?([^\s\"',}{:\]]{4,})[\"']?"
        ),
        category="PASSWORD",
        priority=Priority.MEDIUM,
        capture_group=2,
        description="Password in config/logs",
    ),
    Pattern(
        name="authorization_header",
        regex=_compile(
            r"(?i)authorization[\"'\s:=]+[\"']?([^\s\"'\n]{10,})[\"']?"
        ),
        category="AUTH_HEADER",
        priority=Priority.MEDIUM,
        capture_group=1,
        description="Authorization Header Value",
    ),
]

# Low-Priority Patterns (P60-70) - Optional/Configurable
_LOW_PRIORITY_PATTERNS: list[Pattern] = [
    Pattern(
        name="ip_private",
        regex=_compile(
            r"\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}"
            r"|192\.168\.\d{1,3}\.\d{1,3}"
            r"|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})\b"
        ),
        category="IP_PRIVATE",
        priority=Priority.LOW,
        description="Private IP Address",
    ),
    Pattern(
        name="ip_public",
        regex=_compile(
            r"\b(?!10\.|192\.168\.|172\.(?:1[6-9]|2\d|3[01])\.)"
            r"(?!127\.)"
            r"(?!0\.)"
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"
        ),
        category="IP_PUBLIC",
        priority=Priority.OPTIONAL,
        description="Public IP Address",
    ),
    Pattern(
        name="email",
        regex=_compile(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
        ),
        category="EMAIL",
        priority=Priority.OPTIONAL,
        description="Email Address",
    ),
    Pattern(
        name="hostname_internal",
        regex=_compile(
            r"(?i)\b[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?"
            r"\.(?:internal|local|corp|lan|intranet)\b"
        ),
        category="HOSTNAME",
        priority=Priority.OPTIONAL,
        description="Internal Hostname",
    ),
    Pattern(
        name="uuid",
        regex=_compile(
            r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
            re.IGNORECASE,
        ),
        category="UUID",
        priority=Priority.DISABLED,
        description="UUID (often needed for debugging)",
    ),
]

DEFAULT_PATTERNS: tuple[Pattern, ...] = tuple(
    _HIGH_PRIORITY_PATTERNS + _MEDIUM_PRIORITY_PATTERNS + _LOW_PRIORITY_PATTERNS
)

HIGH_PRIORITY_PATTERN_NAMES: frozenset[str] = frozenset(
    p.name for p in _HIGH_PRIORITY_PATTERNS
)


def get_patterns_by_priority(
    min_priority: int = Priority.OPTIONAL,
) -> list[Pattern]:
    """Get patterns filtered by minimum priority.

    Args:
        min_priority: Minimum priority threshold.

    Returns:
        List of patterns with priority >= min_priority, sorted by priority desc.
    """
    patterns = [p for p in DEFAULT_PATTERNS if p.priority >= min_priority]
    return sorted(patterns, key=lambda p: p.priority, reverse=True)


def get_pattern_by_name(name: str) -> Pattern | None:
    """Get a pattern by its name."""
    for pattern in DEFAULT_PATTERNS:
        if pattern.name == name:
            return pattern
    return None


def create_custom_pattern(
    name: str,
    pattern: str,
    category: str,
    priority: int = Priority.MEDIUM,
    capture_group: int = 0,
    flags: int = 0,
) -> Pattern:
    """Create a custom pattern.

    Args:
        name: Unique pattern identifier.
        pattern: Regular expression string.
        category: Category for token naming.
        priority: Pattern priority.
        capture_group: Which group contains the secret.
        flags: Regex flags.

    Returns:
        New Pattern instance.
    """
    return Pattern(
        name=name,
        regex=_compile(pattern, flags),
        category=category,
        priority=priority,
        capture_group=capture_group,
    )
