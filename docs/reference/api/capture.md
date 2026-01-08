# Capture API

The capture module executes commands and captures their output.

## Overview

```python
from bugsafe.capture.runner import run_command, CaptureConfig

# Run with default settings
result = run_command(["python", "script.py"])
print(result.exit_code)
print(result.stdout)

# Run with custom config
config = CaptureConfig(timeout=60, max_output_bytes=1_000_000)
result = run_command(["python", "script.py"], config)
```

## CaptureConfig

Configuration for command capture.

::: bugsafe.capture.runner.CaptureConfig
    options:
      show_source: false
      heading_level: 3

## CaptureResult

Result of command execution.

::: bugsafe.capture.runner.CaptureResult
    options:
      show_source: false
      heading_level: 3

## run_command

Execute a command and capture output.

::: bugsafe.capture.runner.run_command
    options:
      show_source: false
      heading_level: 3
