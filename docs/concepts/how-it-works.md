# How It Works

bugsafe creates safe-to-share crash bundles by capturing, redacting, and packaging debugging information.

## Pipeline Overview

``` mermaid
flowchart LR
  A["🎯 Capture"] --> B["🔒 Redact"]
  B --> C["📦 Bundle"]
  C --> D["📄 Render"]
```

## 1. Capture

When you run `bugsafe run -- python script.py`:

``` mermaid
flowchart TB
  subgraph Capture["🎯 Capture Phase"]
    A["Run Command"] --> B["Collect stdout/stderr"]
    B --> C["Parse Traceback"]
    C --> D["Snapshot Environment"]
  end
  D --> E["Python version, packages, git info"]
```

- **Command execution** — Spawns the command as a subprocess
- **Output capture** — Collects stdout and stderr
- **Traceback parsing** — Extracts Python exception details
- **Environment snapshot** — Captures Python version, packages, git info

## 2. Redact

Before storing anything:

``` mermaid
flowchart LR
  subgraph Input
    A["Raw Text"]
  end
  subgraph Redaction["🔒 Redaction Engine"]
    B["Pattern Matching\n25+ patterns"]
    C["Tokenization\nsk-abc → API_KEY_1"]
    D["Path Anonymization\n/home/user → ~"]
  end
  subgraph Output
    E["Safe Text"]
  end
  A --> B --> C --> D --> E
```

- **Pattern matching** — Scans text for 25+ secret patterns
- **Tokenization** — Replaces secrets with deterministic tokens
- **Path anonymization** — Removes usernames from file paths
- **Correlation preservation** — Same secret = same token

## 3. Bundle

Creates a `.bugbundle` file (ZIP format):

``` mermaid
flowchart TB
  subgraph Bundle["📦 crash.bugbundle"]
    M["manifest.json\nMetadata & checksums"]
    T["traceback.json\nParsed exception"]
    E["environment.json\nSystem info"]
    O["output.txt\nstdout/stderr"]
    A["attachments/\nAdditional files"]
  end
```

## 4. Render

Outputs the bundle in various formats:

``` mermaid
flowchart LR
  A["📦 Bundle"] --> B{"Format?"}
  B -->|"--format md"| C["📝 Markdown\nGitHub issues"]
  B -->|"--format json"| D["🔧 JSON\nTools & APIs"]
  B -->|"--llm"| E["🤖 LLM Context\nToken-optimized"]
```

## Key Principles

### Privacy by Default

All sensitive data is redacted before storage. The original secrets are never written to disk.

### Correlation Preservation

The same secret produces the same token within a bundle:

``` mermaid
flowchart LR
  subgraph Original["Original Code"]
    A["API_KEY=sk-abc123"]
    B["headers={'auth': 'sk-abc123'}"]
  end
  subgraph Redacted["Redacted Output"]
    C["API_KEY=&lt;API_KEY_1&gt;"]
    D["headers={'auth': '&lt;API_KEY_1&gt;'}"]
  end
  A -->|same token| C
  B -->|same token| D
```

This helps debuggers understand relationships without exposing the actual values.

### Non-Reversible

Tokens cannot be reversed to the original value. Only a salted hash is stored for verification.

## See Also

- [Security Model](security-model.md)
- [Tokenization](tokenization.md)
- [Bundle Format](bundle-format.md)
