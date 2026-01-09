"""Tests for configuration management."""

from pathlib import Path

from bugsafe.config import (
    DEFAULT_ENV_ALLOWLIST,
    DEFAULT_MAX_OUTPUT_SIZE,
    DEFAULT_OUTPUT_FORMAT,
    DEFAULT_TIMEOUT,
    BugsafeConfig,
    DefaultsConfig,
    OutputConfig,
    RedactionConfig,
    get_config_dir,
    get_config_file,
    load_config,
)


class TestGetConfigDir:
    """Tests for get_config_dir function."""

    def test_uses_xdg_config_home(self, monkeypatch):
        """Uses XDG_CONFIG_HOME when set."""
        monkeypatch.setenv("XDG_CONFIG_HOME", "/custom/config")

        result = get_config_dir()

        assert result == Path("/custom/config/bugsafe")

    def test_falls_back_to_home(self, monkeypatch):
        """Falls back to ~/.config when XDG_CONFIG_HOME not set."""
        monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)

        result = get_config_dir()

        assert result == Path.home() / ".config" / "bugsafe"


class TestGetConfigFile:
    """Tests for get_config_file function."""

    def test_returns_config_toml(self, monkeypatch):
        """Returns config.toml in config directory."""
        monkeypatch.setenv("XDG_CONFIG_HOME", "/custom/config")

        result = get_config_file()

        assert result == Path("/custom/config/bugsafe/config.toml")


class TestDefaultsConfig:
    """Tests for DefaultsConfig dataclass."""

    def test_default_values(self):
        """Has correct default values."""
        config = DefaultsConfig()

        assert config.env_allowlist == DEFAULT_ENV_ALLOWLIST
        assert config.timeout == DEFAULT_TIMEOUT
        assert config.max_output_size == DEFAULT_MAX_OUTPUT_SIZE

    def test_custom_values(self):
        """Accepts custom values."""
        config = DefaultsConfig(
            env_allowlist=frozenset({"CUSTOM_VAR"}),
            timeout=60,
            max_output_size=1024,
        )

        assert config.env_allowlist == frozenset({"CUSTOM_VAR"})
        assert config.timeout == 60
        assert config.max_output_size == 1024


class TestRedactionConfig:
    """Tests for RedactionConfig dataclass."""

    def test_default_values(self):
        """Has correct default values."""
        config = RedactionConfig()

        assert config.custom_patterns_file is None
        assert config.redact_emails is True
        assert config.redact_ips is True
        assert config.redact_uuids is False

    def test_custom_values(self):
        """Accepts custom values."""
        config = RedactionConfig(
            custom_patterns_file=Path("/patterns.yaml"),
            redact_emails=False,
            redact_ips=False,
            redact_uuids=True,
        )

        assert config.custom_patterns_file == Path("/patterns.yaml")
        assert config.redact_emails is False
        assert config.redact_ips is False
        assert config.redact_uuids is True


class TestOutputConfig:
    """Tests for OutputConfig dataclass."""

    def test_default_values(self):
        """Has correct default values."""
        config = OutputConfig()

        assert config.default_format == DEFAULT_OUTPUT_FORMAT
        assert config.default_output_dir is None

    def test_custom_values(self):
        """Accepts custom values."""
        config = OutputConfig(
            default_format="json",
            default_output_dir=Path("/output"),
        )

        assert config.default_format == "json"
        assert config.default_output_dir == Path("/output")


class TestBugsafeConfig:
    """Tests for BugsafeConfig dataclass."""

    def test_default_values(self):
        """Has correct default values."""
        config = BugsafeConfig()

        assert isinstance(config.defaults, DefaultsConfig)
        assert isinstance(config.redaction, RedactionConfig)
        assert isinstance(config.output, OutputConfig)

    def test_load_nonexistent_file(self, tmp_path):
        """Returns default config when file doesn't exist."""
        path = tmp_path / "nonexistent.toml"

        config = BugsafeConfig.load(path)

        assert config.defaults.timeout == DEFAULT_TIMEOUT

    def test_load_valid_file(self, tmp_path):
        """Loads configuration from valid TOML file."""
        path = tmp_path / "config.toml"
        path.write_text("""
[defaults]
timeout = 60
max_output_size = 1024

[redaction]
redact_emails = false
redact_uuids = true

[output]
default_format = "json"
""")

        config = BugsafeConfig.load(path)

        assert config.defaults.timeout == 60
        assert config.defaults.max_output_size == 1024
        assert config.redaction.redact_emails is False
        assert config.redaction.redact_uuids is True
        assert config.output.default_format == "json"

    def test_load_invalid_toml(self, tmp_path):
        """Returns default config for invalid TOML."""
        path = tmp_path / "config.toml"
        path.write_text("invalid toml {{{{")

        config = BugsafeConfig.load(path)

        assert config.defaults.timeout == DEFAULT_TIMEOUT

    def test_load_with_env_allowlist(self, tmp_path):
        """Loads custom env_allowlist."""
        path = tmp_path / "config.toml"
        path.write_text("""
[defaults]
env_allowlist = ["PATH", "HOME", "CUSTOM_VAR"]
""")

        config = BugsafeConfig.load(path)

        assert "PATH" in config.defaults.env_allowlist
        assert "HOME" in config.defaults.env_allowlist
        assert "CUSTOM_VAR" in config.defaults.env_allowlist

    def test_load_with_custom_patterns(self, tmp_path):
        """Loads custom patterns file path."""
        path = tmp_path / "config.toml"
        path.write_text("""
[redaction]
custom_patterns = "~/patterns.yaml"
""")

        config = BugsafeConfig.load(path)

        assert config.redaction.custom_patterns_file is not None
        assert "patterns.yaml" in str(config.redaction.custom_patterns_file)

    def test_load_with_output_dir(self, tmp_path):
        """Loads custom output directory."""
        path = tmp_path / "config.toml"
        path.write_text("""
[output]
default_output_dir = "~/crashes"
""")

        config = BugsafeConfig.load(path)

        assert config.output.default_output_dir is not None

    def test_from_dict_empty(self):
        """Creates config from empty dict."""
        config = BugsafeConfig.from_dict({})

        assert config.defaults.timeout == DEFAULT_TIMEOUT

    def test_to_dict(self):
        """Converts config to dict."""
        config = BugsafeConfig(
            defaults=DefaultsConfig(timeout=60),
            redaction=RedactionConfig(redact_emails=False),
            output=OutputConfig(default_format="json"),
        )

        result = config.to_dict()

        assert result["defaults"]["timeout"] == 60
        assert result["redaction"]["redact_emails"] is False
        assert result["output"]["default_format"] == "json"

    def test_to_dict_with_paths(self):
        """Converts config with paths to dict."""
        config = BugsafeConfig(
            redaction=RedactionConfig(custom_patterns_file=Path("/patterns.yaml")),
            output=OutputConfig(default_output_dir=Path("/output")),
        )

        result = config.to_dict()

        # Path separators are platform-dependent
        assert "patterns.yaml" in result["redaction"]["custom_patterns"]
        assert "output" in result["output"]["default_output_dir"]


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_config_default(self, monkeypatch, tmp_path):
        """Loads config from default location."""
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

        config = load_config()

        assert isinstance(config, BugsafeConfig)

    def test_load_config_custom_path(self, tmp_path):
        """Loads config from custom path."""
        path = tmp_path / "custom.toml"
        path.write_text("[defaults]\ntimeout = 30")

        config = load_config(path)

        assert config.defaults.timeout == 30
