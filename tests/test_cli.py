"""
Tests for chimera_runtime.cli

Tests all CLI commands using Click's CliRunner for in-process testing.
Each command is tested for:
  - Correct exit code (0 for success, 1 for error)
  - Expected output content
  - Proper error handling
"""

import json
import os
import shutil
import pytest
from pathlib import Path

from click.testing import CliRunner

from chimera_runtime.cli.main import cli


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def work_dir(tmp_path):
    """Create a working directory with config and policy."""
    # Create config
    config_dir = tmp_path / ".chimera"
    config_dir.mkdir()

    policy_dir = tmp_path / "policies"
    policy_dir.mkdir()

    audit_dir = tmp_path / "audit_logs"
    audit_dir.mkdir()

    # Copy governance.csl
    src_policy = Path(__file__).parent.parent / "policies" / "governance.csl"
    if src_policy.exists():
        shutil.copy(src_policy, policy_dir / "governance.csl")
    else:
        # Create a minimal policy
        (policy_dir / "governance.csl").write_text(
            'CONFIG {\n  ENFORCEMENT_MODE: BLOCK\n}\n\n'
            'DOMAIN TestGuard {\n'
            '  VARIABLES {\n    amount: 0..1000000\n    role: {"ADMIN", "USER"}\n  }\n\n'
            '  STATE_CONSTRAINT admin_required {\n'
            '    WHEN amount > 50000\n    THEN role == "ADMIN"\n  }\n}\n',
            encoding="utf-8",
        )

    # Create config yaml
    config_yaml = f"""
llm:
  provider: openai
  model: gpt-4o
  temperature: 0.7
  max_retries: 3
  candidates_per_attempt: 3
policy:
  file: {policy_dir}/governance.csl
  auto_verify: true
audit:
  enabled: true
  output_dir: {audit_dir}
  format: json
  html_reports: true
  retention_days: 180
oversight:
  require_confirmation: false
  allow_override: true
"""
    (config_dir / "config.yaml").write_text(config_yaml, encoding="utf-8")

    return tmp_path


def _populate_audit(audit_dir: str, n: int = 3):
    """Create sample audit records."""
    from chimera_runtime.models import (
        AgentInfo, InputInfo, Attempt, Candidate, PolicyEvaluation,
        Violation,
    )
    from chimera_runtime.audit.recorder import build_audit_record
    from chimera_runtime.audit.storage import save_record

    for i in range(n):
        result = "ALLOWED" if i % 2 == 0 else "BLOCKED"
        violations = []
        if result == "BLOCKED":
            violations = [Violation(
                constraint="test_limit",
                rule="amount > 50000",
                trigger_values={"amount": 100000},
                explanation="Exceeds limit",
            )]

        record = build_audit_record(
            agent_info=AgentInfo(
                name="test-agent", version="0.1.0", csl_core_version="0.3.0",
                model="gpt-4o", model_provider="openai", temperature=0.7,
            ),
            input_info=InputInfo(raw_request=f"Request {i}"),
            attempts=[Attempt(
                attempt_number=1,
                candidates=[Candidate(
                    candidate_id="cand_001",
                    strategy=f"Strategy {i}",
                    llm_reasoning="Test",
                    llm_confidence=0.85,
                    parameters={"amount": 50000 * (i + 1)},
                    policy_evaluation=PolicyEvaluation(
                        policy_file="test.csl",
                        policy_hash="sha256:test",
                        result=result,
                        duration_ms=1.0,
                        violations=violations,
                    ),
                )],
                outcome="ALL_PASSED" if result == "ALLOWED" else "ALL_BLOCKED",
            )],
            action_taken=f"Strategy {i}" if result == "ALLOWED" else "BLOCKED",
            result=result,
            final_parameters={"amount": 50000 * (i + 1)} if result == "ALLOWED" else {},
            policy_file="test.csl",
            policy_hash="sha256:test",
            decision_id=f"dec_test_{i:03d}",
            total_duration_ms=15.0,
        )
        save_record(record, audit_dir=audit_dir)


def _csl_available() -> bool:
    try:
        from chimera_core import load_guard
        return True
    except ImportError:
        return False


# ============================================================================
# VERSION & HELP
# ============================================================================

class TestVersionAndHelp:

    def test_version(self, runner):
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "chimera-runtime" in result.output

    def test_help(self, runner):
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "EU AI Act" in result.output

    def test_help_lists_commands(self, runner):
        result = runner.invoke(cli, ["--help"])
        assert "init" in result.output
        assert "run" in result.output
        assert "verify" in result.output
        assert "audit" in result.output
        assert "policy" in result.output
        assert "explain" in result.output
        assert "docs" in result.output
        assert "stop" in result.output


# ============================================================================
# INIT
# ============================================================================

class TestInit:

    def test_init_non_interactive(self, runner, tmp_path):
        config_path = str(tmp_path / ".chimera" / "config.yaml")
        result = runner.invoke(cli, [
            "--config", config_path,
            "init", "--non-interactive",
        ])
        assert result.exit_code == 0
        assert "Initialized" in result.output
        assert Path(config_path).exists()

    def test_init_creates_policy(self, runner, tmp_path):
        config_path = str(tmp_path / ".chimera" / "config.yaml")
        result = runner.invoke(cli, [
            "--config", config_path,
            "init", "--non-interactive",
        ])
        assert result.exit_code == 0
        # Either "Starter policy created" or "Policy file already exists"
        assert "policy" in result.output.lower()

    def test_init_creates_directories(self, runner, tmp_path):
        config_path = str(tmp_path / "deep" / ".chimera" / "config.yaml")
        result = runner.invoke(cli, [
            "--config", config_path,
            "init", "--non-interactive",
        ])
        assert result.exit_code == 0
        assert Path(config_path).exists()


# ============================================================================
# VERIFY
# ============================================================================

@pytest.mark.skipif(not _csl_available(), reason="csl-core not installed")
class TestVerify:

    def test_verify_valid_policy(self, runner, work_dir):
        policy = str(work_dir / "policies" / "governance.csl")
        result = runner.invoke(cli, [
            "--config", str(work_dir / ".chimera" / "config.yaml"),
            "verify", policy,
        ])
        assert result.exit_code == 0
        assert "Policy Verified" in result.output

    def test_verify_shows_domain(self, runner, work_dir):
        policy = str(work_dir / "policies" / "governance.csl")
        result = runner.invoke(cli, [
            "--config", str(work_dir / ".chimera" / "config.yaml"),
            "verify", policy,
        ])
        assert "Domain:" in result.output

    def test_verify_shows_variables(self, runner, work_dir):
        policy = str(work_dir / "policies" / "governance.csl")
        result = runner.invoke(cli, [
            "--config", str(work_dir / ".chimera" / "config.yaml"),
            "verify", policy,
        ])
        assert "Variables:" in result.output

    def test_verify_shows_constraints(self, runner, work_dir):
        policy = str(work_dir / "policies" / "governance.csl")
        result = runner.invoke(cli, [
            "--config", str(work_dir / ".chimera" / "config.yaml"),
            "verify", policy,
        ])
        assert "Constraints:" in result.output

    def test_verify_missing_file(self, runner, work_dir):
        result = runner.invoke(cli, [
            "--config", str(work_dir / ".chimera" / "config.yaml"),
            "verify", "/nonexistent/policy.csl",
        ])
        assert result.exit_code == 1

    def test_verify_uses_config_policy(self, runner, work_dir):
        """When no argument given, uses config.policy.file."""
        result = runner.invoke(cli, [
            "--config", str(work_dir / ".chimera" / "config.yaml"),
            "verify",
        ])
        assert result.exit_code == 0
        assert "Policy Verified" in result.output


# ============================================================================
# STOP
# ============================================================================

class TestStop:

    def test_stop_creates_halt_file(self, runner, work_dir):
        result = runner.invoke(cli, [
            "--config", str(work_dir / ".chimera" / "config.yaml"),
            "stop",
        ])
        assert result.exit_code == 0
        assert "HALT signal sent" in result.output
        assert (work_dir / ".chimera" / ".halt").exists()

    def test_stop_force(self, runner, work_dir):
        result = runner.invoke(cli, [
            "--config", str(work_dir / ".chimera" / "config.yaml"),
            "stop", "--force",
        ])
        assert result.exit_code == 0
        assert "FORCE HALT" in result.output

        halt_content = json.loads((work_dir / ".chimera" / ".halt").read_text())
        assert halt_content["force"] is True


# ============================================================================
# AUDIT
# ============================================================================

class TestAudit:

    def test_audit_empty(self, runner, work_dir):
        result = runner.invoke(cli, [
            "--config", str(work_dir / ".chimera" / "config.yaml"),
            "audit", "--audit-dir", str(work_dir / "audit_logs"),
        ])
        assert result.exit_code == 0
        assert "No audit records" in result.output

    def test_audit_last(self, runner, work_dir):
        _populate_audit(str(work_dir / "audit_logs"), n=5)
        result = runner.invoke(cli, [
            "--config", str(work_dir / ".chimera" / "config.yaml"),
            "audit", "--last", "3",
            "--audit-dir", str(work_dir / "audit_logs"),
        ])
        assert result.exit_code == 0
        assert "Total: 3" in result.output

    def test_audit_filter_blocked(self, runner, work_dir):
        _populate_audit(str(work_dir / "audit_logs"), n=6)
        result = runner.invoke(cli, [
            "--config", str(work_dir / ".chimera" / "config.yaml"),
            "audit", "--result", "BLOCKED",
            "--audit-dir", str(work_dir / "audit_logs"),
        ])
        assert result.exit_code == 0
        assert "BLOCKED" in result.output

    def test_audit_stats(self, runner, work_dir):
        _populate_audit(str(work_dir / "audit_logs"), n=4)
        result = runner.invoke(cli, [
            "--config", str(work_dir / ".chimera" / "config.yaml"),
            "audit", "--stats",
            "--audit-dir", str(work_dir / "audit_logs"),
        ])
        assert result.exit_code == 0
        assert "Audit Statistics" in result.output
        assert "Total Decisions" in result.output

    def test_audit_violations(self, runner, work_dir):
        _populate_audit(str(work_dir / "audit_logs"), n=4)
        result = runner.invoke(cli, [
            "--config", str(work_dir / ".chimera" / "config.yaml"),
            "audit", "--violations",
            "--audit-dir", str(work_dir / "audit_logs"),
        ])
        assert result.exit_code == 0
        assert "Violation" in result.output

    def test_audit_by_id(self, runner, work_dir):
        _populate_audit(str(work_dir / "audit_logs"), n=3)
        result = runner.invoke(cli, [
            "--config", str(work_dir / ".chimera" / "config.yaml"),
            "audit", "--id", "dec_test_000",
            "--audit-dir", str(work_dir / "audit_logs"),
        ])
        assert result.exit_code == 0
        assert "dec_test_000" in result.output

    def test_audit_by_id_not_found(self, runner, work_dir):
        result = runner.invoke(cli, [
            "--config", str(work_dir / ".chimera" / "config.yaml"),
            "audit", "--id", "dec_nonexistent",
            "--audit-dir", str(work_dir / "audit_logs"),
        ])
        assert result.exit_code == 1

    def test_audit_export(self, runner, work_dir):
        _populate_audit(str(work_dir / "audit_logs"), n=3)
        export_path = str(work_dir / "export.json")
        result = runner.invoke(cli, [
            "--config", str(work_dir / ".chimera" / "config.yaml"),
            "audit", "--export", export_path,
            "--audit-dir", str(work_dir / "audit_logs"),
        ])
        assert result.exit_code == 0
        assert "Exported" in result.output
        assert Path(export_path).exists()


# ============================================================================
# POLICY
# ============================================================================

class TestPolicy:

    def test_policy_new(self, runner, tmp_path):
        result = runner.invoke(cli, [
            "policy", "new", "TestDomain",
            "--dir", str(tmp_path / "policies"),
        ])
        assert result.exit_code == 0
        assert "Created policy" in result.output
        assert (tmp_path / "policies" / "testdomain.csl").exists()

    def test_policy_new_content(self, runner, tmp_path):
        runner.invoke(cli, [
            "policy", "new", "MyGuard",
            "--dir", str(tmp_path / "policies"),
        ])
        content = (tmp_path / "policies" / "myguard.csl").read_text()
        assert "DOMAIN MyGuard" in content
        assert "VARIABLES" in content

    @pytest.mark.skipif(not _csl_available(), reason="csl-core not installed")
    def test_policy_list(self, runner, work_dir):
        result = runner.invoke(cli, [
            "policy", "list",
            "--dir", str(work_dir / "policies"),
        ])
        assert result.exit_code == 0
        assert "governance.csl" in result.output

    def test_policy_list_empty(self, runner, tmp_path):
        empty_dir = tmp_path / "empty_policies"
        empty_dir.mkdir()
        result = runner.invoke(cli, [
            "policy", "list",
            "--dir", str(empty_dir),
        ])
        assert result.exit_code == 0
        assert "No policy files" in result.output or "No .csl files" in result.output

    @pytest.mark.skipif(not _csl_available(), reason="csl-core not installed")
    def test_policy_simulate(self, runner, work_dir):
        policy = str(work_dir / "policies" / "governance.csl")
        context = '{"amount": 50000, "role": "MANAGER", "channel": "DIGITAL", "is_weekend": "NO", "urgency": "MEDIUM", "department": "MARKETING"}'
        result = runner.invoke(cli, [
            "policy", "simulate", policy, context,
        ])
        assert result.exit_code == 0
        assert "ALLOWED" in result.output or "BLOCKED" in result.output

    @pytest.mark.skipif(not _csl_available(), reason="csl-core not installed")
    def test_policy_simulate_blocked(self, runner, work_dir):
        policy = str(work_dir / "policies" / "governance.csl")
        context = '{"amount": 500000, "role": "MANAGER", "channel": "DIGITAL", "is_weekend": "NO", "urgency": "MEDIUM", "department": "MARKETING"}'
        result = runner.invoke(cli, [
            "policy", "simulate", policy, context,
        ])
        assert result.exit_code == 0
        assert "BLOCKED" in result.output

    def test_policy_simulate_no_input(self, runner, work_dir):
        policy = str(work_dir / "policies" / "governance.csl")
        result = runner.invoke(cli, ["policy", "simulate", policy])
        assert result.exit_code == 1

    def test_policy_simulate_invalid_json(self, runner, work_dir):
        policy = str(work_dir / "policies" / "governance.csl")
        result = runner.invoke(cli, ["policy", "simulate", policy, "not-json"])
        assert result.exit_code == 1


# ============================================================================
# EXPLAIN
# ============================================================================

class TestExplain:

    def test_explain_generates_html(self, runner, work_dir):
        _populate_audit(str(work_dir / "audit_logs"), n=3)
        output = str(work_dir / "explanation.html")
        result = runner.invoke(cli, [
            "--config", str(work_dir / ".chimera" / "config.yaml"),
            "explain", "--id", "dec_test_000",
            "--output", output,
            "--audit-dir", str(work_dir / "audit_logs"),
        ])
        assert result.exit_code == 0
        assert "Explanation Report" in result.output
        assert Path(output).exists()

        html = Path(output).read_text()
        assert "<!DOCTYPE html>" in html
        assert "dec_test_000" in html

    def test_explain_missing_id(self, runner, work_dir):
        result = runner.invoke(cli, [
            "--config", str(work_dir / ".chimera" / "config.yaml"),
            "explain", "--id", "dec_nonexistent",
            "--audit-dir", str(work_dir / "audit_logs"),
        ])
        assert result.exit_code == 1


# ============================================================================
# DOCS
# ============================================================================

@pytest.mark.skipif(not _csl_available(), reason="csl-core not installed")
class TestDocs:

    def test_docs_generate(self, runner, work_dir):
        output = str(work_dir / "docs" / "annex_iv.md")
        result = runner.invoke(cli, [
            "--config", str(work_dir / ".chimera" / "config.yaml"),
            "docs", "generate",
            "--output", output,
            "--audit-dir", str(work_dir / "audit_logs"),
        ])
        assert result.exit_code == 0
        assert "Documentation Generated" in result.output
        assert Path(output).exists()

    def test_docs_generate_with_audit(self, runner, work_dir):
        _populate_audit(str(work_dir / "audit_logs"), n=5)
        output = str(work_dir / "docs" / "annex_iv.md")
        result = runner.invoke(cli, [
            "--config", str(work_dir / ".chimera" / "config.yaml"),
            "docs", "generate",
            "--output", output,
            "--audit-dir", str(work_dir / "audit_logs"),
        ])
        assert result.exit_code == 0
        content = Path(output).read_text()
        assert "Total Decisions" in content

    def test_docs_status(self, runner, work_dir):
        result = runner.invoke(cli, [
            "--config", str(work_dir / ".chimera" / "config.yaml"),
            "docs", "status",
            "--audit-dir", str(work_dir / "audit_logs"),
        ])
        assert result.exit_code == 0
        assert "Documentation Status" in result.output
        assert "/19" in result.output

    def test_docs_refresh(self, runner, work_dir):
        output = str(work_dir / "docs" / "annex_iv.md")
        result = runner.invoke(cli, [
            "--config", str(work_dir / ".chimera" / "config.yaml"),
            "docs", "refresh",
            "--output", output,
            "--audit-dir", str(work_dir / "audit_logs"),
        ])
        assert result.exit_code == 0
        assert "refreshed" in result.output


# ============================================================================
# SUBCOMMAND HELP
# ============================================================================

class TestSubcommandHelp:
    """Ensure every subcommand has a --help that works."""

    @pytest.mark.parametrize("cmd", [
        ["init", "--help"],
        ["run", "--help"],
        ["stop", "--help"],
        ["verify", "--help"],
        ["audit", "--help"],
        ["policy", "--help"],
        ["policy", "new", "--help"],
        ["policy", "list", "--help"],
        ["policy", "simulate", "--help"],
        ["explain", "--help"],
        ["docs", "--help"],
        ["docs", "generate", "--help"],
        ["docs", "status", "--help"],
        ["docs", "refresh", "--help"],
    ])
    def test_help_works(self, runner, cmd):
        result = runner.invoke(cli, cmd)
        assert result.exit_code == 0
        assert "--help" not in result.output or "Show this message" in result.output
