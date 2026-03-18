"""
Tests for chimera_runtime.config

Validates:
  - YAML loading and parsing
  - Default values when file is missing
  - Environment variable overrides
  - Validation catches invalid values
  - Save produces readable YAML
  - Roundtrip: save → load produces identical config
"""

import os
import tempfile
from pathlib import Path

import pytest

from chimera_runtime.config import (
    load_config,
    save_config,
    validate_config,
    ConfigError,
)
from chimera_runtime.models import (
    AgentConfig,
    LLMConfig,
    PolicyConfig,
    AuditConfig,
    OversightConfig,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def tmp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


@pytest.fixture
def sample_yaml_content():
    return """
agent:
  name: test-agent
  version: "0.2.0"

llm:
  provider: anthropic
  model: claude-sonnet-4-20250514
  temperature: 0.5
  max_retries: 2
  candidates_per_attempt: 4

policy:
  file: ./policies/test.csl
  auto_verify: true

audit:
  enabled: true
  output_dir: ./test_logs
  format: both
  html_reports: true
  retention_days: 365

oversight:
  require_confirmation: true
  allow_override: true
  policy_hot_reload: false
  stop_on_consecutive_blocks: 3
"""


@pytest.fixture
def sample_config_file(tmp_dir, sample_yaml_content):
    path = tmp_dir / "config.yaml"
    path.write_text(sample_yaml_content)
    return path


# ============================================================================
# LOADING TESTS
# ============================================================================

class TestLoadConfig:
    def test_load_from_file(self, sample_config_file):
        cfg = load_config(str(sample_config_file))
        assert cfg.agent.name == "test-agent"
        assert cfg.agent.version == "0.2.0"
        assert cfg.llm.provider == "anthropic"
        assert cfg.llm.model == "claude-sonnet-4-20250514"
        assert cfg.llm.temperature == 0.5
        assert cfg.llm.max_retries == 2
        assert cfg.llm.candidates_per_attempt == 4
        assert cfg.policy.file == "./policies/test.csl"
        assert cfg.audit.output_dir == "./test_logs"
        assert cfg.audit.format == "both"
        assert cfg.audit.retention_days == 365
        assert cfg.oversight.require_confirmation is True
        assert cfg.oversight.stop_on_consecutive_blocks == 3

    def test_load_nonexistent_returns_defaults(self, tmp_dir):
        cfg = load_config(str(tmp_dir / "nonexistent.yaml"))
        assert cfg.llm.provider == "openai"
        assert cfg.llm.model == "gpt-4o"
        assert cfg.audit.retention_days == 180

    def test_load_empty_file_returns_defaults(self, tmp_dir):
        path = tmp_dir / "empty.yaml"
        path.write_text("")
        cfg = load_config(str(path))
        assert cfg.llm.provider == "openai"

    def test_load_malformed_yaml_raises(self, tmp_dir):
        path = tmp_dir / "bad.yaml"
        path.write_text("{{invalid yaml: [")
        with pytest.raises(ConfigError, match="Failed to parse"):
            load_config(str(path))

    def test_load_non_dict_yaml_raises(self, tmp_dir):
        path = tmp_dir / "list.yaml"
        path.write_text("- item1\n- item2\n")
        with pytest.raises(ConfigError, match="YAML mapping"):
            load_config(str(path))

    def test_partial_config_fills_defaults(self, tmp_dir):
        path = tmp_dir / "partial.yaml"
        path.write_text("llm:\n  provider: google\n")
        cfg = load_config(str(path))
        assert cfg.llm.provider == "google"
        assert cfg.llm.model == "gpt-4o"  # default
        assert cfg.audit.retention_days == 180  # default


# ============================================================================
# ENVIRONMENT VARIABLE OVERRIDE TESTS
# ============================================================================

class TestEnvOverrides:
    def test_api_key_from_env(self, tmp_dir, monkeypatch):
        path = tmp_dir / "config.yaml"
        path.write_text("llm:\n  provider: openai\n")
        monkeypatch.setenv("CHIMERA_API_KEY", "sk-test-key-123")
        cfg = load_config(str(path))
        assert cfg.llm.api_key == "sk-test-key-123"

    def test_model_from_env(self, tmp_dir, monkeypatch):
        path = tmp_dir / "config.yaml"
        path.write_text("llm:\n  provider: openai\n")
        monkeypatch.setenv("CHIMERA_MODEL", "gpt-4.1")
        cfg = load_config(str(path))
        assert cfg.llm.model == "gpt-4.1"

    def test_env_overrides_yaml(self, sample_config_file, monkeypatch):
        monkeypatch.setenv("CHIMERA_PROVIDER", "ollama")
        cfg = load_config(str(sample_config_file))
        assert cfg.llm.provider == "ollama"  # env overrides yaml

    def test_empty_env_no_override(self, tmp_dir, monkeypatch):
        path = tmp_dir / "config.yaml"
        path.write_text("llm:\n  provider: openai\n  model: gpt-4o\n")
        monkeypatch.setenv("CHIMERA_MODEL", "")
        cfg = load_config(str(path))
        assert cfg.llm.model == "gpt-4o"  # empty env doesn't override


# ============================================================================
# VALIDATION TESTS
# ============================================================================

class TestValidation:
    def test_valid_config_passes(self):
        cfg = AgentConfig()
        validate_config(cfg)  # Should not raise

    def test_invalid_provider(self):
        cfg = AgentConfig(llm=LLMConfig(provider="invalid_provider"))
        with pytest.raises(ConfigError, match="llm.provider"):
            validate_config(cfg)

    def test_temperature_too_high(self):
        cfg = AgentConfig(llm=LLMConfig(temperature=3.0))
        with pytest.raises(ConfigError, match="temperature"):
            validate_config(cfg)

    def test_temperature_negative(self):
        cfg = AgentConfig(llm=LLMConfig(temperature=-0.1))
        with pytest.raises(ConfigError, match="temperature"):
            validate_config(cfg)

    def test_max_retries_zero(self):
        cfg = AgentConfig(llm=LLMConfig(max_retries=0))
        with pytest.raises(ConfigError, match="max_retries"):
            validate_config(cfg)

    def test_empty_policy_file(self):
        cfg = AgentConfig(policy=PolicyConfig(file=""))
        with pytest.raises(ConfigError, match="policy.file"):
            validate_config(cfg)

    def test_invalid_audit_format(self):
        cfg = AgentConfig(audit=AuditConfig(format="xml"))
        with pytest.raises(ConfigError, match="audit.format"):
            validate_config(cfg)

    def test_zero_retention_days(self):
        cfg = AgentConfig(audit=AuditConfig(retention_days=0))
        with pytest.raises(ConfigError, match="retention_days"):
            validate_config(cfg)

    def test_multiple_errors_reported(self):
        cfg = AgentConfig(
            llm=LLMConfig(provider="bad", temperature=5.0),
            audit=AuditConfig(format="xml"),
        )
        with pytest.raises(ConfigError) as exc_info:
            validate_config(cfg)
        msg = str(exc_info.value)
        assert "llm.provider" in msg
        assert "temperature" in msg
        assert "audit.format" in msg


# ============================================================================
# SAVE TESTS
# ============================================================================

class TestSaveConfig:
    def test_save_creates_file(self, tmp_dir):
        cfg = AgentConfig()
        path = save_config(cfg, str(tmp_dir / "output.yaml"))
        assert path.exists()

    def test_save_creates_parent_dirs(self, tmp_dir):
        cfg = AgentConfig()
        path = save_config(cfg, str(tmp_dir / "deep" / "nested" / "config.yaml"))
        assert path.exists()

    def test_save_has_header(self, tmp_dir):
        cfg = AgentConfig()
        path = save_config(cfg, str(tmp_dir / "config.yaml"))
        content = path.read_text()
        assert "chimera-runtime configuration" in content
        assert "CHIMERA_API_KEY" in content

    def test_roundtrip_save_load(self, tmp_dir):
        original = AgentConfig(
            llm=LLMConfig(provider="anthropic", model="claude-sonnet-4-20250514", temperature=0.3),
            policy=PolicyConfig(file="./custom.csl"),
            audit=AuditConfig(retention_days=365, format="both"),
        )
        path = save_config(original, str(tmp_dir / "config.yaml"))
        restored = load_config(str(path))

        assert restored.llm.provider == "anthropic"
        assert restored.llm.model == "claude-sonnet-4-20250514"
        assert restored.llm.temperature == 0.3
        assert restored.policy.file == "./custom.csl"
        assert restored.audit.retention_days == 365
        assert restored.audit.format == "both"
