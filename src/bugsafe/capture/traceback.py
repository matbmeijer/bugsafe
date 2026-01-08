"""Traceback parser - Extract structured information from Python tracebacks."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

ANSI_PATTERN = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]|\x1b\][^\x07]*\x07")

TRACEBACK_HEADER = re.compile(
    r"^Traceback \(most recent call last\):?\s*$", re.MULTILINE
)

FRAME_PATTERN = re.compile(
    r'^\s*File "(?P<file>[^"]+)", line (?P<line>\d+)(?:, in (?P<function>\S+))?',
    re.MULTILINE,
)

EXCEPTION_PATTERN = re.compile(
    r"^(?P<type>[A-Za-z_][A-Za-z0-9_.]*):\s*(?P<message>.*)$",
    re.MULTILINE,
)

EXCEPTION_NO_MSG_PATTERN = re.compile(
    r"^(?P<type>[A-Za-z_][A-Za-z0-9_.]*)$",
    re.MULTILINE,
)

SYNTAX_ERROR_PATTERN = re.compile(
    r'^\s*File "(?P<file>[^"]+)", line (?P<line>\d+)\n'
    r"(?P<code>.*)\n"
    r"\s*(?P<caret>\^+)?\n"
    r"(?P<type>SyntaxError|IndentationError|TabError):\s*(?P<message>.*)",
    re.MULTILINE,
)

CHAINED_CAUSE = re.compile(
    r"^\nThe above exception was the direct cause of the following exception:\n",
    re.MULTILINE,
)

CHAINED_CONTEXT = re.compile(
    r"^\nDuring handling of the above exception, another exception occurred:\n",
    re.MULTILINE,
)

RECURSION_TRUNCATION = re.compile(
    r"^\s*\[Previous line repeated (\d+) more times?\]",
    re.MULTILINE,
)

LOCAL_VAR_PATTERN = re.compile(
    r"^\s{4,}(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(?P<value>.+)$",
    re.MULTILINE,
)


@dataclass
class Frame:
    """A single stack frame in a traceback.

    Attributes:
        file: File path where the frame originated.
        line: Line number in the file.
        function: Function name (may be None for module-level code).
        code: The source code line (may be None).
        locals: Local variables captured in the frame (if available).
    """

    file: str
    line: int
    function: str | None = None
    code: str | None = None
    locals: dict[str, str] = field(default_factory=dict)


@dataclass
class ParsedTraceback:
    """Structured representation of a Python traceback.

    Attributes:
        exception_type: The type of exception raised.
        message: The exception message.
        frames: List of stack frames (innermost last).
        cause: Chained exception (__cause__).
        context: Chained exception (__context__).
        partial: Whether parsing was incomplete.
        recursion_depth: Estimated recursion depth if truncated.
    """

    exception_type: str
    message: str
    frames: list[Frame] = field(default_factory=list)
    cause: ParsedTraceback | None = None
    context: ParsedTraceback | None = None
    partial: bool = False
    recursion_depth: int | None = None


def _strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from text."""
    return ANSI_PATTERN.sub("", text)


def _find_traceback_blocks(text: str) -> list[tuple[int, int]]:
    """Find start and end positions of traceback blocks.

    Returns:
        List of (start, end) tuples for each traceback block.
    """
    blocks: list[tuple[int, int]] = []

    for match in TRACEBACK_HEADER.finditer(text):
        start = match.start()
        remaining = text[match.end() :]

        end_pos = _find_traceback_end(remaining)
        end = match.end() + end_pos
        blocks.append((start, end))

    return blocks


def _find_traceback_end(text: str) -> int:
    """Find the end position of a traceback starting after the header."""
    lines = text.split("\n")
    last_valid_pos = 0
    current_pos = 0
    in_frame = False

    for line in lines:
        line_len = len(line) + 1

        if FRAME_PATTERN.match(line):
            in_frame = True
            last_valid_pos = current_pos + line_len
        elif in_frame and line.startswith("    ") and line.strip():
            last_valid_pos = current_pos + line_len
        elif EXCEPTION_PATTERN.match(line) or EXCEPTION_NO_MSG_PATTERN.match(line):
            last_valid_pos = current_pos + line_len
            break
        elif RECURSION_TRUNCATION.match(line):
            last_valid_pos = current_pos + line_len
        elif line.strip() == "" and in_frame:
            pass
        elif in_frame and not line.startswith(" "):
            if EXCEPTION_PATTERN.match(line) or EXCEPTION_NO_MSG_PATTERN.match(line):
                last_valid_pos = current_pos + line_len
            break

        current_pos += line_len

    return last_valid_pos


def _parse_frames(text: str) -> tuple[list[Frame], int | None]:
    """Parse stack frames from traceback text.

    Returns:
        Tuple of (frames_list, recursion_depth).
    """
    frames: list[Frame] = []
    recursion_depth: int | None = None
    lines = text.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i]
        frame_match = FRAME_PATTERN.match(line)

        if frame_match:
            file_path = frame_match.group("file")
            line_num = int(frame_match.group("line"))
            function = frame_match.group("function")

            code: str | None = None
            frame_locals: dict[str, str] = {}

            if i + 1 < len(lines):
                next_line = lines[i + 1]
                if next_line.startswith("    ") and not FRAME_PATTERN.match(next_line):
                    code = next_line.strip()
                    i += 1

                    j = i + 1
                    while j < len(lines):
                        local_match = LOCAL_VAR_PATTERN.match(lines[j])
                        if local_match:
                            name = local_match.group("name")
                            frame_locals[name] = local_match.group("value")
                            i = j
                            j += 1
                        else:
                            break

            frames.append(
                Frame(
                    file=file_path,
                    line=line_num,
                    function=function,
                    code=code,
                    locals=frame_locals,
                )
            )

        recursion_match = RECURSION_TRUNCATION.match(line)
        if recursion_match:
            recursion_depth = int(recursion_match.group(1))

        i += 1

    return frames, recursion_depth


def _parse_exception(text: str) -> tuple[str, str]:
    """Extract exception type and message from traceback text.

    Returns:
        Tuple of (exception_type, message).
    """
    lines = text.strip().split("\n")

    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue

        exc_match = EXCEPTION_PATTERN.match(line)
        if exc_match:
            return exc_match.group("type"), exc_match.group("message")

        no_msg_match = EXCEPTION_NO_MSG_PATTERN.match(line)
        if no_msg_match:
            return no_msg_match.group("type"), ""

    return "Unknown", ""


def _parse_single_traceback(text: str) -> ParsedTraceback:
    """Parse a single traceback block (no chained exceptions)."""
    frames, recursion_depth = _parse_frames(text)
    exception_type, message = _parse_exception(text)

    return ParsedTraceback(
        exception_type=exception_type,
        message=message,
        frames=frames,
        recursion_depth=recursion_depth,
        partial=len(frames) == 0 and exception_type == "Unknown",
    )


def _split_chained_tracebacks(text: str) -> tuple[str, str | None, str | None]:
    """Split text by chained exception markers.

    Returns:
        Tuple of (main_tb, cause_tb, context_tb).
    """
    cause_match = CHAINED_CAUSE.search(text)
    context_match = CHAINED_CONTEXT.search(text)

    if cause_match:
        cause_text = text[: cause_match.start()]
        main_text = text[cause_match.end() :]
        return main_text, cause_text, None

    if context_match:
        context_text = text[: context_match.start()]
        main_text = text[context_match.end() :]
        return main_text, None, context_text

    return text, None, None


def extract_traceback(stderr: str) -> ParsedTraceback | None:
    """Extract and parse Python traceback from stderr.

    This function finds the last complete traceback in the input
    and parses it into a structured format. It handles:
    - Standard CPython tracebacks
    - Chained exceptions (__cause__ and __context__)
    - Recursion errors with truncation
    - Rich/better_exceptions local variable display
    - ANSI escape codes

    Args:
        stderr: The stderr output to parse.

    Returns:
        ParsedTraceback if a traceback was found, None otherwise.
    """
    if not stderr or not stderr.strip():
        return None

    text = _strip_ansi(stderr)

    main_text, cause_text, context_text = _split_chained_tracebacks(text)

    blocks = _find_traceback_blocks(main_text)
    if not blocks:
        return None

    start, end = blocks[-1]
    tb_text = main_text[start:end]

    result = _parse_single_traceback(tb_text)

    if cause_text:
        cause_blocks = _find_traceback_blocks(cause_text)
        if cause_blocks:
            cause_start, cause_end = cause_blocks[-1]
            result.cause = _parse_single_traceback(cause_text[cause_start:cause_end])

    if context_text:
        context_blocks = _find_traceback_blocks(context_text)
        if context_blocks:
            ctx_start, ctx_end = context_blocks[-1]
            result.context = _parse_single_traceback(context_text[ctx_start:ctx_end])

    return result


def extract_syntax_error(stderr: str) -> ParsedTraceback | None:
    """Extract syntax error from stderr (special format).

    Syntax errors have a different format than regular tracebacks:
      File "foo.py", line 1
        print(
              ^
    SyntaxError: unexpected EOF while parsing

    Args:
        stderr: The stderr output to parse.

    Returns:
        ParsedTraceback if a syntax error was found, None otherwise.
    """
    if not stderr:
        return None

    text = _strip_ansi(stderr)
    match = SYNTAX_ERROR_PATTERN.search(text)

    if not match:
        return None

    frame = Frame(
        file=match.group("file"),
        line=int(match.group("line")),
        code=match.group("code").strip() if match.group("code") else None,
    )

    return ParsedTraceback(
        exception_type=match.group("type"),
        message=match.group("message"),
        frames=[frame],
    )
