"""pytest plugin for bugsafe - Capture crash bundles on test failure."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pytest


@dataclass
class BugsafeConfig:
    """Plugin configuration from pytest options."""

    enabled: bool = False
    on_fail_only: bool = False
    output_dir: Path = field(default_factory=lambda: Path(".bugsafe"))


@dataclass
class CapturedOutput:
    """Captured test session output."""

    stdout: str = ""
    stderr: str = ""
    failures: list[str] = field(default_factory=list)


class BugsafePlugin:
    """pytest plugin that captures test output and creates bundles on failure."""

    def __init__(self, config: BugsafeConfig) -> None:
        self.config = config
        self.captured = CapturedOutput()

    def pytest_runtest_logreport(self, report: pytest.TestReport) -> None:
        """Capture failed test reports."""
        if report.failed and report.when == "call":
            self.captured.failures.append(f"{report.nodeid}\n{report.longreprtext}")

    def pytest_terminal_summary(
        self, terminalreporter: pytest.TerminalReporter
    ) -> None:
        """Capture terminal output at end of session."""
        if hasattr(terminalreporter, "_tw"):
            if hasattr(terminalreporter._tw, "_file"):
                file_obj = terminalreporter._tw._file
                if hasattr(file_obj, "getvalue"):
                    self.captured.stdout = file_obj.getvalue()

    def pytest_sessionfinish(self, session: pytest.Session, exitstatus: int) -> None:
        """Create bundle if tests failed."""
        if not self._should_create_bundle(exitstatus):
            return

        self._create_bundle(session, exitstatus)

    def _should_create_bundle(self, exitstatus: int) -> bool:
        """Determine if bundle should be created."""
        if not self.config.enabled:
            return False

        if self.config.on_fail_only:
            return exitstatus != 0

        return True

    def _create_bundle(self, session: pytest.Session, exitstatus: int) -> None:
        """Create crash bundle from captured output."""
        from bugsafe import __version__
        from bugsafe.bundle.schema import (
            BugBundle,
            BundleMetadata,
            CaptureOutput,
            Environment,
            PackageInfo,
        )
        from bugsafe.bundle.writer import create_bundle
        from bugsafe.capture.environment import EnvConfig, collect_environment
        from bugsafe.redact.engine import create_redaction_engine

        self.config.output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        output_path = self.config.output_dir / f"test_failure_{timestamp}.bugbundle"

        stderr_content = "\n\n".join(self.captured.failures)

        engine = create_redaction_engine()

        redacted_stdout, _ = engine.redact(self.captured.stdout)
        redacted_stderr, _ = engine.redact(stderr_content)

        env_snapshot = collect_environment(EnvConfig())

        command = ["pytest"] + [str(arg) for arg in session.config.args]

        capture = CaptureOutput(
            stdout=redacted_stdout,
            stderr=redacted_stderr,
            exit_code=exitstatus,
            duration_ms=0,
            command=command,
            timed_out=False,
            truncated=False,
        )

        environment = Environment(
            python_version=env_snapshot.python_version,
            python_executable=env_snapshot.python_executable,
            platform=env_snapshot.platform,
            packages=[
                PackageInfo(name=p.name, version=p.version)
                for p in env_snapshot.packages
            ],
            env_vars=env_snapshot.env_vars,
            cwd=env_snapshot.cwd,
            git=None,
            virtualenv=env_snapshot.virtualenv,
            in_container=env_snapshot.in_container,
            ci_detected=env_snapshot.ci_detected,
        )

        bundle = BugBundle(
            metadata=BundleMetadata(
                created_at=datetime.now(timezone.utc),
                bugsafe_version=__version__,
                redaction_salt_hash=engine.get_salt_hash(),
            ),
            capture=capture,
            traceback=None,
            environment=environment,
            redaction_report=engine.get_redaction_summary(),
        )

        create_bundle(bundle, output_path)

        print(f"\n[bugsafe] Bundle created: {output_path}")


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add bugsafe command line options."""
    group = parser.getgroup("bugsafe", "bugsafe crash capture")

    group.addoption(
        "--bugsafe",
        action="store_true",
        default=False,
        help="Enable bugsafe crash capture for all tests",
    )

    group.addoption(
        "--bugsafe-on-fail",
        action="store_true",
        default=False,
        help="Enable bugsafe crash capture only on test failure",
    )

    group.addoption(
        "--bugsafe-output",
        action="store",
        default=".bugsafe",
        help="Output directory for crash bundles (default: .bugsafe)",
    )


def pytest_configure(config: pytest.Config) -> None:
    """Configure and register the plugin."""
    bugsafe_enabled = config.getoption("--bugsafe", default=False)
    on_fail_only = config.getoption("--bugsafe-on-fail", default=False)
    output_dir = config.getoption("--bugsafe-output", default=".bugsafe")

    if bugsafe_enabled or on_fail_only:
        plugin_config = BugsafeConfig(
            enabled=True,
            on_fail_only=on_fail_only,
            output_dir=Path(output_dir),
        )
        config.pluginmanager.register(BugsafePlugin(plugin_config), "bugsafe")
