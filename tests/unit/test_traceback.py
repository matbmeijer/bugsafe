"""Unit tests for capture/traceback.py."""

from bugsafe.capture.traceback import (
    Frame,
    ParsedTraceback,
    extract_syntax_error,
    extract_traceback,
)

SIMPLE_TRACEBACK = """\
Traceback (most recent call last):
  File "test.py", line 10, in main
    foo()
  File "test.py", line 5, in foo
    raise ValueError("test error")
ValueError: test error
"""

CHAINED_TRACEBACK_CAUSE = """\
Traceback (most recent call last):
  File "test.py", line 3, in inner
    raise ValueError("inner")
ValueError: inner

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "test.py", line 7, in outer
    raise RuntimeError("outer") from e
RuntimeError: outer
"""

CHAINED_TRACEBACK_CONTEXT = """\
Traceback (most recent call last):
  File "test.py", line 3, in inner
    raise ValueError("inner")
ValueError: inner

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "test.py", line 7, in outer
    raise RuntimeError("outer")
RuntimeError: outer
"""

RECURSION_TRACEBACK = """\
Traceback (most recent call last):
  File "test.py", line 2, in recurse
    recurse()
  File "test.py", line 2, in recurse
    recurse()
  File "test.py", line 2, in recurse
    recurse()
  [Previous line repeated 995 more times]
RecursionError: maximum recursion depth exceeded
"""

SYNTAX_ERROR = """\
  File "test.py", line 1
    print(
          ^
SyntaxError: unexpected EOF while parsing
"""

MULTILINE_EXCEPTION = """\
Traceback (most recent call last):
  File "test.py", line 5, in main
    raise ValueError("line1\\nline2\\nline3")
ValueError: line1
line2
line3
"""

NO_TRACEBACK = """\
Some random output
that is not a traceback
just stderr content
"""

ANSI_TRACEBACK = """\
\x1b[31mTraceback (most recent call last):\x1b[0m
  File "test.py", line 5, in main
    \x1b[33mraise ValueError("test")\x1b[0m
\x1b[31mValueError\x1b[0m: test
"""

EXCEPTION_NO_MESSAGE = """\
Traceback (most recent call last):
  File "test.py", line 1, in <module>
    raise StopIteration
StopIteration
"""


class TestExtractTraceback:
    """Tests for extract_traceback function."""

    def test_simple_traceback(self):
        result = extract_traceback(SIMPLE_TRACEBACK)
        assert result is not None
        assert result.exception_type == "ValueError"
        assert result.message == "test error"
        assert len(result.frames) == 2
        assert result.frames[0].file == "test.py"
        assert result.frames[0].line == 10
        assert result.frames[0].function == "main"
        assert result.frames[1].function == "foo"

    def test_chained_traceback_cause(self):
        result = extract_traceback(CHAINED_TRACEBACK_CAUSE)
        assert result is not None
        assert result.exception_type == "RuntimeError"
        assert result.message == "outer"
        assert result.cause is not None
        assert result.cause.exception_type == "ValueError"
        assert result.cause.message == "inner"

    def test_chained_traceback_context(self):
        result = extract_traceback(CHAINED_TRACEBACK_CONTEXT)
        assert result is not None
        assert result.exception_type == "RuntimeError"
        assert result.context is not None
        assert result.context.exception_type == "ValueError"

    def test_recursion_traceback(self):
        result = extract_traceback(RECURSION_TRACEBACK)
        assert result is not None
        assert result.exception_type == "RecursionError"
        assert result.recursion_depth == 995

    def test_no_traceback(self):
        result = extract_traceback(NO_TRACEBACK)
        assert result is None

    def test_empty_input(self):
        assert extract_traceback("") is None
        assert extract_traceback(None) is None

    def test_ansi_stripping(self):
        result = extract_traceback(ANSI_TRACEBACK)
        assert result is not None
        assert result.exception_type == "ValueError"
        assert "\x1b[" not in result.message

    def test_exception_no_message(self):
        result = extract_traceback(EXCEPTION_NO_MESSAGE)
        assert result is not None
        assert result.exception_type == "StopIteration"
        assert result.message == ""

    def test_frame_code_extraction(self):
        result = extract_traceback(SIMPLE_TRACEBACK)
        assert result is not None
        assert result.frames[0].code == "foo()"
        assert result.frames[1].code == 'raise ValueError("test error")'


class TestExtractSyntaxError:
    """Tests for extract_syntax_error function."""

    def test_simple_syntax_error(self):
        result = extract_syntax_error(SYNTAX_ERROR)
        assert result is not None
        assert result.exception_type == "SyntaxError"
        assert "unexpected EOF" in result.message
        assert len(result.frames) == 1
        assert result.frames[0].file == "test.py"
        assert result.frames[0].line == 1

    def test_no_syntax_error(self):
        result = extract_syntax_error(NO_TRACEBACK)
        assert result is None

    def test_empty_input(self):
        assert extract_syntax_error("") is None
        assert extract_syntax_error(None) is None


class TestFrame:
    """Tests for Frame dataclass."""

    def test_default_values(self):
        frame = Frame(file="test.py", line=1)
        assert frame.file == "test.py"
        assert frame.line == 1
        assert frame.function is None
        assert frame.code is None
        assert frame.locals == {}

    def test_with_all_values(self):
        frame = Frame(
            file="test.py",
            line=10,
            function="main",
            code="foo()",
            locals={"x": "1", "y": "2"},
        )
        assert frame.function == "main"
        assert frame.code == "foo()"
        assert frame.locals == {"x": "1", "y": "2"}


class TestParsedTraceback:
    """Tests for ParsedTraceback dataclass."""

    def test_default_values(self):
        tb = ParsedTraceback(exception_type="ValueError", message="test")
        assert tb.exception_type == "ValueError"
        assert tb.message == "test"
        assert tb.frames == []
        assert tb.cause is None
        assert tb.context is None
        assert tb.partial is False

    def test_with_frames(self):
        frames = [Frame(file="test.py", line=1)]
        tb = ParsedTraceback(
            exception_type="ValueError",
            message="test",
            frames=frames,
        )
        assert len(tb.frames) == 1


class TestMultipleTracebacks:
    """Tests for handling multiple tracebacks."""

    def test_extracts_last_traceback(self):
        text = """\
Some output
Traceback (most recent call last):
  File "first.py", line 1, in first
    pass
FirstError: first

More output
Traceback (most recent call last):
  File "second.py", line 2, in second
    pass
SecondError: second
"""
        result = extract_traceback(text)
        assert result is not None
        assert result.exception_type == "SecondError"
        assert result.frames[0].file == "second.py"


class TestEdgeCases:
    """Tests for edge cases."""

    def test_module_level_code(self):
        text = """\
Traceback (most recent call last):
  File "test.py", line 1, in <module>
    x = 1/0
ZeroDivisionError: division by zero
"""
        result = extract_traceback(text)
        assert result is not None
        assert result.frames[0].function == "<module>"

    def test_nested_exception_message(self):
        text = """\
Traceback (most recent call last):
  File "test.py", line 1, in main
    raise ValueError("Error: something went wrong")
ValueError: Error: something went wrong
"""
        result = extract_traceback(text)
        assert result is not None
        assert result.message == "Error: something went wrong"

    def test_unicode_in_traceback(self):
        text = """\
Traceback (most recent call last):
  File "テスト.py", line 1, in main
    raise ValueError("エラー: 世界")
ValueError: エラー: 世界
"""
        result = extract_traceback(text)
        assert result is not None
        assert "世界" in result.message
        assert result.frames[0].file == "テスト.py"
