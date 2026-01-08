"""Bundle writer - Create and modify .bugbundle files."""

from __future__ import annotations

import hashlib
import json
import os
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from bugsafe.bundle.schema import BugBundle

if TYPE_CHECKING:
    pass

MAX_BUNDLE_SIZE = 50 * 1024 * 1024  # 50 MB
MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_ATTACHMENTS = 20

ALLOWED_EXTENSIONS = frozenset(
    {
        ".txt",
        ".log",
        ".yaml",
        ".yml",
        ".json",
        ".toml",
        ".ini",
        ".cfg",
        ".md",
        ".rst",
    }
)

MANIFEST_FILENAME = "manifest.json"
STDOUT_FILENAME = "stdout.txt"
STDERR_FILENAME = "stderr.txt"
CHECKSUM_FILENAME = "checksum.sha256"
ATTACHMENTS_DIR = "attachments"


class BundleError(Exception):
    """Base exception for bundle errors."""


class BundleWriteError(BundleError):
    """Error writing bundle."""


class BundleSizeError(BundleError):
    """Bundle exceeds size limit."""


class AttachmentError(BundleError):
    """Error with attachment."""


@dataclass
class ValidationResult:
    """Result of bundle validation.

    Attributes:
        valid: Whether the bundle is valid.
        errors: List of validation errors.
        warnings: List of validation warnings.
    """

    valid: bool
    errors: list[str]
    warnings: list[str]


def _compute_checksum(data: bytes) -> str:
    """Compute SHA256 checksum of data."""
    return hashlib.sha256(data).hexdigest()


def _sanitize_filename(name: str) -> str:
    """Sanitize filename to prevent path traversal."""
    name = os.path.basename(name)
    name = name.replace("..", "_")
    name = "".join(c if c.isalnum() or c in "._-" else "_" for c in name)
    return name or "unnamed"


def _ensure_unique_name(name: str, existing: set[str]) -> str:
    """Ensure attachment name is unique."""
    if name not in existing:
        return name

    base, ext = os.path.splitext(name)
    counter = 1
    while f"{base}_{counter}{ext}" in existing:
        counter += 1
    return f"{base}_{counter}{ext}"


def create_bundle(
    bundle: BugBundle,
    path: Path,
    *,
    overwrite: bool = True,
) -> None:
    """Create a .bugbundle file.

    Args:
        bundle: The BugBundle to write.
        path: Output path for the bundle.
        overwrite: Whether to overwrite existing file.

    Raises:
        BundleWriteError: If writing fails.
        BundleSizeError: If bundle exceeds size limit.
        FileExistsError: If file exists and overwrite=False.
    """
    path = Path(path)

    if path.exists() and not overwrite:
        raise FileExistsError(f"Bundle already exists: {path}")

    path.parent.mkdir(parents=True, exist_ok=True)

    manifest_data = bundle.to_dict()
    manifest_json = json.dumps(manifest_data, indent=2, default=str)
    manifest_bytes = manifest_json.encode("utf-8")

    checksum = _compute_checksum(manifest_bytes)
    checksum_content = f"{checksum}  {MANIFEST_FILENAME}\n"

    stdout_content = bundle.capture.stdout or ""
    stderr_content = bundle.capture.stderr or ""

    total_size = (
        len(manifest_bytes)
        + len(stdout_content.encode("utf-8"))
        + len(stderr_content.encode("utf-8"))
        + len(checksum_content.encode("utf-8"))
    )

    if total_size > MAX_BUNDLE_SIZE:
        raise BundleSizeError(
            f"Bundle size ({total_size} bytes) exceeds limit ({MAX_BUNDLE_SIZE} bytes)"
        )

    try:
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(MANIFEST_FILENAME, manifest_bytes)
            zf.writestr(CHECKSUM_FILENAME, checksum_content)

            if stdout_content:
                zf.writestr(STDOUT_FILENAME, stdout_content)

            if stderr_content:
                zf.writestr(STDERR_FILENAME, stderr_content)

    except OSError as e:
        raise BundleWriteError(f"Failed to write bundle: {e}") from e


def add_attachment(
    bundle_path: Path,
    name: str,
    content: str | bytes,
) -> str:
    """Add an attachment to an existing bundle.

    Args:
        bundle_path: Path to the bundle.
        name: Attachment filename.
        content: Attachment content.

    Returns:
        The final filename used (may be modified for uniqueness).

    Raises:
        BundleWriteError: If bundle doesn't exist or is invalid.
        AttachmentError: If attachment is invalid or limit reached.
    """
    bundle_path = Path(bundle_path)

    if not bundle_path.exists():
        raise BundleWriteError(f"Bundle not found: {bundle_path}")

    safe_name = _sanitize_filename(name)

    ext = os.path.splitext(safe_name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise AttachmentError(
            f"Extension '{ext}' not allowed. Allowed: {sorted(ALLOWED_EXTENSIONS)}"
        )

    if isinstance(content, str):
        content_bytes = content.encode("utf-8")
    else:
        content_bytes = content

    if len(content_bytes) > MAX_ATTACHMENT_SIZE:
        raise AttachmentError(
            f"Attachment size ({len(content_bytes)} bytes) exceeds limit "
            f"({MAX_ATTACHMENT_SIZE} bytes)"
        )

    try:
        with zipfile.ZipFile(bundle_path, "a") as zf:
            existing = {
                n.replace(f"{ATTACHMENTS_DIR}/", "")
                for n in zf.namelist()
                if n.startswith(f"{ATTACHMENTS_DIR}/")
            }

            if len(existing) >= MAX_ATTACHMENTS:
                raise AttachmentError(
                    f"Maximum attachments ({MAX_ATTACHMENTS}) reached"
                )

            final_name = _ensure_unique_name(safe_name, existing)
            attachment_path = f"{ATTACHMENTS_DIR}/{final_name}"

            zf.writestr(attachment_path, content_bytes)

            return final_name

    except zipfile.BadZipFile as e:
        raise BundleWriteError(f"Invalid bundle file: {e}") from e
    except OSError as e:
        raise BundleWriteError(f"Failed to add attachment: {e}") from e


def validate_bundle(path: Path) -> ValidationResult:
    """Validate a bundle file.

    Args:
        path: Path to the bundle.

    Returns:
        ValidationResult with validity status and any issues.
    """
    path = Path(path)
    errors: list[str] = []
    warnings: list[str] = []

    if not path.exists():
        return ValidationResult(
            valid=False,
            errors=[f"Bundle not found: {path}"],
            warnings=[],
        )

    try:
        with zipfile.ZipFile(path, "r") as zf:
            namelist = zf.namelist()

            if MANIFEST_FILENAME not in namelist:
                errors.append(f"Missing {MANIFEST_FILENAME}")

            if CHECKSUM_FILENAME not in namelist:
                warnings.append(f"Missing {CHECKSUM_FILENAME}")

            if MANIFEST_FILENAME in namelist and CHECKSUM_FILENAME in namelist:
                manifest_data = zf.read(MANIFEST_FILENAME)
                checksum_content = zf.read(CHECKSUM_FILENAME).decode("utf-8")

                expected_checksum = _compute_checksum(manifest_data)
                if expected_checksum not in checksum_content:
                    errors.append("Checksum mismatch - bundle may be corrupted")

            if MANIFEST_FILENAME in namelist:
                try:
                    manifest_data = zf.read(MANIFEST_FILENAME)
                    json.loads(manifest_data.decode("utf-8"))
                except json.JSONDecodeError as e:
                    errors.append(f"Invalid JSON in manifest: {e}")

            for name in namelist:
                if ".." in name or name.startswith("/"):
                    errors.append(f"Suspicious path in bundle: {name}")

            attachment_count = sum(
                1 for n in namelist if n.startswith(f"{ATTACHMENTS_DIR}/")
            )
            if attachment_count > MAX_ATTACHMENTS:
                warnings.append(
                    f"Too many attachments: {attachment_count} > {MAX_ATTACHMENTS}"
                )

    except zipfile.BadZipFile as e:
        return ValidationResult(
            valid=False,
            errors=[f"Invalid ZIP file: {e}"],
            warnings=[],
        )
    except OSError as e:
        return ValidationResult(
            valid=False,
            errors=[f"Error reading bundle: {e}"],
            warnings=[],
        )

    return ValidationResult(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )
