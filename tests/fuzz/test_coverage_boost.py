"""Additional fuzz tests to increase code coverage."""

from datetime import datetime, timezone

from hypothesis import given, settings
from hypothesis import strategies as st

from bugsafe.bundle.schema import BugBundle, BundleMetadata, CaptureOutput
from bugsafe.capture.runner import run_command
from bugsafe.redact.engine import create_redaction_engine
from bugsafe.render.markdown import render_markdown


class TestRedactionFuzz:
    """Fuzz tests for redaction engine."""

    @given(st.text(max_size=500))
    @settings(max_examples=30)
    def test_redact_arbitrary_text(self, text):
        """Redact arbitrary text without crashing."""
        engine = create_redaction_engine()
        result, report = engine.redact(text)

        assert isinstance(result, str)
        assert report.get_total() >= 0

    @given(st.lists(st.text(max_size=50), max_size=10))
    @settings(max_examples=20)
    def test_redact_multiple_lines(self, lines):
        """Redact multiple lines."""
        engine = create_redaction_engine()
        text = "\n".join(lines)

        result, _ = engine.redact(text)

        assert isinstance(result, str)

    @given(st.text(alphabet="0123456789abcdef", min_size=20, max_size=50))
    @settings(max_examples=20)
    def test_redact_hex_strings(self, text):
        """Redact hex-like strings."""
        engine = create_redaction_engine()

        result, _ = engine.redact(text)

        assert isinstance(result, str)


class TestRenderFuzz:
    """Fuzz tests for rendering."""

    @given(
        st.text(max_size=200),
        st.text(max_size=200),
        st.integers(min_value=-128, max_value=127),
    )
    @settings(max_examples=20)
    def test_render_markdown_fuzz(self, stdout, stderr, exit_code):
        """Render markdown with various inputs."""
        bundle = BugBundle(
            metadata=BundleMetadata(
                created_at=datetime.now(timezone.utc),
                bugsafe_version="0.1.0",
                redaction_salt_hash="test",
            ),
            capture=CaptureOutput(
                stdout=stdout,
                stderr=stderr,
                exit_code=exit_code,
                duration_ms=100,
                command=["test"],
                timed_out=False,
                truncated=False,
            ),
        )

        result = render_markdown(bundle)

        assert isinstance(result, str)
        assert len(result) > 0


class TestRunnerFuzz:
    """Fuzz tests for command runner."""

    @given(
        st.lists(
            st.text(alphabet="abcdefghijklmnop", min_size=1, max_size=5),
            min_size=1,
            max_size=3,
        )
    )
    @settings(max_examples=10)
    def test_run_with_args(self, args):
        """Run echo with various args."""
        result = run_command(["echo"] + args)

        assert result.exit_code == 0


class TestVerifyRedaction:
    """Tests for verify_redaction method."""

    def test_verify_clean_text(self):
        """Verify clean text passes."""
        engine = create_redaction_engine()

        leaks = engine.verify_redaction("This is clean text")

        assert len(leaks) == 0

    def test_verify_text_with_tokens(self):
        """Verify text with redaction tokens passes."""
        engine = create_redaction_engine()

        leaks = engine.verify_redaction("Key: <API_KEY_1>")

        assert len(leaks) == 0

    def test_verify_aws_key(self):
        """Verify detects AWS key."""
        engine = create_redaction_engine()

        leaks = engine.verify_redaction("AKIAIOSFODNN7EXAMPLE")

        assert len(leaks) > 0

    def test_verify_multiple_secrets(self):
        """Verify detects multiple secrets."""
        engine = create_redaction_engine()
        text = "Key1: AKIAIOSFODNN7EXAMPLE Key2: AKIAIOSFODNN7ANOTHER"

        leaks = engine.verify_redaction(text)

        assert len(leaks) >= 1
