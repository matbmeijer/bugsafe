"""Unified exception hierarchy for bundle operations."""

from __future__ import annotations


class BundleError(Exception):
    """Base exception for all bundle operations."""


class BundleReadError(BundleError):
    """Base exception for bundle read errors."""


class BundleWriteError(BundleError):
    """Base exception for bundle write errors."""


class BundleNotFoundError(BundleReadError):
    """Bundle file not found."""


class BundleCorruptError(BundleReadError):
    """Bundle is corrupted or invalid."""


class BundleParseError(BundleReadError):
    """Error parsing bundle content."""


class BundleSchemaError(BundleReadError):
    """Bundle doesn't match expected schema."""


class BundleIntegrityError(BundleReadError):
    """Bundle checksum verification failed."""


class BundleVersionError(BundleReadError):
    """Unsupported bundle version."""


class AttachmentNotFoundError(BundleReadError):
    """Requested attachment not found."""


class SecurityError(BundleReadError):
    """Security issue detected (e.g., path traversal)."""


class BundleSizeError(BundleWriteError):
    """Bundle exceeds size limit."""


class AttachmentError(BundleWriteError):
    """Error with attachment."""
