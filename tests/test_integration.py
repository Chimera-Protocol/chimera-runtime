"""
Full Integration Tests for chimera-compliance v2.0

End-to-end flows testing the complete lifecycle:
  init → config → verify → simulate → decide → audit → explain → docs

LLM calls are mocked; everything else is real:
  - Real CSL-Core policy compilation & Z3 verification
  - Real audit record creation, storage, and querying
  - Real HTML report generation
  - Real Annex IV documentation generation
  - Real CLI commands via Click's CliRunner

These tests validate that all 6 phases work together seamlessly.
"""

import json
import os
import shutil
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from click.testing import CliRunner


# ============================================================================
# SKIP IF DEPENDENCIES MISSING
# ============================================================================

def _csl_available() -> bool:
    try:
        from chimera_core import load_guard
        return True
    except ImportError:
        return False


def _jinja2_available() -> bool:
    try:
        import jinja2
        return True
    except ImportError:
        return False


pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not _csl_available(), reason="csl-core not installed"),
]


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def project_dir(tmp_path):
    """Create a complete project directory structure."""
    root = tmp_path / "my_project"
    root.mkdir()

    (root / "policies").mkdir()
    (root / "audit_logs").mkdir()
    (root / "docs").mkdir()
    (root / ".chimera").mkdir()

    # Copy real governance policy
    src_policy = Path(__file__).parent.parent / "policies" / "governance.csl"
    if src_policy.exists():
        shutil.copy(src_policy, root / "policies" / "governance.csl")

    return root


@pytest.fixture
def config_yaml(project_dir):
    """Create a valid config pointing to project_dir paths."""
    config_content = f"""
agent:
  name: integration-test-agent
  version: 2.0.0-test

llm:
  provider: openai
  model: gpt-4o
  temperature: 0.7
  max_retries: 3
  candidates_per_attempt: 3

policy:
  file: {project_dir}/policies/governance.csl
  auto_verify: true

audit:
  enabled: true
  output_dir: {project_dir}/audit_logs
  format: json
  html_reports: true
  retention_days: 180

oversight:
  require_confirmation: false
  allow_override: true
  stop_on_consecutive_blocks: 5
"""
    config_path = project_dir / ".chimera" / "config.yaml"
    config_path.write_text(config_content, encoding="utf-8")
    return str(config_path)


@pytest.fixture
def runner():
    return CliRunner()


def _mock_llm_response(candidates_data: list[dict]):
    """Create a mock LLM provider that returns specified candidates."""
    from chimera_compliance.models import Candidate, generate_candidate_id

    mock_provider = MagicMock()

    def mock_generate(request="", context=None, n=3, variable_spec="", rejection_context=None):
        results = []
        for i, data in enumerate(candidates_data[:n]):
            results.append(Candidate(
                candidate_id=generate_candidate_id(i),
                strategy=data.get("strategy", f"Strategy {i}"),
                llm_reasoning=data.get("reasoning", "Mock LLM reasoning"),
                llm_confidence=data.get("confidence", 0.85),
                parameters=data["parameters"],
            ))
        return results

    mock_provider.generate_candidates = mock_generate
    mock_provider.model = "gpt-4o-mock"
    mock_provider.provider_name = "openai"
    mock_provider.temperature = 0.7
    return mock_provider


# ============================================================================
# 1. LIFECYCLE: INIT → CONFIG → VERIFY
# ============================================================================

class TestLifecycleSetup:
    """Phase 1: Project initialization and configuration."""

    def test_init_creates_project(self, runner, tmp_path):
        """chimera-compliance init creates config and starter policy."""
        from chimera_compliance.cli.main import cli

        config_path = str(tmp_path / ".chimera" / "config.yaml")
        result = runner.invoke(cli, [
            "--config", config_path,
            "init", "--non-interactive",
        ])
        assert result.exit_code == 0
        assert Path(config_path).exists()

    def test_config_loads_correctly(self, config_yaml):
        """Config YAML round-trips through load/save."""
        from chimera_compliance import load_config, save_config

        config = load_config(config_yaml)
        assert config.llm.provider == "openai"
        assert config.llm.model == "gpt-4o"
        assert config.audit.retention_days == 180
        assert config.oversight.allow_override is True

        # Save and reload
        new_path = str(Path(config_yaml).parent / "config_copy.yaml")
        save_config(config, new_path)
        config2 = load_config(new_path)
        assert config2.llm.provider == config.llm.provider

    def test_policy_verifies(self, project_dir):
        """Governance policy passes full Z3 verification."""
        from chimera_compliance import PolicyManager

        pm = PolicyManager(
            str(project_dir / "policies" / "governance.csl"),
            auto_verify=True,
        )
        assert pm.domain_name == "GovernanceGuard"
        assert pm.constraint_count >= 5
        assert len(pm.variable_names) >= 4
        assert pm.hash.startswith("sha256:")

    def test_verify_cli_command(self, runner, project_dir, config_yaml):
        """CLI verify command works end-to-end."""
        from chimera_compliance.cli.main import cli

        result = runner.invoke(cli, [
            "--config", config_yaml,
            "verify",
            str(project_dir / "policies" / "governance.csl"),
        ])
        assert result.exit_code == 0
        assert "Policy Verified" in result.output
        assert "GovernanceGuard" in result.output


# ============================================================================
# 2. POLICY SIMULATION (NO LLM)
# ============================================================================

class TestPolicySimulation:
    """Phase 2: Policy evaluation without LLM calls."""

    def test_allowed_within_limits(self, project_dir):
        """MANAGER with 200k should be ALLOWED."""
        from chimera_compliance import PolicyManager

        pm = PolicyManager(str(project_dir / "policies" / "governance.csl"))
        result = pm.evaluate({
            "amount": 200000,
            "role": "MANAGER",
            "channel": "DIGITAL",
            "is_weekend": "NO",
            "urgency": "MEDIUM",
            "department": "MARKETING",
        })
        assert result.result == "ALLOWED"
        assert len(result.violations) == 0

    def test_blocked_exceeds_limit(self, project_dir):
        """MANAGER with 500k should be BLOCKED."""
        from chimera_compliance import PolicyManager

        pm = PolicyManager(str(project_dir / "policies" / "governance.csl"))
        result = pm.evaluate({
            "amount": 500000,
            "role": "MANAGER",
            "channel": "DIGITAL",
            "is_weekend": "NO",
            "urgency": "MEDIUM",
            "department": "MARKETING",
        })
        assert result.result == "BLOCKED"
        assert len(result.violations) > 0

    def test_simulate_cli_allowed(self, runner, project_dir, config_yaml):
        """CLI simulate shows ALLOWED for valid input."""
        from chimera_compliance.cli.main import cli

        context = json.dumps({
            "amount": 100000, "role": "MANAGER", "channel": "DIGITAL",
            "is_weekend": "NO", "urgency": "MEDIUM", "department": "MARKETING",
        })
        result = runner.invoke(cli, [
            "--config", config_yaml,
            "policy", "simulate",
            str(project_dir / "policies" / "governance.csl"),
            context,
        ])
        assert result.exit_code == 0
        assert "ALLOWED" in result.output

    def test_simulate_cli_blocked(self, runner, project_dir, config_yaml):
        """CLI simulate shows BLOCKED with violations."""
        from chimera_compliance.cli.main import cli

        context = json.dumps({
            "amount": 500000, "role": "MANAGER", "channel": "DIGITAL",
            "is_weekend": "NO", "urgency": "MEDIUM", "department": "MARKETING",
        })
        result = runner.invoke(cli, [
            "--config", config_yaml,
            "policy", "simulate",
            str(project_dir / "policies" / "governance.csl"),
            context,
        ])
        assert result.exit_code == 0
        assert "BLOCKED" in result.output

    def test_dry_run_never_blocks(self, project_dir):
        """Dry-run mode evaluates but always returns ALLOWED."""
        from chimera_compliance import PolicyManager

        pm = PolicyManager(
            str(project_dir / "policies" / "governance.csl"),
            dry_run=True,
        )
        result = pm.evaluate({
            "amount": 999999,
            "role": "ANALYST",
            "channel": "ALL",
            "is_weekend": "YES",
            "urgency": "LOW",
            "department": "HR",
        })
        assert result.result == "ALLOWED"


# ============================================================================
# 3. AGENT DECIDE (MOCK LLM)
# ============================================================================

class TestAgentDecide:
    """Phase 3: Full decide pipeline with mocked LLM."""

    def test_decide_allowed(self, project_dir, config_yaml):
        """Agent.decide() produces ALLOWED result for compliant candidate."""
        from chimera_compliance import ChimeraAgent, load_config

        config = load_config(config_yaml)
        mock_provider = _mock_llm_response([
            {
                "strategy": "Allocate 200k to digital channels",
                "reasoning": "Within manager limit",
                "confidence": 0.9,
                "parameters": {
                    "amount": 200000, "role": "MANAGER",
                    "channel": "DIGITAL", "is_weekend": "NO",
                    "urgency": "MEDIUM", "department": "MARKETING",
                },
            },
        ])

        with patch("chimera_compliance.agent.get_provider", return_value=mock_provider):
            agent = ChimeraAgent.from_config(config, config_path=config_yaml)
            result = agent.decide("Increase marketing spend by $200k")

        assert result.result == "ALLOWED"
        assert result.action is not None
        assert result.decision_id.startswith("dec_")
        assert result.audit is not None

    def test_decide_blocked_all_candidates(self, project_dir, config_yaml):
        """Agent.decide() returns BLOCKED when all candidates violate policy."""
        from chimera_compliance import ChimeraAgent, load_config

        config = load_config(config_yaml)
        # All candidates exceed limits
        mock_provider = _mock_llm_response([
            {"strategy": "Big spend", "parameters": {
                "amount": 999999, "role": "ANALYST",
                "channel": "ALL", "is_weekend": "YES",
                "urgency": "LOW", "department": "HR",
            }},
            {"strategy": "Also big", "parameters": {
                "amount": 800000, "role": "MANAGER",
                "channel": "TV", "is_weekend": "NO",
                "urgency": "MEDIUM", "department": "MARKETING",
            }},
        ])

        with patch("chimera_compliance.agent.get_provider", return_value=mock_provider):
            agent = ChimeraAgent.from_config(config, config_path=config_yaml)
            result = agent.decide("Spend everything")

        assert result.result == "BLOCKED"
        assert result.audit is not None
        assert result.audit.reasoning.total_attempts >= 1

    def test_decide_creates_audit_file(self, project_dir, config_yaml):
        """Every decide() creates a JSON audit file on disk."""
        from chimera_compliance import ChimeraAgent, load_config

        config = load_config(config_yaml)
        mock_provider = _mock_llm_response([
            {"strategy": "Reasonable spend", "parameters": {
                "amount": 50000, "role": "DIRECTOR",
                "channel": "DIGITAL", "is_weekend": "NO",
                "urgency": "HIGH", "department": "ENGINEERING",
            }},
        ])

        with patch("chimera_compliance.agent.get_provider", return_value=mock_provider):
            agent = ChimeraAgent.from_config(config, config_path=config_yaml)
            result = agent.decide("Approve engineering budget")

        # Check audit file exists
        audit_files = list((project_dir / "audit_logs").glob("dec_*.json"))
        assert len(audit_files) >= 1

        # Verify file content
        record_data = json.loads(audit_files[0].read_text())
        assert record_data["decision"]["result"] in ("ALLOWED", "BLOCKED")
        assert record_data["schema_version"] in ("1.0.0", "2.0")

    def test_halt_and_resume(self, project_dir, config_yaml):
        """Agent halt/resume lifecycle works correctly."""
        from chimera_compliance import ChimeraAgent, AgentHalted, load_config

        config = load_config(config_yaml)
        mock_provider = _mock_llm_response([{"strategy": "x", "parameters": {
            "amount": 1000, "role": "CEO", "channel": "DIGITAL",
            "is_weekend": "NO", "urgency": "LOW", "department": "MARKETING",
        }}])

        with patch("chimera_compliance.agent.get_provider", return_value=mock_provider):
            agent = ChimeraAgent.from_config(config, config_path=config_yaml)

            agent.halt()
            assert agent.is_halted

            with pytest.raises(AgentHalted):
                agent.decide("Should fail")

            agent.resume()
            assert not agent.is_halted

            result = agent.decide("Should work now")
            assert result.result in ("ALLOWED", "BLOCKED")


# ============================================================================
# 4. AUDIT PIPELINE
# ============================================================================

class TestAuditPipeline:
    """Phase 4: Audit record creation → query → export → explain."""

    def _run_decisions(self, project_dir, config_yaml, n=5):
        """Run N mock decisions to populate audit logs."""
        from chimera_compliance import ChimeraAgent, load_config

        config = load_config(config_yaml)
        results = []

        for i in range(n):
            amount = 50000 * (i + 1)
            role = "DIRECTOR" if amount <= 500000 else "ANALYST"
            mock_provider = _mock_llm_response([{
                "strategy": f"Plan {i}",
                "parameters": {
                    "amount": amount, "role": role,
                    "channel": "DIGITAL", "is_weekend": "NO",
                    "urgency": "MEDIUM", "department": "MARKETING",
                },
            }])

            with patch("chimera_compliance.agent.get_provider", return_value=mock_provider):
                agent = ChimeraAgent.from_config(config, config_path=config_yaml)
                result = agent.decide(f"Request {i}")
                results.append(result)

        return results

    def test_audit_records_created(self, project_dir, config_yaml):
        """Multiple decisions create multiple audit files."""
        self._run_decisions(project_dir, config_yaml, n=3)

        audit_files = list((project_dir / "audit_logs").glob("dec_*.json"))
        assert len(audit_files) == 3

    def test_audit_query_stats(self, project_dir, config_yaml):
        """AuditQuery.stats() returns accurate aggregate metrics."""
        from chimera_compliance import AuditQuery

        self._run_decisions(project_dir, config_yaml, n=5)

        query = AuditQuery(str(project_dir / "audit_logs"))
        stats = query.stats()

        assert stats.total_decisions == 5
        assert stats.allowed_count + stats.blocked_count == 5
        assert 0.0 <= stats.allow_rate <= 1.0
        assert stats.avg_duration_ms > 0

    def test_audit_query_filter(self, project_dir, config_yaml):
        """AuditQuery.filter() correctly filters by result type."""
        from chimera_compliance import AuditQuery

        self._run_decisions(project_dir, config_yaml, n=5)

        query = AuditQuery(str(project_dir / "audit_logs"))
        all_records = query.filter()
        assert len(all_records) == 5

        allowed = query.filter(result="ALLOWED")
        blocked = query.filter(result="BLOCKED")
        assert len(allowed) + len(blocked) == 5

    def test_audit_load_single_record(self, project_dir, config_yaml):
        """load_record() retrieves a specific decision by ID."""
        from chimera_compliance import load_record

        results = self._run_decisions(project_dir, config_yaml, n=2)
        decision_id = results[0].decision_id

        record = load_record(decision_id, audit_dir=str(project_dir / "audit_logs"))
        assert record.decision_id == decision_id
        assert record.decision.result in ("ALLOWED", "BLOCKED")

    def test_audit_export_json(self, project_dir, config_yaml):
        """AuditQuery.export() creates a valid JSON export file."""
        from chimera_compliance import AuditQuery

        self._run_decisions(project_dir, config_yaml, n=3)

        query = AuditQuery(str(project_dir / "audit_logs"))
        export_path = str(project_dir / "export.json")
        query.export(export_path, format="json")

        assert Path(export_path).exists()
        data = json.loads(Path(export_path).read_text())
        assert isinstance(data, list)
        assert len(data) == 3

    def test_audit_cli_stats(self, runner, project_dir, config_yaml):
        """CLI audit --stats works end-to-end."""
        from chimera_compliance.cli.main import cli

        self._run_decisions(project_dir, config_yaml, n=4)

        result = runner.invoke(cli, [
            "--config", config_yaml,
            "audit", "--stats",
            "--audit-dir", str(project_dir / "audit_logs"),
        ])
        assert result.exit_code == 0
        assert "Audit Statistics" in result.output
        assert "Total Decisions" in result.output

    def test_explain_generates_html(self, project_dir, config_yaml):
        """Art. 86 explain generates a valid HTML report."""
        from chimera_compliance import load_record, generate_html

        results = self._run_decisions(project_dir, config_yaml, n=1)
        decision_id = results[0].decision_id

        record = load_record(decision_id, audit_dir=str(project_dir / "audit_logs"))
        html = generate_html(record)

        assert "<!DOCTYPE html>" in html
        assert decision_id in html
        assert "Art. 86" in html or "Right to Explanation" in html

    def test_explain_cli_command(self, runner, project_dir, config_yaml):
        """CLI explain --id generates HTML file."""
        from chimera_compliance.cli.main import cli

        results = self._run_decisions(project_dir, config_yaml, n=1)
        decision_id = results[0].decision_id

        output_path = str(project_dir / "docs" / "explanation.html")
        result = runner.invoke(cli, [
            "--config", config_yaml,
            "explain", "--id", decision_id,
            "--output", output_path,
            "--audit-dir", str(project_dir / "audit_logs"),
        ])
        assert result.exit_code == 0
        assert Path(output_path).exists()

        html = Path(output_path).read_text()
        assert "<!DOCTYPE html>" in html


# ============================================================================
# 5. DOCUMENTATION GENERATOR
# ============================================================================

@pytest.mark.skipif(not _jinja2_available(), reason="jinja2 not installed")
class TestDocsGenerator:
    """Phase 5: Annex IV documentation generation."""

    def _run_decisions(self, project_dir, config_yaml, n=3):
        """Same helper as audit tests."""
        from chimera_compliance import ChimeraAgent, load_config

        config = load_config(config_yaml)

        for i in range(n):
            mock_provider = _mock_llm_response([{
                "strategy": f"Plan {i}",
                "parameters": {
                    "amount": 50000, "role": "MANAGER",
                    "channel": "DIGITAL", "is_weekend": "NO",
                    "urgency": "MEDIUM", "department": "MARKETING",
                },
            }])
            with patch("chimera_compliance.agent.get_provider", return_value=mock_provider):
                agent = ChimeraAgent.from_config(config, config_path=config_yaml)
                agent.decide(f"Request {i}")

    def test_docs_generate_without_audit(self, project_dir, config_yaml):
        """Docs generate works even without audit data (11/19)."""
        from chimera_compliance import AnnexIVGenerator, load_config

        config = load_config(config_yaml)
        gen = AnnexIVGenerator(
            config=config,
            audit_dir=str(project_dir / "audit_logs"),
            policy_path=str(project_dir / "policies" / "governance.csl"),
        )

        output = str(project_dir / "docs" / "annex_iv.md")
        gen.generate(output_path=output)

        assert Path(output).exists()
        content = Path(output).read_text()
        assert "GovernanceGuard" in content

        status = gen.status()
        assert status["filled"] >= 11  # Without audit: 11 auto-filled

    def test_docs_generate_with_audit(self, project_dir, config_yaml):
        """Docs generate with audit data fills 14/19 sections."""
        from chimera_compliance import AnnexIVGenerator, load_config

        self._run_decisions(project_dir, config_yaml, n=3)

        config = load_config(config_yaml)
        gen = AnnexIVGenerator(
            config=config,
            audit_dir=str(project_dir / "audit_logs"),
            policy_path=str(project_dir / "policies" / "governance.csl"),
        )

        output = str(project_dir / "docs" / "annex_iv_full.md")
        gen.generate(output_path=output)

        content = Path(output).read_text()
        assert "Total Decisions" in content

        status = gen.status()
        assert status["filled"] == 14

    def test_docs_cli_generate(self, runner, project_dir, config_yaml):
        """CLI docs generate works end-to-end."""
        from chimera_compliance.cli.main import cli

        self._run_decisions(project_dir, config_yaml, n=2)

        output = str(project_dir / "docs" / "annex_iv_cli.md")
        result = runner.invoke(cli, [
            "--config", config_yaml,
            "docs", "generate",
            "--output", output,
            "--audit-dir", str(project_dir / "audit_logs"),
        ])
        assert result.exit_code == 0
        assert Path(output).exists()

    def test_docs_cli_status(self, runner, project_dir, config_yaml):
        """CLI docs status shows coverage tree."""
        from chimera_compliance.cli.main import cli

        result = runner.invoke(cli, [
            "--config", config_yaml,
            "docs", "status",
            "--audit-dir", str(project_dir / "audit_logs"),
        ])
        assert result.exit_code == 0
        assert "/19" in result.output


# ============================================================================
# 6. FULL LIFECYCLE E2E
# ============================================================================

class TestFullLifecycle:
    """Complete end-to-end flow through all phases."""

    def test_complete_lifecycle(self, project_dir, config_yaml, runner):
        """
        Full lifecycle:
        1. Config loads
        2. Policy verifies
        3. Agent makes decisions (mock LLM)
        4. Audit records created
        5. Audit stats calculated
        6. HTML explanation generated
        7. Annex IV docs generated
        8. CLI commands all work
        """
        from chimera_compliance import (
            load_config, PolicyManager, ChimeraAgent,
            AuditQuery, load_record, generate_html,
        )
        from chimera_compliance.cli.main import cli

        # 1. CONFIG
        config = load_config(config_yaml)
        assert config.agent.name == "integration-test-agent"

        # 2. POLICY
        pm = PolicyManager(config.policy.file, auto_verify=True)
        assert pm.domain_name == "GovernanceGuard"

        # Direct evaluation
        eval_result = pm.evaluate({
            "amount": 100000, "role": "DIRECTOR", "channel": "DIGITAL",
            "is_weekend": "NO", "urgency": "HIGH", "department": "ENGINEERING",
        })
        assert eval_result.result == "ALLOWED"

        # 3. AGENT DECISIONS (mix of allowed and blocked)
        decision_ids = []
        scenarios = [
            {"amount": 100000, "role": "DIRECTOR", "channel": "DIGITAL",
             "is_weekend": "NO", "urgency": "HIGH", "department": "ENGINEERING"},
            {"amount": 200000, "role": "MANAGER", "channel": "TV",
             "is_weekend": "NO", "urgency": "MEDIUM", "department": "MARKETING"},
            {"amount": 999999, "role": "ANALYST", "channel": "ALL",
             "is_weekend": "YES", "urgency": "LOW", "department": "HR"},
            {"amount": 50000, "role": "VP", "channel": "PRINT",
             "is_weekend": "NO", "urgency": "CRITICAL", "department": "FINANCE"},
        ]

        for i, params in enumerate(scenarios):
            mock_provider = _mock_llm_response([{
                "strategy": f"Lifecycle plan {i}",
                "parameters": params,
            }])
            with patch("chimera_compliance.agent.get_provider", return_value=mock_provider):
                agent = ChimeraAgent.from_config(config, config_path=config_yaml)
                result = agent.decide(f"Lifecycle request {i}")
                decision_ids.append(result.decision_id)

        # 4. AUDIT RECORDS
        audit_dir = str(project_dir / "audit_logs")
        audit_files = list(Path(audit_dir).glob("dec_*.json"))
        assert len(audit_files) == 4

        # 5. AUDIT STATS
        query = AuditQuery(audit_dir)
        stats = query.stats()
        assert stats.total_decisions == 4
        assert stats.allowed_count + stats.blocked_count == 4

        # Filter
        allowed = query.filter(result="ALLOWED")
        blocked = query.filter(result="BLOCKED")
        assert len(allowed) + len(blocked) == 4
        assert len(blocked) >= 1  # ANALYST with 999k must be blocked

        # Top violations
        violations = query.top_violations(n=10)
        if blocked:
            assert len(violations) > 0

        # 6. HTML EXPLANATION
        first_id = decision_ids[0]
        record = load_record(first_id, audit_dir=audit_dir)
        html = generate_html(record)
        assert "<!DOCTYPE html>" in html
        assert first_id in html

        html_path = project_dir / "docs" / f"{first_id}.html"
        html_path.parent.mkdir(parents=True, exist_ok=True)
        html_path.write_text(html, encoding="utf-8")
        assert html_path.exists()

        # 7. ANNEX IV DOCS
        try:
            from chimera_compliance import AnnexIVGenerator

            gen = AnnexIVGenerator(
                config=config,
                audit_dir=audit_dir,
                policy_path=config.policy.file,
            )
            doc_path = str(project_dir / "docs" / "annex_iv.md")
            gen.generate(output_path=doc_path)
            assert Path(doc_path).exists()

            status = gen.status()
            assert status["filled"] == 14
            assert status["manual_required"] == 5
        except ImportError:
            pass  # jinja2 optional

        # 8. CLI COMMANDS
        # Version
        r = runner.invoke(cli, ["--version"])
        assert r.exit_code == 0

        # Verify
        r = runner.invoke(cli, [
            "--config", config_yaml,
            "verify", config.policy.file,
        ])
        assert r.exit_code == 0
        assert "Policy Verified" in r.output

        # Audit stats
        r = runner.invoke(cli, [
            "--config", config_yaml,
            "audit", "--stats",
            "--audit-dir", audit_dir,
        ])
        assert r.exit_code == 0
        assert "Total Decisions" in r.output

        # Audit last 2
        r = runner.invoke(cli, [
            "--config", config_yaml,
            "audit", "--last", "2",
            "--audit-dir", audit_dir,
        ])
        assert r.exit_code == 0

        # Export
        export_path = str(project_dir / "export.json")
        r = runner.invoke(cli, [
            "--config", config_yaml,
            "audit", "--export", export_path,
            "--audit-dir", audit_dir,
        ])
        assert r.exit_code == 0
        assert Path(export_path).exists()

        exported = json.loads(Path(export_path).read_text())
        assert len(exported) == 4

        # Explain
        r = runner.invoke(cli, [
            "--config", config_yaml,
            "explain", "--id", first_id,
            "--output", str(project_dir / "docs" / "explain_cli.html"),
            "--audit-dir", audit_dir,
        ])
        assert r.exit_code == 0

    def test_policy_hot_reload(self, project_dir, config_yaml):
        """Policy hot-reload detects content changes."""
        from chimera_compliance import PolicyManager

        policy_path = str(project_dir / "policies" / "governance.csl")
        pm = PolicyManager(policy_path, auto_verify=True)

        original_hash = pm.hash
        assert not pm.reload()  # No change

        # Modify policy
        content = Path(policy_path).read_text()
        Path(policy_path).write_text(content + "\n", encoding="utf-8")
        assert pm.reload()  # Changed
        assert pm.hash != original_hash

    def test_retention_enforcement(self, project_dir, config_yaml):
        """Retention enforcement removes old records."""
        from chimera_compliance import enforce_retention
        import time

        audit_dir = str(project_dir / "audit_logs")

        # Create a fake old record
        old_file = Path(audit_dir) / "dec_old_test.json"
        old_data = {
            "schema_version": "2.0",
            "decision_id": "dec_old_test",
            "timestamp": "2020-01-01T00:00:00Z",
            "decision": {"result": "ALLOWED", "action_taken": "test",
                         "policy_file": "test.csl", "policy_hash": "sha256:test",
                         "final_parameters": {}},
            "agent": {"name": "test", "version": "0.1.0", "csl_core_version": "0.3.0",
                       "model": "test", "model_provider": "test", "temperature": 0.7},
            "input": {"raw_request": "test", "context": {}, "timestamp": "2020-01-01T00:00:00Z"},
            "reasoning": {"total_attempts": 1, "total_candidates": 1,
                          "selected_candidate": None, "attempts": []},
            "performance": {"total_duration_ms": 10.0, "llm_duration_ms": 5.0,
                            "policy_duration_ms": 1.0, "overhead_ms": 4.0},
            "compliance": {"eu_ai_act_articles": [], "annex_iv_refs": [],
                           "retention_until": "2020-07-01T00:00:00Z"},
        }
        old_file.write_text(json.dumps(old_data), encoding="utf-8")
        assert old_file.exists()

        # Set file mtime to 2 years ago so retention picks it up
        old_mtime = time.time() - (365 * 2 * 86400)
        os.utime(str(old_file), (old_mtime, old_mtime))

        removed = enforce_retention(audit_dir, retention_days=180)
        assert removed >= 1
        assert not old_file.exists()
