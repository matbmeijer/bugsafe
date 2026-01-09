"""MCP server module for bugsafe.

Requires the `mcp` optional dependency:
    pip install bugsafe[mcp]
"""

try:
    from bugsafe.mcp.server import mcp, run_server

    __all__ = ["mcp", "run_server"]
except ImportError:
    __all__ = []
