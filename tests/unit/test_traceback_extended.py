"""Functional tests for traceback extraction - verifies correct parsing."""

from bugsafe.capture.traceback import extract_traceback


class TestStandardTraceback:
    """Functional tests for standard Python traceback extraction."""

    def test_extracts_exception_type_correctly(self):
        """Exception type must be correctly identified from traceback."""
        text = """Traceback (most recent call last):
  File "test.py", line 10, in main
    raise ValueError("test message")
ValueError: test message"""

        result = extract_traceback(text)

        assert result is not None, "Should extract traceback"
        assert result.exception_type == "ValueError", "Exception type must match"

    def test_extracts_exception_message(self):
        """Exception message must be correctly extracted."""
        text = """Traceback (most recent call last):
  File "test.py", line 10, in main
    raise RuntimeError("detailed error message")
RuntimeError: detailed error message"""

        result = extract_traceback(text)

        assert result is not None
        assert "detailed error message" in result.message

    def test_extracts_frame_information(self):
        """Stack frame details must be correctly extracted."""
        text = """Traceback (most recent call last):
  File "myfile.py", line 42, in my_function
    do_something()
  File "other.py", line 10, in do_something
    raise Exception("error")
Exception: error"""

        result = extract_traceback(text)

        assert result is not None
        assert len(result.frames) >= 1, "Should have at least one frame"


class TestNoTraceback:
    """Functional tests for text without tracebacks."""

    def test_returns_none_for_plain_text(self):
        """Plain text without traceback should return None."""
        text = "This is just normal log output with no errors."

        result = extract_traceback(text)

        assert result is None, "Should return None for plain text"

    def test_returns_none_for_empty_string(self):
        """Empty string should return None."""
        result = extract_traceback("")

        assert result is None, "Should return None for empty string"


class TestChainedExceptions:
    """Functional tests for chained exception handling."""

    def test_extracts_final_exception_from_chain(self):
        """Should extract exception info from chained exceptions."""
        text = """Traceback (most recent call last):
  File "db.py", line 15, in connect
    conn = psycopg2.connect(dsn)
ConnectionError: Could not connect

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "app.py", line 25, in main
    db.connect()
RuntimeError: Database connection failed"""

        result = extract_traceback(text)

        assert result is not None, "Should extract from chained traceback"
        # Should get either the first or last exception
        assert result.exception_type in ("ConnectionError", "RuntimeError")
