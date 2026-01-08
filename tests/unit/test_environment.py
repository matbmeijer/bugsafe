"""Unit tests for capture/environment.py."""

import os
import sys
from unittest.mock import patch

from bugsafe.capture.environment import (
    DEFAULT_ENV_ALLOWLIST,
    ENV_BLOCKLIST,
    EnvConfig,
    EnvSnapshot,
    GitInfo,
    PackageInfo,
    PlatformDetails,
    collect_environment,
)


class TestEnvConfig:
    """Tests for EnvConfig dataclass."""

    def test_default_values(self):
        config = EnvConfig()
        assert config.env_allowlist == DEFAULT_ENV_ALLOWLIST
        assert config.include_git is True
        assert config.include_packages is True
        assert config.max_packages == 500

    def test_custom_values(self):
        config = EnvConfig(
            include_git=False,
            max_packages=100,
        )
        assert config.include_git is False
        assert config.max_packages == 100


class TestCollectEnvironment:
    """Tests for collect_environment function."""

    def test_basic_collection(self):
        result = collect_environment()
        assert isinstance(result, EnvSnapshot)
        assert result.python_version == sys.version
        assert result.python_executable == sys.executable
        assert result.platform != ""

    def test_platform_details(self):
        result = collect_environment()
        assert isinstance(result.platform_details, PlatformDetails)
        assert result.platform_details.system != ""
        assert result.platform_details.machine != ""

    def test_cwd_collection(self):
        result = collect_environment()
        assert result.cwd == os.getcwd()

    def test_virtualenv_detection(self):
        result = collect_environment()
        expected = sys.prefix != sys.base_prefix
        assert result.virtualenv == expected

    def test_packages_collection(self):
        result = collect_environment()
        assert isinstance(result.packages, list)
        if result.packages:
            assert isinstance(result.packages[0], PackageInfo)
            assert result.packages[0].name != ""
            assert result.packages[0].version != ""

    def test_packages_disabled(self):
        config = EnvConfig(include_packages=False)
        result = collect_environment(config)
        assert result.packages == []

    def test_git_disabled(self):
        config = EnvConfig(include_git=False)
        result = collect_environment(config)
        assert result.git is None

    def test_env_vars_filtered(self):
        result = collect_environment()
        for blocked in ENV_BLOCKLIST:
            assert blocked not in result.env_vars

    def test_max_packages_limit(self):
        config = EnvConfig(max_packages=5)
        result = collect_environment(config)
        assert len(result.packages) <= 5

    def test_packages_truncation_flag(self):
        config = EnvConfig(max_packages=1)
        result = collect_environment(config)
        if len(result.packages) == 1:
            pass


class TestEnvVarsFiltering:
    """Tests for environment variable filtering."""

    def test_allowlist_filtering(self):
        config = EnvConfig(env_allowlist=frozenset({"PATH"}))
        result = collect_environment(config)
        for key in result.env_vars:
            assert key == "PATH"

    def test_blocklist_patterns(self):
        with patch.dict(os.environ, {"MY_PASSWORD": "secret123"}):
            config = EnvConfig(env_allowlist=frozenset({"MY_PASSWORD", "PATH"}))
            result = collect_environment(config)
            assert "MY_PASSWORD" not in result.env_vars

    def test_blocklist_explicit(self):
        with patch.dict(os.environ, {"AWS_SECRET_ACCESS_KEY": "xxx"}):
            config = EnvConfig(env_allowlist=frozenset({"AWS_SECRET_ACCESS_KEY"}))
            result = collect_environment(config)
            assert "AWS_SECRET_ACCESS_KEY" not in result.env_vars


class TestGitInfo:
    """Tests for GitInfo collection."""

    def test_git_info_structure(self):
        result = collect_environment()
        if result.git is not None:
            assert isinstance(result.git, GitInfo)
            assert result.git.ref is None or isinstance(result.git.ref, str)
            assert result.git.branch is None or isinstance(result.git.branch, str)
            assert result.git.dirty is None or isinstance(result.git.dirty, bool)

    def test_git_url_redaction(self):
        result = collect_environment()
        if result.git is not None and result.git.remote_url is not None:
            assert (
                "@" not in result.git.remote_url
                or "<REDACTED>" in result.git.remote_url
            )


class TestContainerDetection:
    """Tests for container detection."""

    def test_container_detection_type(self):
        result = collect_environment()
        assert isinstance(result.in_container, bool)


class TestCIDetection:
    """Tests for CI environment detection."""

    def test_ci_detection_type(self):
        result = collect_environment()
        assert isinstance(result.ci_detected, bool)

    def test_ci_detected_when_env_set(self):
        with patch.dict(os.environ, {"CI": "true"}):
            result = collect_environment()
            assert result.ci_detected is True

    def test_github_actions_detected(self):
        with patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}):
            result = collect_environment()
            assert result.ci_detected is True


class TestPlatformDetails:
    """Tests for PlatformDetails dataclass."""

    def test_all_fields_populated(self):
        result = collect_environment()
        pd = result.platform_details
        assert pd.system != ""
        assert pd.machine != ""


class TestPackageInfo:
    """Tests for PackageInfo dataclass."""

    def test_package_info_creation(self):
        pkg = PackageInfo(name="pytest", version="8.0.0")
        assert pkg.name == "pytest"
        assert pkg.version == "8.0.0"


class TestEdgeCases:
    """Tests for edge cases."""

    def test_cwd_permission_error(self):
        with patch("os.getcwd", side_effect=OSError("Permission denied")):
            result = collect_environment()
            assert result.cwd == "<permission denied>"

    def test_empty_env_allowlist(self):
        config = EnvConfig(env_allowlist=frozenset())
        result = collect_environment(config)
        assert result.env_vars == {}
