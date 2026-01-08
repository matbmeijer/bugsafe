"""Bundle module - .bugbundle format handling."""

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
    "BugBundle",
    "BundleMetadata",
    "CaptureOutput",
    "Environment",
    "Frame",
    "Traceback",
    "create_bundle",
    "add_attachment",
    "validate_bundle",
    "read_bundle",
    "list_attachments",
    "get_attachment",
    "verify_integrity",
]
