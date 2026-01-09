"""Redaction engine - Main redaction orchestration."""

from __future__ import annotations

import re
import signal
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

from bugsafe.redact.path_anonymizer import PathAnonymizer, create_default_anonymizer
from bugsafe.redact.patterns import (
    DEFAULT_PATTERNS,
    HIGH_PRIORITY_PATTERN_NAMES,
    Pattern,
    PatternConfig,
)
from bugsafe.redact.tokenizer import Tokenizer

if TYPE_CHECKING:
    pass

PATTERN_TIMEOUT_MS = 100
MIN_SECRET_LENGTH = 4
MAX_PATTERN_LENGTH = 1000


class RedactionTimeoutError(Exception):
    """Raised when a pattern match times out."""


class PatternComplexityError(ValueError):
    """Raised when a pattern is too complex."""


@lru_cache(maxsize=128)
def compile_pattern_safely(pattern: str, flags: int = 0) -> re.Pattern[str]:
    """Compile regex with safety limits to prevent ReDoS.

    Args:
        pattern: The regex pattern string.
        flags: Optional regex flags.

    Returns:
        Compiled regex pattern.

    Raises:
        PatternComplexityError: If pattern exceeds complexity limits.
    """
    if len(pattern) > MAX_PATTERN_LENGTH:
        raise PatternComplexityError(
            f"Pattern too complex: {len(pattern)} chars > {MAX_PATTERN_LENGTH} limit"
        )
    return re.compile(pattern, flags)


@dataclass
class RedactionMatch:
    """A single redaction match.

    Attributes:
        original: The original secret value.
        token: The replacement token.
        category: The pattern category.
        pattern_name: Name of the pattern that matched.
        start: Start position in original text.
        end: End position in original text.
    """

    original: str
    token: str
    category: str
    pattern_name: str
    start: int
    end: int


@dataclass
class RedactionReport:
    """Report of redactions performed.

    Attributes:
        matches: List of all redaction matches.
        categories: Count of redactions by category.
        patterns_used: Set of pattern names that matched.
        warnings: Any warnings during redaction.
    """

    matches: list[RedactionMatch] = field(default_factory=list)
    categories: dict[str, int] = field(default_factory=dict)
    patterns_used: set[str] = field(default_factory=set)
    warnings: list[str] = field(default_factory=list)

    def add(
        self,
        original: str,
        token: str,
        category: str,
        pattern_name: str,
        start: int = 0,
        end: int = 0,
    ) -> None:
        """Add a redaction match to the report."""
        self.matches.append(
            RedactionMatch(
                original=original,
                token=token,
                category=category,
                pattern_name=pattern_name,
                start=start,
                end=end,
            )
        )
        self.categories[category] = self.categories.get(category, 0) + 1
        self.patterns_used.add(pattern_name)

    def merge(self, other: RedactionReport) -> RedactionReport:
        """Merge another report into this one."""
        self.matches.extend(other.matches)
        for category, count in other.categories.items():
            self.categories[category] = self.categories.get(category, 0) + count
        self.patterns_used.update(other.patterns_used)
        self.warnings.extend(other.warnings)
        return self

    def get_summary(self) -> dict[str, int]:
        """Get summary of redactions by category."""
        return dict(self.categories)

    def get_total(self) -> int:
        """Get total number of redactions."""
        return len(self.matches)


@contextmanager
def _timeout_handler(timeout_ms: int) -> Iterator[None]:
    """Context manager for pattern matching timeout (Unix only).

    On Windows, timeout is not supported and patterns run without timeout.
    """
    if timeout_ms <= 0:
        yield
        return

    # SIGALRM and setitimer are Unix-only
    if not hasattr(signal, "SIGALRM") or not hasattr(signal, "setitimer"):
        yield
        return

    def handler(signum: int, frame: object) -> None:
        raise RedactionTimeoutError("Pattern matching timed out")

    try:
        old_handler = signal.signal(signal.SIGALRM, handler)
        signal.setitimer(signal.ITIMER_REAL, timeout_ms / 1000.0)
        yield
    except (ValueError, AttributeError):
        yield
    finally:
        try:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, old_handler)
        except (ValueError, AttributeError):
            pass


@dataclass
class RedactionEngine:
    """Main redaction engine.

    Orchestrates pattern matching, tokenization, and path anonymization
    to redact sensitive information from text.

    Attributes:
        tokenizer: Tokenizer for generating replacement tokens.
        path_anonymizer: Path anonymizer for file paths.
        config: Pattern configuration.
        patterns: List of patterns to use.
        timeout_ms: Timeout per pattern in milliseconds.
    """

    tokenizer: Tokenizer = field(default_factory=Tokenizer)
    path_anonymizer: PathAnonymizer = field(default_factory=create_default_anonymizer)
    config: PatternConfig = field(default_factory=PatternConfig)
    patterns: list[Pattern] = field(default_factory=list)
    timeout_ms: int = PATTERN_TIMEOUT_MS
    _last_report: RedactionReport = field(default_factory=RedactionReport, repr=False)

    def __post_init__(self) -> None:
        """Initialize patterns if not provided."""
        if not self.patterns:
            self.patterns = list(DEFAULT_PATTERNS)

        if self.config.custom_patterns:
            self.patterns.extend(self.config.custom_patterns)

    def redact(self, text: str) -> tuple[str, RedactionReport]:
        """Redact sensitive information from text.

        Args:
            text: Text to redact.

        Returns:
            Tuple of (redacted_text, report).
        """
        if not text:
            return text, RedactionReport()

        report = RedactionReport()
        result = text

        sorted_patterns = sorted(
            self.patterns,
            key=lambda p: (p.priority, len(p.regex.pattern)),
            reverse=True,
        )

        for pattern in sorted_patterns:
            if not self._should_apply_pattern(pattern):
                continue

            try:
                result = self._apply_pattern(result, pattern, report)
            except RedactionTimeoutError:
                report.warnings.append(
                    f"Pattern '{pattern.name}' timed out and was skipped"
                )

        result = self.path_anonymizer.anonymize(result)

        self._last_report = report
        return result, report

    def _should_apply_pattern(self, pattern: Pattern) -> bool:
        """Check if a pattern should be applied based on config."""
        if pattern.name in self.config.disabled_patterns:
            return False

        if self.config.enabled_patterns is not None:
            if pattern.name not in self.config.enabled_patterns:
                return False

        if pattern.category == "EMAIL" and not self.config.redact_emails:
            return False

        if pattern.category in ("IP_PRIVATE", "IP_PUBLIC"):
            if not self.config.redact_ips:
                return False

        if pattern.category == "UUID":
            if not self.config.redact_uuids:
                return False
            return True

        if pattern.priority < self.config.min_priority:
            return False

        return True

    def _apply_pattern(
        self,
        text: str,
        pattern: Pattern,
        report: RedactionReport,
    ) -> str:
        """Apply a single pattern to text.

        Returns:
            Modified text with secrets replaced.
        """
        replacements: list[tuple[str, str]] = []

        try:
            with _timeout_handler(self.timeout_ms):
                for match in pattern.regex.finditer(text):
                    if pattern.capture_group > 0:
                        try:
                            secret = match.group(pattern.capture_group)
                            if secret is None:
                                continue
                        except IndexError:
                            secret = match.group(0)
                    else:
                        secret = match.group(0)

                    if not secret or len(secret) < MIN_SECRET_LENGTH:
                        continue

                    if self.tokenizer.is_token(secret):
                        continue

                    token = self.tokenizer.tokenize(secret, pattern.category)
                    replacements.append((secret, token))

        except RedactionTimeoutError:
            raise

        result = text
        for secret, token in replacements:
            if secret in result:
                result = result.replace(secret, token)
                report.add(
                    original=secret,
                    token=token,
                    category=pattern.category,
                    pattern_name=pattern.name,
                )

        return result

    def verify_redaction(self, text: str) -> list[str]:
        """Verify that no high-priority secrets remain in text.

        Args:
            text: Text to verify.

        Returns:
            List of pattern names that still match (potential leaks).
        """
        leaks: list[str] = []

        for pattern in self.patterns:
            if pattern.name not in HIGH_PRIORITY_PATTERN_NAMES:
                continue

            for match in pattern.regex.finditer(text):
                matched_text = match.group(0)
                if not self.tokenizer.is_token(matched_text):
                    leaks.append(pattern.name)
                    break

        return leaks

    def get_salt_hash(self) -> str:
        """Get the salt hash for bundle metadata."""
        return self.tokenizer.get_salt_hash()

    def get_redaction_summary(self) -> dict[str, int]:
        """Get summary from last redaction operation.

        Returns:
            Dictionary mapping category names to redaction counts.
        """
        return self._last_report.get_summary()


def create_redaction_engine(
    project_root: Path | None = None,
    config: PatternConfig | None = None,
) -> RedactionEngine:
    """Create a configured redaction engine.

    Args:
        project_root: Project root for path anonymization.
        config: Optional pattern configuration.

    Returns:
        Configured RedactionEngine.
    """
    tokenizer = Tokenizer()
    path_anonymizer = PathAnonymizer(project_root=project_root)

    return RedactionEngine(
        tokenizer=tokenizer,
        path_anonymizer=path_anonymizer,
        config=config or PatternConfig(),
    )
