"""Extended tests for environment module."""

from bugsafe.capture.environment import (
    EnvConfig,
    collect_environment,
)


class TestEnvConfig:
    """Tests for EnvConfig dataclass."""

    def test_default_config(self):
        """Default config has correct values."""
        config = EnvConfig()

        assert config.include_packages is True
        assert config.include_git is True
        assert config.max_packages == 500

    def test_custom_config(self):
        """Custom config values are set."""
        config = EnvConfig(
            include_packages=False,
            include_git=False,
            max_packages=100,
        )

        assert config.include_packages is False
        assert config.include_git is False
        assert config.max_packages == 100


class TestCollectEnvironment:
    """Tests for collect_environment function."""

    def test_collect_basic_info(self):
        """Collects basic environment info."""
        snapshot = collect_environment(EnvConfig())

        assert snapshot.python_version is not None
        assert snapshot.python_executable is not None
        assert snapshot.platform is not None
        assert snapshot.cwd is not None

    def test_collect_with_packages(self):
        """Collects environment with packages."""
        config = EnvConfig(include_packages=True)
        snapshot = collect_environment(config)

        assert isinstance(snapshot.packages, list)

    def test_collect_without_packages(self):
        """Collects environment without packages."""
        config = EnvConfig(include_packages=False)
        snapshot = collect_environment(config)

        assert snapshot.packages == []

    def test_collect_without_git(self):
        """Collects environment without git info."""
        config = EnvConfig(include_git=False)
        snapshot = collect_environment(config)

        assert snapshot.git is None

    def test_collect_with_git(self):
        """Collects environment with git info."""
        config = EnvConfig(include_git=True)
        snapshot = collect_environment(config)

        # May or may not have git info depending on environment
        assert snapshot.git is None or hasattr(snapshot.git, "branch")

    def test_snapshot_has_ci_detection(self):
        """Snapshot includes CI detection."""
        snapshot = collect_environment(EnvConfig())

        assert isinstance(snapshot.ci_detected, bool)

    def test_snapshot_has_container_detection(self):
        """Snapshot includes container detection."""
        snapshot = collect_environment(EnvConfig())

        assert isinstance(snapshot.in_container, bool)
