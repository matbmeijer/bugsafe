"""Tests for bugsafe pytest plugin."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from bugsafe.pytest_plugin import (
    BugsafeConfig,
    BugsafePlugin,
    CapturedOutput,
    pytest_addoption,
    pytest_configure,
)


class TestBugsafeConfig:
    """Tests for BugsafeConfig dataclass."""

    def test_bugsafe_config_defaults(self):
        """Default config has correct values."""
        config = BugsafeConfig()

        assert config.enabled is False
        assert config.on_fail_only is False
        assert config.output_dir == Path(".bugsafe")

    def test_bugsafe_config_custom_output(self):
        """Custom output directory is set correctly."""
        config = BugsafeConfig(
            enabled=True,
            on_fail_only=True,
            output_dir=Path("/custom/path"),
        )

        assert config.enabled is True
        assert config.on_fail_only is True
        assert config.output_dir == Path("/custom/path")


class TestCapturedOutput:
    """Tests for CapturedOutput dataclass."""

    def test_captured_output_defaults(self):
        """Default captured output has correct values."""
        output = CapturedOutput()

        assert output.stdout == ""
        assert output.stderr == ""
        assert output.failures == []

    def test_captured_output_with_data(self):
        """CapturedOutput stores data correctly."""
        output = CapturedOutput(
            stdout="test output",
            stderr="test error",
            failures=["test failure 1", "test failure 2"],
        )

        assert output.stdout == "test output"
        assert output.stderr == "test error"
        assert len(output.failures) == 2


class TestBugsafePlugin:
    """Tests for BugsafePlugin class."""

    def test_plugin_should_create_bundle_disabled(self):
        """Plugin doesn't create bundle when disabled."""
        config = BugsafeConfig(enabled=False)
        plugin = BugsafePlugin(config)

        assert plugin._should_create_bundle(exitstatus=1) is False

    def test_plugin_should_create_bundle_enabled(self):
        """Plugin creates bundle when enabled."""
        config = BugsafeConfig(enabled=True)
        plugin = BugsafePlugin(config)

        assert plugin._should_create_bundle(exitstatus=0) is True
        assert plugin._should_create_bundle(exitstatus=1) is True

    def test_plugin_should_create_bundle_on_fail_only(self):
        """Plugin creates bundle only on failure when on_fail_only is set."""
        config = BugsafeConfig(enabled=True, on_fail_only=True)
        plugin = BugsafePlugin(config)

        assert plugin._should_create_bundle(exitstatus=0) is False
        assert plugin._should_create_bundle(exitstatus=1) is True

    def test_plugin_pytest_runtest_logreport_captures_failure(self):
        """Plugin captures failed test reports."""
        config = BugsafeConfig(enabled=True)
        plugin = BugsafePlugin(config)

        report = MagicMock()
        report.failed = True
        report.when = "call"
        report.nodeid = "test_example.py::test_func"
        report.longreprtext = "AssertionError: expected 1, got 2"

        plugin.pytest_runtest_logreport(report)

        assert len(plugin.captured.failures) == 1
        assert "test_example.py::test_func" in plugin.captured.failures[0]

    def test_plugin_pytest_runtest_logreport_ignores_passed(self):
        """Plugin ignores passed test reports."""
        config = BugsafeConfig(enabled=True)
        plugin = BugsafePlugin(config)

        report = MagicMock()
        report.failed = False
        report.when = "call"

        plugin.pytest_runtest_logreport(report)

        assert len(plugin.captured.failures) == 0

    def test_plugin_pytest_runtest_logreport_ignores_setup(self):
        """Plugin ignores setup phase reports."""
        config = BugsafeConfig(enabled=True)
        plugin = BugsafePlugin(config)

        report = MagicMock()
        report.failed = True
        report.when = "setup"

        plugin.pytest_runtest_logreport(report)

        assert len(plugin.captured.failures) == 0

    def test_plugin_pytest_terminal_summary_captures_output(self):
        """Plugin captures terminal output."""
        config = BugsafeConfig(enabled=True)
        plugin = BugsafePlugin(config)

        terminalreporter = MagicMock()
        terminalreporter._tw._file.getvalue.return_value = "test output"

        plugin.pytest_terminal_summary(terminalreporter)

        assert plugin.captured.stdout == "test output"

    def test_plugin_pytest_terminal_summary_no_tw(self):
        """Plugin handles missing _tw attribute."""
        config = BugsafeConfig(enabled=True)
        plugin = BugsafePlugin(config)

        terminalreporter = MagicMock(spec=[])

        plugin.pytest_terminal_summary(terminalreporter)

        assert plugin.captured.stdout == ""

    def test_plugin_pytest_sessionfinish_disabled(self):
        """Plugin doesn't create bundle when disabled."""
        config = BugsafeConfig(enabled=False)
        plugin = BugsafePlugin(config)

        session = MagicMock()

        with patch.object(plugin, "_create_bundle") as mock_create:
            plugin.pytest_sessionfinish(session, exitstatus=1)
            mock_create.assert_not_called()

    def test_plugin_pytest_sessionfinish_creates_bundle(self, tmp_path):
        """Plugin creates bundle on session finish."""
        config = BugsafeConfig(enabled=True, output_dir=tmp_path)
        plugin = BugsafePlugin(config)
        plugin.captured.failures.append("test failure")

        session = MagicMock()
        session.config.args = ["tests/"]

        plugin.pytest_sessionfinish(session, exitstatus=1)

        bundles = list(tmp_path.glob("*.bugbundle"))
        assert len(bundles) == 1


class TestPytestHooks:
    """Tests for pytest hook functions."""

    def test_pytest_addoption(self):
        """pytest_addoption adds correct options."""
        parser = MagicMock()
        group = MagicMock()
        parser.getgroup.return_value = group

        pytest_addoption(parser)

        parser.getgroup.assert_called_once_with("bugsafe", "bugsafe crash capture")
        assert group.addoption.call_count == 3

    def test_pytest_configure_disabled(self):
        """pytest_configure doesn't register plugin when disabled."""
        config = MagicMock()
        config.getoption.side_effect = lambda opt, default=None: {
            "--bugsafe": False,
            "--bugsafe-on-fail": False,
            "--bugsafe-output": ".bugsafe",
        }.get(opt, default)

        pytest_configure(config)

        config.pluginmanager.register.assert_not_called()

    def test_pytest_configure_enabled(self):
        """pytest_configure registers plugin when enabled."""
        config = MagicMock()
        config.getoption.side_effect = lambda opt, default=None: {
            "--bugsafe": True,
            "--bugsafe-on-fail": False,
            "--bugsafe-output": ".bugsafe",
        }.get(opt, default)

        pytest_configure(config)

        config.pluginmanager.register.assert_called_once()

    def test_pytest_configure_on_fail_only(self):
        """pytest_configure registers plugin when on_fail_only is set."""
        config = MagicMock()
        config.getoption.side_effect = lambda opt, default=None: {
            "--bugsafe": False,
            "--bugsafe-on-fail": True,
            "--bugsafe-output": "/custom/path",
        }.get(opt, default)

        pytest_configure(config)

        config.pluginmanager.register.assert_called_once()
        call_args = config.pluginmanager.register.call_args
        plugin = call_args[0][0]
        assert plugin.config.on_fail_only is True
        assert plugin.config.output_dir == Path("/custom/path")
