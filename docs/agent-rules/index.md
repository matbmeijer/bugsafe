# Agent Rules for AI IDEs

Pre-configured rules for AI-powered IDEs and coding assistants.

## Supported Platforms

| Platform | Rule Location | Format |
|----------|---------------|--------|
| Claude Code | `.claude/CLAUDE.md` + `.claude/rules/` | YAML frontmatter with paths |
| Cursor | `.cursor/rules/` | Folder-based RULE.md |
| Windsurf | `.windsurf/workflows/` | Workflow markdown |
| Generic | `AGENTS.md` | Simple markdown |

## Quick Setup

### Option 1: Copy from docs

Copy the rules from this directory to your IDE-specific location:

```bash
# Claude Code
cp docs/agent-rules/*.md .claude/rules/

# Cursor
mkdir -p .cursor/rules/bugsafe
cp docs/agent-rules/bugsafe.md .cursor/rules/bugsafe/RULE.md
```

### Option 2: Symlink

```bash
# Claude Code
ln -s docs/agent-rules .claude/rules

# Cursor
ln -s ../../docs/agent-rules/bugsafe.md .cursor/rules/bugsafe/RULE.md
```

## MCP Integration

All platforms support MCP servers. Add to your configuration:

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

## Available Rules

- [bugsafe.md](bugsafe.md) — Main bugsafe agent instructions
- [code-style.md](code-style.md) — Python code style guidelines
- [testing.md](testing.md) — Testing conventions
- [redaction.md](redaction.md) — Redaction engine details
