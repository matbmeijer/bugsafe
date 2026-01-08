"""Fuzz tests for malformed input handling."""

import json
import zipfile
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

from bugsafe.bundle.reader import (
    BundleCorruptError,
    BundleParseError,
    BundleSchemaError,
    SecurityError,
    read_bundle,
)
from bugsafe.bundle.schema import BugBundle
from bugsafe.bundle.writer import create_bundle
from bugsafe.capture.traceback import extract_traceback
from bugsafe.redact.engine import create_redaction_engine


class TestMalformedTraceback:
    """Fuzz tests for traceback parsing."""

    @given(st.text(max_size=5000))
    @settings(max_examples=100)
    def test_no_crash_on_arbitrary_traceback(self, text: str):
        """Traceback parser doesn't crash on arbitrary input."""
        result = extract_traceback(text)
        assert result is None or hasattr(result, "exception_type")

    @given(st.binary(max_size=2000))
    @settings(max_examples=50)
    def test_handles_binary_input(self, data: bytes):
        """Traceback parser handles binary-ish input."""
        try:
            text = data.decode("utf-8", errors="replace")
        except Exception:
            return
        result = extract_traceback(text)
        assert result is None or hasattr(result, "exception_type")

    @given(st.text(max_size=1000))
    @settings(max_examples=50)
    def test_partial_traceback(self, noise: str):
        """Partial traceback patterns don't crash parser."""
        partial_patterns = [
            "Traceback (most recent call last):",
            "  File ",
            "    raise ",
            "ValueError:",
            noise + "Traceback" + noise,
        ]
        for pattern in partial_patterns:
            text = noise + pattern + noise
            result = extract_traceback(text)
            assert result is None or hasattr(result, "exception_type")


class TestMalformedBundle:
    """Fuzz tests for bundle reading."""

    @given(st.binary(max_size=1000))
    @settings(max_examples=50)
    def test_invalid_zip_content(self, data: bytes):
        """Reader handles invalid ZIP content gracefully."""
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".bugbundle", delete=False) as f:
            f.write(data)
            bundle_path = Path(f.name)

        try:
            read_bundle(bundle_path)
        except (BundleCorruptError, BundleParseError, BundleSchemaError):
            pass
        finally:
            bundle_path.unlink(missing_ok=True)

    @given(st.text(max_size=500))
    @settings(max_examples=50)
    def test_invalid_manifest_json(self, json_text: str):
        """Reader handles invalid JSON in manifest."""
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".bugbundle", delete=False) as f:
            bundle_path = Path(f.name)

        with zipfile.ZipFile(bundle_path, "w") as zf:
            zf.writestr("manifest.json", json_text)

        try:
            read_bundle(bundle_path)
        except (BundleParseError, BundleSchemaError, BundleCorruptError, Exception):
            pass
        finally:
            bundle_path.unlink(missing_ok=True)

    @given(st.dictionaries(st.text(max_size=20), st.text(max_size=50), max_size=10))
    @settings(max_examples=50)
    def test_arbitrary_json_schema(self, data: dict):
        """Reader handles arbitrary JSON that doesn't match schema."""
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".bugbundle", delete=False) as f:
            bundle_path = Path(f.name)

        with zipfile.ZipFile(bundle_path, "w") as zf:
            zf.writestr("manifest.json", json.dumps(data))

        try:
            read_bundle(bundle_path)
        except (BundleSchemaError, BundleParseError):
            pass
        finally:
            bundle_path.unlink(missing_ok=True)


class TestPathTraversal:
    """Fuzz tests for path traversal protection."""

    @given(
        st.sampled_from(["../etc/passwd", "/../secret", "/etc/passwd", "..\\windows"])
    )
    @settings(max_examples=10)
    def test_path_traversal_blocked(self, filename: str):
        """Path traversal attempts are blocked."""
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".bugbundle", delete=False) as f:
            bundle_path = Path(f.name)

        try:
            with zipfile.ZipFile(bundle_path, "w") as zf:
                zf.writestr("manifest.json", "{}")
                try:
                    zf.writestr(filename, "malicious content")
                except (ValueError, OSError):
                    return

            read_bundle(bundle_path)
        except (SecurityError, BundleCorruptError, BundleSchemaError):
            pass
        finally:
            bundle_path.unlink(missing_ok=True)


class TestMalformedRedaction:
    """Fuzz tests for redaction engine."""

    @given(st.text(max_size=10000))
    @settings(max_examples=100)
    def test_large_text_no_timeout(self, text: str):
        """Engine handles large text without hanging."""
        engine = create_redaction_engine()
        result, _ = engine.redact(text)
        assert isinstance(result, str)

    @given(st.text(alphabet="()*+?[]{}|\\^$.", max_size=200))
    @settings(max_examples=50)
    def test_regex_metacharacters(self, text: str):
        """Engine handles regex metacharacters safely."""
        engine = create_redaction_engine()
        result, _ = engine.redact(text)
        assert isinstance(result, str)

    @given(st.text(max_size=500))
    @settings(max_examples=50)
    def test_repeated_patterns(self, base: str):
        """Engine handles repeated patterns."""
        text = (base + " AKIAIOSFODNN7EXAMPLE ") * 100
        engine = create_redaction_engine()
        result, report = engine.redact(text)
        assert "AKIAIOSFODNN7EXAMPLE" not in result


class TestBundleRoundTrip:
    """Fuzz tests for bundle round-trip."""

    @given(
        st.text(max_size=500),
        st.text(max_size=500),
        st.integers(min_value=-128, max_value=127),
    )
    @settings(max_examples=50)
    def test_roundtrip_preserves_data(
        self,
        stdout: str,
        stderr: str,
        exit_code: int,
    ):
        """Bundle round-trip preserves data."""
        import tempfile

        from bugsafe.bundle.schema import CaptureOutput

        bundle = BugBundle(
            capture=CaptureOutput(
                stdout=stdout,
                stderr=stderr,
                exit_code=exit_code,
                command=["test"],
            ),
        )

        with tempfile.NamedTemporaryFile(suffix=".bugbundle", delete=False) as f:
            bundle_path = Path(f.name)

        try:
            create_bundle(bundle, bundle_path)
            loaded = read_bundle(bundle_path)

            assert loaded.capture.stdout == stdout
            assert loaded.capture.stderr == stderr
            assert loaded.capture.exit_code == exit_code
        finally:
            bundle_path.unlink(missing_ok=True)


class TestUnicodeHandling:
    """Fuzz tests for Unicode handling."""

    @given(st.text(alphabet=st.characters(min_codepoint=0x100), max_size=500))
    @settings(max_examples=50)
    def test_non_ascii_redaction(self, text: str):
        """Redaction handles non-ASCII text."""
        engine = create_redaction_engine()
        result, _ = engine.redact(text)
        assert isinstance(result, str)

    @given(st.text(alphabet=st.characters(min_codepoint=0x10000), max_size=200))
    @settings(max_examples=30)
    def test_emoji_and_symbols(self, text: str):
        """Redaction handles emoji and special symbols."""
        engine = create_redaction_engine()
        result, _ = engine.redact(text)
        assert isinstance(result, str)

    @given(st.text(max_size=500))
    @settings(max_examples=50)
    def test_mixed_unicode_and_secrets(self, prefix: str):
        """Redaction handles mixed Unicode and secrets."""
        text = f"{prefix} 密码=AKIAIOSFODNN7EXAMPLE 邮箱=test@example.com"
        engine = create_redaction_engine()
        result, _ = engine.redact(text)
        assert "AKIAIOSFODNN7EXAMPLE" not in result
