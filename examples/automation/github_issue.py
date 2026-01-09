"""Create GitHub issue from crash bundle.

Usage:
    export GITHUB_TOKEN="ghp_..."
    python github_issue.py owner/repo bug.bugbundle
"""

from __future__ import annotations

import json
import subprocess
import sys
import urllib.request
from pathlib import Path


def render_bundle(bundle_path: Path) -> str:
    """Render bundle to markdown."""
    result = subprocess.run(
        ["bugsafe", "render", str(bundle_path)],
        capture_output=True,
        text=True,
    )
    return result.stdout


def create_issue(repo: str, title: str, body: str, token: str) -> str:
    """Create GitHub issue, return URL."""
    url = f"https://api.github.com/repos/{repo}/issues"

    payload = {"title": title, "body": body, "labels": ["bug", "crash"]}

    req = urllib.request.Request(  # noqa: S310
        url,
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
        },
    )

    with urllib.request.urlopen(req) as response:  # noqa: S310
        data = json.loads(response.read())
        return data["html_url"]


def main() -> None:
    import os

    if len(sys.argv) < 3:
        print("Usage: python github_issue.py <owner/repo> <bundle.bugbundle>")
        sys.exit(1)

    repo = sys.argv[1]
    bundle_path = Path(sys.argv[2])
    token = os.environ.get("GITHUB_TOKEN")

    if not token:
        print("GITHUB_TOKEN not set")
        sys.exit(1)

    if not bundle_path.exists():
        print(f"Bundle not found: {bundle_path}")
        sys.exit(1)

    body = render_bundle(bundle_path)
    title = f"Crash report: {bundle_path.stem}"

    issue_url = create_issue(repo, title, body, token)
    print(f"Created issue: {issue_url}")


if __name__ == "__main__":
    main()
