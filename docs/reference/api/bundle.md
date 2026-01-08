# Bundle API

The bundle module handles the `.bugbundle` file format.

## Overview

```python
from bugsafe.bundle.schema import BugBundle, CaptureOutput
from bugsafe.bundle.writer import write_bundle
from bugsafe.bundle.reader import read_bundle

# Create a bundle
bundle = BugBundle(
    capture=CaptureOutput(
        stdout="output",
        stderr="error",
        exit_code=1,
        command=["python", "script.py"],
    )
)

# Write to file
write_bundle(bundle, "crash.bugbundle")

# Read from file
loaded = read_bundle("crash.bugbundle")
```

## Schema

### BugBundle

Complete bug bundle containing all captured data.

::: bugsafe.bundle.schema.BugBundle
    options:
      show_source: false
      heading_level: 3
      members:
        - to_dict
        - from_dict

### CaptureOutput

Captured command output.

::: bugsafe.bundle.schema.CaptureOutput
    options:
      show_source: false
      heading_level: 3

### Traceback

Structured Python traceback.

::: bugsafe.bundle.schema.Traceback
    options:
      show_source: false
      heading_level: 3

### Environment

Environment snapshot.

::: bugsafe.bundle.schema.Environment
    options:
      show_source: false
      heading_level: 3

### BundleMetadata

Bundle metadata.

::: bugsafe.bundle.schema.BundleMetadata
    options:
      show_source: false
      heading_level: 3

## Reader/Writer Functions

### read_bundle

::: bugsafe.bundle.reader.read_bundle
    options:
      show_source: false
      heading_level: 3

### create_bundle

::: bugsafe.bundle.writer.create_bundle
    options:
      show_source: false
      heading_level: 3

### validate_bundle

::: bugsafe.bundle.writer.validate_bundle
    options:
      show_source: false
      heading_level: 3
