"""Bundle reader - Read and parse .bugbundle files."""

from __future__ import annotations

import hashlib
import json
import zipfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from bugsafe.bundle.schema import BUNDLE_VERSION, BugBundle

MANIFEST_FILENAME = "manifest.json"
STDOUT_FILENAME = "stdout.txt"
STDERR_FILENAME = "stderr.txt"
CHECKSUM_FILENAME = "checksum.sha256"
ATTACHMENTS_DIR = "attachments"

MigrationFunc = Callable[[dict[str, Any]], dict[str, Any]]


class BundleReadError(Exception):
    """Base exception for bundle read errors."""


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


VERSION_MIGRATIONS: dict[str, MigrationFunc] = {
    "1.0": lambda b: b,
}


def _compute_checksum(data: bytes) -> str:
    """Compute SHA256 checksum of data."""
    return hashlib.sha256(data).hexdigest()


def _check_path_safety(name: str) -> None:
    """Check for path traversal attempts."""
    if ".." in name:
        raise SecurityError(f"Path traversal detected: {name}")
    if name.startswith("/") or name.startswith("\\"):
        raise SecurityError(f"Absolute path detected: {name}")


def _migrate_bundle(data: dict[str, Any], version: str) -> dict[str, Any]:
    """Migrate bundle data to current version."""
    if version not in VERSION_MIGRATIONS:
        raise BundleVersionError(f"Unsupported bundle version: {version}")

    return VERSION_MIGRATIONS[version](data)


def read_bundle(path: Path) -> BugBundle:
    """Read and parse a .bugbundle file.

    Args:
        path: Path to the bundle file.

    Returns:
        Parsed BugBundle.

    Raises:
        BundleNotFoundError: If file doesn't exist.
        BundleCorruptError: If ZIP is invalid.
        BundleParseError: If JSON parsing fails.
        BundleSchemaError: If schema validation fails.
        BundleVersionError: If version is unsupported.
    """
    path = Path(path)

    if not path.exists():
        raise BundleNotFoundError(f"Bundle not found: {path}")

    try:
        with zipfile.ZipFile(path, "r") as zf:
            for name in zf.namelist():
                _check_path_safety(name)

            if MANIFEST_FILENAME not in zf.namelist():
                raise BundleCorruptError(
                    f"Bundle missing {MANIFEST_FILENAME}"
                )

            manifest_data = zf.read(MANIFEST_FILENAME)

            try:
                data = json.loads(manifest_data.decode("utf-8"))
            except json.JSONDecodeError as e:
                raise BundleParseError(
                    f"Invalid JSON in manifest at line {e.lineno}: {e.msg}"
                ) from e

            version = data.get("metadata", {}).get("version", BUNDLE_VERSION)
            data = _migrate_bundle(data, version)

            try:
                bundle = BugBundle.model_validate(data)
            except ValidationError as e:
                errors = "; ".join(
                    f"{'.'.join(str(x) for x in err['loc'])}: {err['msg']}"
                    for err in e.errors()
                )
                raise BundleSchemaError(f"Schema validation failed: {errors}") from e

            return bundle

    except zipfile.BadZipFile as e:
        raise BundleCorruptError(f"Invalid ZIP file: {e}") from e
    except OSError as e:
        raise BundleReadError(f"Error reading bundle: {e}") from e


def list_attachments(path: Path) -> list[str]:
    """List all attachments in a bundle.

    Args:
        path: Path to the bundle file.

    Returns:
        List of attachment filenames.

    Raises:
        BundleNotFoundError: If file doesn't exist.
        BundleCorruptError: If ZIP is invalid.
    """
    path = Path(path)

    if not path.exists():
        raise BundleNotFoundError(f"Bundle not found: {path}")

    try:
        with zipfile.ZipFile(path, "r") as zf:
            prefix = f"{ATTACHMENTS_DIR}/"
            attachments = [
                name[len(prefix):]
                for name in zf.namelist()
                if name.startswith(prefix) and len(name) > len(prefix)
            ]
            return sorted(attachments)

    except zipfile.BadZipFile as e:
        raise BundleCorruptError(f"Invalid ZIP file: {e}") from e


def get_attachment(path: Path, name: str) -> str:
    """Get attachment content from a bundle.

    Args:
        path: Path to the bundle file.
        name: Attachment filename.

    Returns:
        Attachment content as string.

    Raises:
        BundleNotFoundError: If bundle doesn't exist.
        AttachmentNotFoundError: If attachment doesn't exist.
        BundleCorruptError: If ZIP is invalid.
    """
    path = Path(path)

    if not path.exists():
        raise BundleNotFoundError(f"Bundle not found: {path}")

    _check_path_safety(name)

    try:
        with zipfile.ZipFile(path, "r") as zf:
            attachment_path = f"{ATTACHMENTS_DIR}/{name}"

            if attachment_path not in zf.namelist():
                raise AttachmentNotFoundError(
                    f"Attachment not found: {name}"
                )

            content = zf.read(attachment_path)
            return content.decode("utf-8")

    except zipfile.BadZipFile as e:
        raise BundleCorruptError(f"Invalid ZIP file: {e}") from e
    except UnicodeDecodeError as e:
        raise BundleParseError(f"Attachment is not valid UTF-8: {e}") from e


def verify_integrity(path: Path) -> bool:
    """Verify bundle integrity using checksum.

    Args:
        path: Path to the bundle file.

    Returns:
        True if checksum matches, False otherwise.

    Raises:
        BundleNotFoundError: If bundle doesn't exist.
        BundleCorruptError: If ZIP is invalid.
    """
    path = Path(path)

    if not path.exists():
        raise BundleNotFoundError(f"Bundle not found: {path}")

    try:
        with zipfile.ZipFile(path, "r") as zf:
            if MANIFEST_FILENAME not in zf.namelist():
                return False

            if CHECKSUM_FILENAME not in zf.namelist():
                return True

            manifest_data = zf.read(MANIFEST_FILENAME)
            checksum_content = zf.read(CHECKSUM_FILENAME).decode("utf-8")

            expected_checksum = _compute_checksum(manifest_data)
            return expected_checksum in checksum_content

    except zipfile.BadZipFile:
        return False
    except OSError:
        return False
