"""Demo script that crashes with secrets in output.

Usage:
    bugsafe run -- python examples/basic/crash_demo.py
    bugsafe render bug.bugbundle
"""

import os


def fetch_data(api_key: str, endpoint: str) -> dict:
    """Simulate API call that fails."""
    print(f"Connecting to {endpoint}...")
    print(f"Using API key: {api_key}")
    raise ConnectionError(f"Failed to connect to {endpoint} with key {api_key}")


def main() -> None:
    api_key = os.getenv("API_KEY", "sk-proj-abc123xyz789secret")
    endpoint = "https://api.example.com/v1/data"

    fetch_data(api_key, endpoint)


if __name__ == "__main__":
    main()
