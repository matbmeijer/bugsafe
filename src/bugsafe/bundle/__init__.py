"""Bundle module - .bugbundle format handling."""

from bugsafe.bundle.exceptions import (
    AttachmentError,
    AttachmentNotFoundError,
    BundleCorruptError,
    BundleError,
    BundleNotFoundError,
    BundleParseError,
    BundleReadError,
    BundleSchemaError,
    BundleSizeError,
    BundleVersionError,
    BundleWriteError,
    SecurityError,
)
from bugsafe.bundle.reader import (
    get_attachment,
    list_attachments,
    read_bundle,
    verify_integrity,
)
from bugsafe.bundle.schema import (
    BugBundle,
    BundleMetadata,
    CaptureOutput,
    Environment,
    Frame,
    Traceback,
)
from bugsafe.bundle.writer import add_attachment, create_bundle, validate_bundle

__all__ = [
    "AttachmentError",
    "AttachmentNotFoundError",
    "BugBundle",
    "BundleCorruptError",
    "BundleError",
    "BundleMetadata",
    "BundleNotFoundError",
    "BundleParseError",
    "BundleReadError",
    "BundleSchemaError",
    "BundleSizeError",
    "BundleVersionError",
    "BundleWriteError",
    "CaptureOutput",
    "Environment",
    "Frame",
    "SecurityError",
    "Traceback",
    "add_attachment",
    "create_bundle",
    "get_attachment",
    "list_attachments",
    "read_bundle",
    "validate_bundle",
    "verify_integrity",
]
