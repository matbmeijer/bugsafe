# Bundle Format

The `.bugbundle` format is a ZIP archive containing structured debugging information.

## Structure

```text
example.bugbundle (ZIP)
├── manifest.json         # Bundle metadata
├── traceback.json        # Parsed exception
├── environment.json      # System information
├── output.txt            # Captured stdout/stderr
├── command.json          # Command details
└── attachments/          # Additional files
    ├── config.yaml
    └── app.log
```

## Manifest

`manifest.json` contains:

```json
{
  "version": "1.0",
  "created_at": "2024-01-15T10:30:00Z",
  "bugsafe_version": "0.1.0",
  "redaction_salt_hash": "sha256:abc123...",
  "checksums": {
    "traceback.json": "sha256:...",
    "environment.json": "sha256:..."
  }
}
```

## Traceback

`traceback.json` contains parsed exception:

```json
{
  "exception_type": "ConnectionError",
  "exception_message": "Failed to connect to <API_HOST_1>",
  "frames": [
    {
      "filename": "<PROJECT>/app.py",
      "lineno": 42,
      "function": "connect",
      "code": "response = requests.get(url)"
    }
  ]
}
```

## Environment

`environment.json` captures:

```json
{
  "python_version": "3.12.0",
  "platform": "linux",
  "packages": {
    "requests": "2.31.0",
    "pydantic": "2.5.0"
  },
  "git": {
    "branch": "main",
    "commit": "abc123",
    "dirty": false
  }
}
```

## Security

- All content is redacted before storage
- Checksums verify integrity
- Salt hash enables verification without exposing secrets

## Reading Bundles

```python
from bugsafe.bundle import BugBundle

bundle = BugBundle.load("crash.bugbundle")
print(bundle.traceback.exception_type)
print(bundle.environment.python_version)
```

## See Also

- [API Reference](../reference/api/bundle.md)
- [How It Works](how-it-works.md)
