# Render API

The render module converts bundles to various output formats.

## Overview

```python
from bugsafe.bundle.reader import read_bundle
from bugsafe.render.markdown import render_markdown

# Load and render
bundle = read_bundle("crash.bugbundle")
markdown = render_markdown(bundle)
print(markdown)
```

## Markdown Renderer

Render bundles as human-readable Markdown.

::: bugsafe.render.markdown.render_markdown
    options:
      show_source: false
      heading_level: 3
      members:
        - to_markdown

## JSON Export

::: bugsafe.render.json_export
    options:
      show_root_heading: true
      members:
        - to_json
        - to_llm_context
