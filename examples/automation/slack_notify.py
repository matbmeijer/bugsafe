"""Post crash bundle to Slack on failure.

Usage:
    export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
    python slack_notify.py "python my_script.py"
"""

from __future__ import annotations

import json
import subprocess
import sys
import urllib.request
from pathlib import Path
from tempfile import NamedTemporaryFile


def run_with_bugsafe(command: str) -> tuple[int, Path | None]:
    """Run command with bugsafe, return exit code and bundle path."""
    with NamedTemporaryFile(suffix=".bugbundle", delete=False) as f:
        bundle_path = Path(f.name)

    result = subprocess.run(
        ["bugsafe", "run", "-o", str(bundle_path), "--"] + command.split(),
        capture_output=True,
        text=True,
    )

    if result.returncode != 0 and bundle_path.exists():
        return result.returncode, bundle_path

    return result.returncode, None


def post_to_slack(webhook_url: str, bundle_path: Path) -> None:
    """Post bundle summary to Slack."""
    if not webhook_url.startswith("https://"):
        raise ValueError("Webhook URL must use HTTPS")

    result = subprocess.run(
        ["bugsafe", "render", str(bundle_path), "--llm"],
        capture_output=True,
        text=True,
    )

    payload = {
        "text": f"🐛 Crash detected\n```{result.stdout[:2000]}```",
    }

    req = urllib.request.Request(  # noqa: S310
        webhook_url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    urllib.request.urlopen(req)  # noqa: S310


def main() -> None:
    import os

    if len(sys.argv) < 2:
        print("Usage: python slack_notify.py <command>")
        sys.exit(1)

    command = " ".join(sys.argv[1:])
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL")

    if not webhook_url:
        print("SLACK_WEBHOOK_URL not set")
        sys.exit(1)

    exit_code, bundle_path = run_with_bugsafe(command)

    if bundle_path:
        post_to_slack(webhook_url, bundle_path)
        print(f"Posted crash to Slack: {bundle_path}")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
