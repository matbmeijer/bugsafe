"""Sample tracebacks for testing."""

STANDARD_CPYTHON = """\
Traceback (most recent call last):
  File "/home/user/project/main.py", line 25, in main
    result = process_data(data)
  File "/home/user/project/processor.py", line 42, in process_data
    return transform(item)
  File "/home/user/project/processor.py", line 15, in transform
    raise ValueError("Invalid data format")
ValueError: Invalid data format
"""

RICH_TRACEBACK_WITH_LOCALS = """\
Traceback (most recent call last):
  File "/home/user/project/app.py", line 10, in calculate
    result = x / y
    x = 10
    y = 0
ZeroDivisionError: division by zero
"""

PYTEST_FAILURE = """\
============================= FAILURES =============================
_________________________ test_example _________________________

    def test_example():
>       assert func(1) == 2
E       assert 1 == 2
E        +  where 1 = func(1)

tests/test_example.py:5: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_example.py::test_example - assert 1 == 2
"""

SYNTAX_ERROR_UNCLOSED_PAREN = """\
  File "script.py", line 5
    print(x
          ^
SyntaxError: unexpected EOF while parsing
"""

SYNTAX_ERROR_INVALID_SYNTAX = """\
  File "script.py", line 3
    def foo(
           ^
SyntaxError: invalid syntax
"""

INDENTATION_ERROR = """\
  File "script.py", line 4
    print("hello")
    ^
IndentationError: unexpected indent
"""

CHAINED_EXCEPTION_CAUSE = """\
Traceback (most recent call last):
  File "db.py", line 15, in connect
    conn = psycopg2.connect(dsn)
  File "psycopg2/__init__.py", line 127, in connect
    raise OperationalError("connection refused")
psycopg2.OperationalError: connection refused

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "app.py", line 25, in init_db
    db = connect_database()
  File "app.py", line 10, in connect_database
    raise DatabaseError("Failed to connect") from e
app.DatabaseError: Failed to connect
"""

CHAINED_EXCEPTION_CONTEXT = """\
Traceback (most recent call last):
  File "handler.py", line 10, in process
    data = json.loads(raw)
  File "json/__init__.py", line 357, in loads
    return _default_decoder.decode(s)
json.JSONDecodeError: Expecting value: line 1 column 1 (char 0)

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "handler.py", line 15, in process
    raise ProcessingError("Invalid JSON input")
handler.ProcessingError: Invalid JSON input
"""

RECURSION_ERROR = """\
Traceback (most recent call last):
  File "recursive.py", line 5, in factorial
    return n * factorial(n - 1)
  File "recursive.py", line 5, in factorial
    return n * factorial(n - 1)
  File "recursive.py", line 5, in factorial
    return n * factorial(n - 1)
  [Previous line repeated 997 more times]
  File "recursive.py", line 3, in factorial
    if n <= 1:
RecursionError: maximum recursion depth exceeded in comparison
"""

MULTILINE_EXCEPTION_MESSAGE = """\
Traceback (most recent call last):
  File "validator.py", line 50, in validate
    raise ValidationError(errors)
ValidationError: Multiple validation errors:
  - Field 'name' is required
  - Field 'email' must be a valid email
  - Field 'age' must be a positive integer
"""

ASSERTION_ERROR_WITH_CONTEXT = """\
Traceback (most recent call last):
  File "test_math.py", line 15, in test_add
    assert add(2, 2) == 5, "Expected 2+2 to equal 5"
AssertionError: Expected 2+2 to equal 5
"""

ATTRIBUTE_ERROR = """\
Traceback (most recent call last):
  File "user.py", line 20, in get_name
    return self.user.name
AttributeError: 'NoneType' object has no attribute 'name'
"""

KEY_ERROR = """\
Traceback (most recent call last):
  File "config.py", line 10, in get_setting
    return settings['database']['host']
KeyError: 'host'
"""

TYPE_ERROR = """\
Traceback (most recent call last):
  File "math_ops.py", line 5, in add
    return a + b
TypeError: unsupported operand type(s) for +: 'int' and 'str'
"""

IMPORT_ERROR = """\
Traceback (most recent call last):
  File "app.py", line 1, in <module>
    from nonexistent_module import something
ModuleNotFoundError: No module named 'nonexistent_module'
"""

FILE_NOT_FOUND = """\
Traceback (most recent call last):
  File "reader.py", line 8, in read_config
    with open('/etc/myapp/config.yaml') as f:
FileNotFoundError: [Errno 2] No such file or directory: '/etc/myapp/config.yaml'
"""

PERMISSION_ERROR = """\
Traceback (most recent call last):
  File "writer.py", line 12, in write_log
    with open('/var/log/app.log', 'w') as f:
PermissionError: [Errno 13] Permission denied: '/var/log/app.log'
"""

OS_ERROR_CONNECTION_REFUSED = """\
Traceback (most recent call last):
  File "client.py", line 25, in connect
    sock.connect(('localhost', 8080))
ConnectionRefusedError: [Errno 111] Connection refused
"""

TIMEOUT_ERROR = """\
Traceback (most recent call last):
  File "http_client.py", line 30, in fetch
    response = requests.get(url, timeout=5)
  File "requests/api.py", line 75, in get
    return request('get', url, **kwargs)
requests.exceptions.ReadTimeout: HTTPConnectionPool(host='api.example.com', port=80): Read timed out. (read timeout=5)
"""

ANSI_COLORED_TRACEBACK = """\
\x1b[38;5;9mTraceback (most recent call last):\x1b[0m
  File \x1b[32m"app.py"\x1b[0m, line \x1b[33m10\x1b[0m, in \x1b[35mmain\x1b[0m
    \x1b[36mresult = calculate(x)\x1b[0m
  File \x1b[32m"math.py"\x1b[0m, line \x1b[33m5\x1b[0m, in \x1b[35mcalculate\x1b[0m
    \x1b[36mreturn 1 / value\x1b[0m
\x1b[38;5;9mZeroDivisionError\x1b[0m: \x1b[38;5;9mdivision by zero\x1b[0m
"""

UNICODE_TRACEBACK = """\
Traceback (most recent call last):
  File "/home/用户/项目/主程序.py", line 10, in 处理数据
    raise ValueError("无效的数据格式: 数据必须是整数")
ValueError: 无效的数据格式: 数据必须是整数
"""

WINDOWS_PATH_TRACEBACK = """\
Traceback (most recent call last):
  File "C:\\Users\\alice\\Projects\\myapp\\main.py", line 15, in main
    process_file(path)
  File "C:\\Users\\alice\\Projects\\myapp\\processor.py", line 8, in process_file
    raise FileNotFoundError(f"File not found: {path}")
FileNotFoundError: File not found: C:\\Users\\alice\\data\\input.txt
"""

EXCEPTION_NO_MESSAGE = """\
Traceback (most recent call last):
  File "generator.py", line 20, in next_item
    return next(self.iterator)
StopIteration
"""

EXCEPTION_GROUP_PYTHON311 = """\
  + Exception Group Traceback (most recent call last):
  |   File "async_app.py", line 25, in main
  |     async with asyncio.TaskGroup() as tg:
  |   File "asyncio/taskgroups.py", line 135, in __aexit__
  |     raise BaseExceptionGroup(msg, exceptions)
  | ExceptionGroup: unhandled errors in a TaskGroup (2 sub-exceptions)
  +-+---------------- 1 ----------------
    | Traceback (most recent call last):
    |   File "async_app.py", line 27, in main
    |     tg.create_task(task1())
    |   File "async_app.py", line 10, in task1
    |     raise ValueError("Task 1 failed")
    | ValueError: Task 1 failed
    +---------------- 2 ----------------
    | Traceback (most recent call last):
    |   File "async_app.py", line 28, in main
    |     tg.create_task(task2())
    |   File "async_app.py", line 15, in task2
    |     raise TypeError("Task 2 failed")
    | TypeError: Task 2 failed
    +------------------------------------
"""

ALL_FIXTURES = {
    "standard_cpython": STANDARD_CPYTHON,
    "rich_with_locals": RICH_TRACEBACK_WITH_LOCALS,
    "pytest_failure": PYTEST_FAILURE,
    "syntax_error_unclosed": SYNTAX_ERROR_UNCLOSED_PAREN,
    "syntax_error_invalid": SYNTAX_ERROR_INVALID_SYNTAX,
    "indentation_error": INDENTATION_ERROR,
    "chained_cause": CHAINED_EXCEPTION_CAUSE,
    "chained_context": CHAINED_EXCEPTION_CONTEXT,
    "recursion_error": RECURSION_ERROR,
    "multiline_message": MULTILINE_EXCEPTION_MESSAGE,
    "assertion_error": ASSERTION_ERROR_WITH_CONTEXT,
    "attribute_error": ATTRIBUTE_ERROR,
    "key_error": KEY_ERROR,
    "type_error": TYPE_ERROR,
    "import_error": IMPORT_ERROR,
    "file_not_found": FILE_NOT_FOUND,
    "permission_error": PERMISSION_ERROR,
    "connection_refused": OS_ERROR_CONNECTION_REFUSED,
    "timeout_error": TIMEOUT_ERROR,
    "ansi_colored": ANSI_COLORED_TRACEBACK,
    "unicode": UNICODE_TRACEBACK,
    "windows_path": WINDOWS_PATH_TRACEBACK,
    "no_message": EXCEPTION_NO_MESSAGE,
    "exception_group": EXCEPTION_GROUP_PYTHON311,
}
