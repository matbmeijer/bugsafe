# LLM Prompt Templates

Pre-written prompts for debugging with bugsafe bundles.

## Debug Prompt

```text
Here is a redacted crash bundle from a Python application.
Analyze the error and identify the root cause.

{bundle}

Focus on:
1. The exception type and message
2. The stack trace and code context
3. Any patterns in the redacted secrets that might indicate misconfiguration
```

## Fix Prompt

```text
Here is a redacted crash bundle. Suggest a code fix for this error.

{bundle}

Provide:
1. The likely cause
2. A minimal code change to fix the issue
3. Any configuration changes needed
```

## Explain Prompt

```text
Explain this Python error to a junior developer. Use simple language.

{bundle}

Include:
1. What went wrong in plain English
2. Why it happened
3. How to prevent it in the future
```

## Security Review Prompt

```text
Review this crash bundle for potential security issues beyond the redacted secrets.

{bundle}

Check for:
1. Information disclosure in error messages
2. Sensitive paths or configuration details
3. Patterns that suggest insecure practices
```

## Usage with CLI

Generate LLM-optimized output:

```bash
bugsafe render crash.bugbundle --llm > context.txt
```

Then paste the contents into your LLM of choice.

## Usage with MCP

If using Claude Desktop, Cursor, or Windsurf with MCP:

```json
{
  "mcpServers": {
    "bugsafe": {
      "command": "uvx",
      "args": ["bugsafe", "mcp"]
    }
  }
}
```

The MCP server provides these tools:

- `scan_secrets` — Scan text for secrets
- `capture_crash` — Run command and capture output
- `render_bundle` — Render bundle to readable format
- `audit_bundle` — Verify redaction completeness
- `create_bundle` — Create a full bundle file

## See Also

- [LLM Integration Guide](llm-integration.md)
- [CLI Reference](../reference/cli.md)
