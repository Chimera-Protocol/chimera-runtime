"""
End-to-End Scenario Test: AcmePay — A Fintech Startup's Compliance Journey

Simulates a real fintech company (AcmePay) adopting chimera-runtime
for EU AI Act compliance. Covers the full lifecycle:

  Phase 1: Company Setup — init, CSL policy (Z3 verified), config
  Phase 2: Normal Operations — 5 legitimate transactions (all ALLOWED)
  Phase 3: Error/Attack Scenarios — 4 violations + consecutive blocks (all BLOCKED)
  Phase 4: Human Override — operator overrides a blocked decision
  Phase 5: Policy Hot-Reload — manager limit raised 250k→500k
  Phase 6: Audit & Reporting — query, stats, export, Art. 86 HTML
  Phase 7: Annex IV Documentation — generate with real audit data
  Phase 8: CLI Verification — run key CLI commands against populated project

LLM calls are mocked. Everything else is real:
  - CSL policy with Z3 formal verification
  - Real filesystem (tmp_path) for audit records
  - Real AuditQuery for stats/export
  - Real AnnexIVGenerator for Annex IV docs
  - Real CliRunner for CLI commands
"""

import json
import os
import pytest
from pathlib import Path
from typing import Any, Dict, List, Optional

from chimera_runtime.agent import ChimeraAgent, AgentHalted
from chimera_runtime.llm.base import BaseLLMProvider, LLMError
from chimera_runtime.policy import PolicyManager, CSL_CORE_AVAILABLE
from chimera_runtime.oversight import HumanOversight
from chimera_runtime.models import (
    AgentConfig, AgentMetaConfig, LLMConfig, PolicyConfig,
    AuditConfig, OversightConfig, HumanOversightRecord,
)
from chimera_runtime.config import save_config, load_config
from chimera_runtime.audit.storage import save_record, load_record, load_all_records
from chimera_runtime.audit.query import AuditQuery
from chimera_runtime.audit.html_report import generate_html
from click.testing import CliRunner
from chimera_runtime.cli.main import cli


# Skip the entire module if CSL-Core is not available
pytestmark = pytest.mark.skipif(
    not CSL_CORE_AVAILABLE,
    reason="CSL-Core required for AcmePay scenario (Z3 formal verification)",
)


# ============================================================================
# MOCK LLM — returns pre-configured candidate JSON strings
# ============================================================================

class MockLLM(BaseLLMProvider):
    """Mock LLM that returns canned JSON responses for each decide() call."""

    def __init__(self, responses: List[str], **kwargs: Any):
        super().__init__(model="acmepay-gpt-4o", **kwargs)
        self._responses = responses
        self._call_index = 0
        self.call_count = 0

    @property
    def provider_name(self) -> str:
        return "mock"

    def _call_llm(self, messages: List[Dict[str, str]]) -> str:
        self.call_count += 1
        if self._call_index < len(self._responses):
            resp = self._responses[self._call_index]
            self._call_index += 1
            return resp
        raise LLMError("MockLLM: no more canned responses")


# ============================================================================
# CSL POLICY — AcmePay Payment Processing (6 constraints, Z3 verified)
# ============================================================================

ACMEPAY_POLICY_CSL = """\
CONFIG {
  ENFORCEMENT_MODE: BLOCK
  CHECK_LOGICAL_CONSISTENCY: TRUE
}

DOMAIN AcmePayGuard {
  VARIABLES {
    amount: 0..2000000
    role: {"ANALYST", "MANAGER", "DIRECTOR", "CFO"}
    transaction_type: {"VIEW", "TRANSFER", "REFUND", "PAYOUT"}
    is_weekend: {"YES", "NO"}
    risk_level: {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
    destination: {"DOMESTIC", "INTERNATIONAL", "INTERNAL"}
  }

  // Analysts can only VIEW — cannot approve any transaction
  STATE_CONSTRAINT analyst_view_only {
    WHEN role == "ANALYST"
    THEN transaction_type == "VIEW"
  }

  // Managers capped at $250,000
  STATE_CONSTRAINT manager_transfer_limit {
    WHEN role == "MANAGER"
    THEN amount <= 250000
  }

  // Directors capped at $750,000
  STATE_CONSTRAINT director_transfer_limit {
    WHEN role == "DIRECTOR"
    THEN amount <= 750000
  }

  // No operations on weekends unless CRITICAL
  STATE_CONSTRAINT weekend_non_critical {
    WHEN is_weekend == "YES"
    THEN risk_level == "CRITICAL"
  }

  // Absolute ceiling: $1,000,000
  STATE_CONSTRAINT absolute_ceiling {
    ALWAYS True
    THEN amount <= 1000000
  }

  // High-risk international transfers over $100k blocked (weekdays only)
  STATE_CONSTRAINT high_risk_international {
    WHEN risk_level == "HIGH" AND destination == "INTERNATIONAL" AND is_weekend == "NO"
    THEN amount <= 100000
  }
}
"""

# Updated policy: manager limit raised from $250k to $500k
ACMEPAY_POLICY_CSL_UPDATED = ACMEPAY_POLICY_CSL.replace(
    "THEN amount <= 250000",
    "THEN amount <= 500000",
)


# ============================================================================
# MOCK LLM RESPONSES — realistic candidate JSON for each scenario
# ============================================================================

def _make_candidates(params_list: List[Dict[str, Any]]) -> str:
    """Build a JSON string of candidates from a list of parameter dicts."""
    candidates = []
    for i, params in enumerate(params_list):
        candidates.append({
            "strategy": f"Strategy option {i+1}",
            "reasoning": f"Reasoning for option {i+1} with amount={params.get('amount', 0)}",
            "confidence": round(0.95 - i * 0.05, 2),
            "parameters": params,
        })
    return json.dumps(candidates)


_BASE = {"is_weekend": "NO", "risk_level": "LOW", "destination": "DOMESTIC"}

# ── Phase 2: Normal operations (all ALLOWED) ──

ANALYST_VIEW = _make_candidates([
    {**_BASE, "amount": 0, "role": "ANALYST", "transaction_type": "VIEW"},
    {**_BASE, "amount": 0, "role": "ANALYST", "transaction_type": "VIEW", "destination": "INTERNAL"},
    {**_BASE, "amount": 0, "role": "ANALYST", "transaction_type": "VIEW", "risk_level": "MEDIUM"},
])

MANAGER_50K = _make_candidates([
    {**_BASE, "amount": 50000, "role": "MANAGER", "transaction_type": "TRANSFER"},
    {**_BASE, "amount": 30000, "role": "MANAGER", "transaction_type": "TRANSFER"},
    {**_BASE, "amount": 45000, "role": "MANAGER", "transaction_type": "REFUND"},
])

MANAGER_200K = _make_candidates([
    {**_BASE, "amount": 200000, "role": "MANAGER", "transaction_type": "TRANSFER"},
    {**_BASE, "amount": 180000, "role": "MANAGER", "transaction_type": "PAYOUT"},
    {**_BASE, "amount": 150000, "role": "MANAGER", "transaction_type": "TRANSFER"},
])

DIRECTOR_500K = _make_candidates([
    {**_BASE, "amount": 500000, "role": "DIRECTOR", "transaction_type": "PAYOUT"},
    {**_BASE, "amount": 450000, "role": "DIRECTOR", "transaction_type": "TRANSFER"},
    {**_BASE, "amount": 400000, "role": "DIRECTOR", "transaction_type": "TRANSFER"},
])

CFO_900K = _make_candidates([
    {**_BASE, "amount": 900000, "role": "CFO", "transaction_type": "PAYOUT"},
    {**_BASE, "amount": 850000, "role": "CFO", "transaction_type": "TRANSFER"},
    {**_BASE, "amount": 800000, "role": "CFO", "transaction_type": "PAYOUT"},
])

# ── Phase 3: Error/attack scenarios (all BLOCKED) ──

# A: Analyst tries to approve a TRANSFER
ANALYST_TRANSFER_BLOCKED = _make_candidates([
    {**_BASE, "amount": 50000, "role": "ANALYST", "transaction_type": "TRANSFER"},
    {**_BASE, "amount": 25000, "role": "ANALYST", "transaction_type": "REFUND"},
    {**_BASE, "amount": 10000, "role": "ANALYST", "transaction_type": "PAYOUT"},
])

# B: Manager tries $500k (exceeds $250k limit)
MANAGER_500K_BLOCKED = _make_candidates([
    {**_BASE, "amount": 500000, "role": "MANAGER", "transaction_type": "TRANSFER"},
    {**_BASE, "amount": 400000, "role": "MANAGER", "transaction_type": "PAYOUT"},
    {**_BASE, "amount": 300000, "role": "MANAGER", "transaction_type": "TRANSFER"},
])

# C: Weekend non-critical transaction (CFO role to isolate weekend constraint)
WEEKEND_BLOCKED = _make_candidates([
    {"amount": 50000, "role": "CFO", "transaction_type": "TRANSFER",
     "is_weekend": "YES", "risk_level": "MEDIUM", "destination": "DOMESTIC"},
    {"amount": 30000, "role": "CFO", "transaction_type": "REFUND",
     "is_weekend": "YES", "risk_level": "LOW", "destination": "DOMESTIC"},
    {"amount": 20000, "role": "CFO", "transaction_type": "TRANSFER",
     "is_weekend": "YES", "risk_level": "HIGH", "destination": "DOMESTIC"},
])

# D: Amount exceeds absolute ceiling ($2M)
CEILING_BLOCKED = _make_candidates([
    {**_BASE, "amount": 2000000, "role": "CFO", "transaction_type": "PAYOUT"},
    {**_BASE, "amount": 1500000, "role": "CFO", "transaction_type": "TRANSFER"},
    {**_BASE, "amount": 1200000, "role": "CFO", "transaction_type": "PAYOUT"},
])

# ── Phase 5: After policy update, Manager $400k passes ──

MANAGER_400K_AFTER_UPDATE = _make_candidates([
    {**_BASE, "amount": 400000, "role": "MANAGER", "transaction_type": "TRANSFER"},
    {**_BASE, "amount": 350000, "role": "MANAGER", "transaction_type": "PAYOUT"},
    {**_BASE, "amount": 300000, "role": "MANAGER", "transaction_type": "TRANSFER"},
])


# ============================================================================
# THE SCENARIO TEST
# ============================================================================

def test_acmepay_full_journey(tmp_path):
    """
    AcmePay's complete compliance journey — from project setup through
    Annex IV documentation with real audit data.

    A single test function that tells the story of a fintech startup
    adopting EU AI Act compliance. ~90 assertions across 8 phases.
    """

    # ── Project directory structure ──
    project = tmp_path / "acmepay"
    project.mkdir()
    policies_dir = project / "policies"
    policies_dir.mkdir()
    audit_dir = project / "audit_logs"
    audit_dir.mkdir()
    config_dir = project / ".chimera"
    config_dir.mkdir()
    docs_dir = project / "docs"
    docs_dir.mkdir()
    reports_dir = project / "reports"
    reports_dir.mkdir()

    policy_path = policies_dir / "payments.csl"
    config_path = config_dir / "config.yaml"
    runner = CliRunner()

    # ================================================================
    # PHASE 1: Company Setup
    # ================================================================
    # AcmePay initializes their compliance project, writes a custom
    # payment processing policy, and verifies it with Z3.

    # 1.1: Write the CSL policy
    policy_path.write_text(ACMEPAY_POLICY_CSL, encoding="utf-8")

    # 1.2: Create and save config
    config = AgentConfig(
        agent=AgentMetaConfig(name="acmepay-agent", version="1.0.0"),
        llm=LLMConfig(provider="openai", model="gpt-4o", temperature=0.7),
        policy=PolicyConfig(file=str(policy_path), auto_verify=True),
        audit=AuditConfig(
            enabled=True,
            output_dir=str(audit_dir),
            format="json",
            html_reports=True,
            retention_days=365,
        ),
        oversight=OversightConfig(
            require_confirmation=False,
            allow_override=True,
            stop_on_consecutive_blocks=3,
        ),
    )
    save_config(config, str(config_path))
    assert config_path.exists(), "Config file must exist after save"

    # 1.3: Load and verify policy with Z3
    pm = PolicyManager(str(policy_path), auto_verify=True)
    assert pm.domain_name == "AcmePayGuard"
    assert pm.constraint_count == 6
    assert pm.backend == "csl-core"
    assert pm.hash.startswith("sha256:")
    assert "amount" in pm.variable_names
    assert "role" in pm.variable_names
    assert "transaction_type" in pm.variable_names

    # 1.4: Verify policy via CLI
    r = runner.invoke(cli, ["--config", str(config_path), "verify", str(policy_path)])
    assert r.exit_code == 0, f"verify failed: {r.output}"

    # 1.5: Run system test (skip LLM)
    r = runner.invoke(cli, ["--config", str(config_path), "test", "--skip-llm"])
    assert r.exit_code == 0, f"test --skip-llm failed: {r.output}"

    # ================================================================
    # PHASE 2: Normal Operations (Day 1-30)
    # ================================================================
    # AcmePay processes 5 legitimate payment requests.
    # All must be ALLOWED by the Z3-verified policy.

    decision_ids: List[str] = []

    normal_scenarios = [
        ("Review daily transactions",              ANALYST_VIEW,    "Analyst VIEW"),
        ("Approve vendor payment $50k",             MANAGER_50K,     "Manager $50k"),
        ("Approve marketing invoice $200k",         MANAGER_200K,    "Manager $200k"),
        ("Approve Q1 payout $500k",                 DIRECTOR_500K,   "Director $500k"),
        ("Approve international wire $900k to HQ",  CFO_900K,        "CFO $900k"),
    ]

    for request_text, mock_response, label in normal_scenarios:
        agent = ChimeraAgent(
            llm_provider=MockLLM(responses=[mock_response]),
            policy_manager=PolicyManager(str(policy_path), auto_verify=False),
            audit_dir=str(audit_dir),
            agent_name="acmepay-agent",
            max_retries=1,
        )
        result = agent.decide(request_text)

        assert result.result == "ALLOWED", f"{label} should be ALLOWED, got {result.result}"
        assert result.decision_id.startswith("dec_")
        assert result.audit is not None
        assert result.audit.decision.policy_hash.startswith("sha256:")
        decision_ids.append(result.decision_id)

    # 5 audit files must exist
    audit_files = list(audit_dir.glob("dec_*.json"))
    assert len(audit_files) == 5, f"Expected 5 audit files, got {len(audit_files)}"

    # ================================================================
    # PHASE 3: Error / Attack Scenarios
    # ================================================================
    # Bad requests arrive. The Z3-verified policy catches them all.

    blocked_ids: List[str] = []

    # ── Scenario A: Analyst tries to approve a TRANSFER ──
    agent_a = ChimeraAgent(
        llm_provider=MockLLM(responses=[ANALYST_TRANSFER_BLOCKED]),
        policy_manager=PolicyManager(str(policy_path), auto_verify=False),
        audit_dir=str(audit_dir),
        agent_name="acmepay-agent",
        max_retries=1,
    )
    result_a = agent_a.decide("Analyst approves payment directly")
    assert result_a.result == "BLOCKED"
    assert "analyst_view_only" in result_a.explanation
    blocked_ids.append(result_a.decision_id)
    decision_ids.append(result_a.decision_id)

    # ── Scenario B: Manager tries $500k (exceeds $250k limit) ──
    agent_b = ChimeraAgent(
        llm_provider=MockLLM(responses=[MANAGER_500K_BLOCKED]),
        policy_manager=PolicyManager(str(policy_path), auto_verify=False),
        audit_dir=str(audit_dir),
        agent_name="acmepay-agent",
        max_retries=1,
    )
    result_b = agent_b.decide("Approve large vendor payment $500k")
    assert result_b.result == "BLOCKED"
    assert "manager_transfer_limit" in result_b.explanation
    blocked_ids.append(result_b.decision_id)
    decision_ids.append(result_b.decision_id)

    # ── Scenario C: Weekend non-critical transaction ──
    agent_c = ChimeraAgent(
        llm_provider=MockLLM(responses=[WEEKEND_BLOCKED]),
        policy_manager=PolicyManager(str(policy_path), auto_verify=False),
        audit_dir=str(audit_dir),
        agent_name="acmepay-agent",
        max_retries=1,
    )
    result_c = agent_c.decide("Process weekend refund")
    assert result_c.result == "BLOCKED"
    assert "weekend_non_critical" in result_c.explanation
    blocked_ids.append(result_c.decision_id)
    decision_ids.append(result_c.decision_id)

    # ── Scenario D: Amount exceeds absolute ceiling ($2M) ──
    agent_d = ChimeraAgent(
        llm_provider=MockLLM(responses=[CEILING_BLOCKED]),
        policy_manager=PolicyManager(str(policy_path), auto_verify=False),
        audit_dir=str(audit_dir),
        agent_name="acmepay-agent",
        max_retries=1,
    )
    result_d = agent_d.decide("Approve mega transaction $2M")
    assert result_d.result == "BLOCKED"
    assert "absolute_ceiling" in result_d.explanation
    blocked_ids.append(result_d.decision_id)
    decision_ids.append(result_d.decision_id)

    # ── Scenario E: Consecutive blocks trigger threshold ──
    # Same agent instance — tracks consecutive_blocks internally
    consecutive_agent = ChimeraAgent(
        llm_provider=MockLLM(responses=[ANALYST_TRANSFER_BLOCKED] * 5),
        policy_manager=PolicyManager(str(policy_path), auto_verify=False),
        audit_dir=str(audit_dir),
        agent_name="acmepay-agent",
        max_retries=1,
    )
    for i in range(3):
        r = consecutive_agent.decide(f"Consecutive bad request #{i+1}")
        assert r.result == "BLOCKED"
        decision_ids.append(r.decision_id)

    assert consecutive_agent.consecutive_blocks == 3, \
        f"Expected 3 consecutive blocks, got {consecutive_agent.consecutive_blocks}"

    # Total: 5 (normal) + 4 (A-D) + 3 (consecutive) = 12
    all_audit_files = list(audit_dir.glob("dec_*.json"))
    assert len(all_audit_files) == 12, f"Expected 12 audit files, got {len(all_audit_files)}"

    # ================================================================
    # PHASE 4: Human Override
    # ================================================================
    # AcmePay's compliance officer reviews blocked decision B
    # (Manager $500k) and issues a verbal override.

    oversight = HumanOversight(mode="auto")
    override_record = oversight.apply_override(
        action="OVERRIDE",
        reason="CFO verbally approved $500k payment to critical vendor — emergency procurement",
    )
    assert isinstance(override_record, HumanOversightRecord)
    assert override_record.action == "OVERRIDE"
    assert "CFO verbally approved" in override_record.reason
    assert override_record.timestamp.endswith("Z")

    # Verify blocked record B is loadable from disk
    blocked_record_b = load_record(result_b.decision_id, audit_dir=str(audit_dir))
    assert blocked_record_b.decision.result == "BLOCKED"
    assert blocked_record_b.agent.name == "acmepay-agent"

    # ================================================================
    # PHASE 5: Policy Hot-Reload
    # ================================================================
    # AcmePay raises manager limit from $250k to $500k after board approval.
    # The agent detects the change and reloads the policy.

    pm_reload = PolicyManager(str(policy_path), auto_verify=False)
    original_hash = pm_reload.hash

    # Verify $400k is currently BLOCKED for managers
    eval_before = pm_reload.evaluate({
        "amount": 400000, "role": "MANAGER", "transaction_type": "TRANSFER",
        "is_weekend": "NO", "risk_level": "LOW", "destination": "DOMESTIC",
    })
    assert eval_before.result == "BLOCKED", "400k should be BLOCKED under old policy"

    # Write updated policy (manager limit 250k → 500k)
    policy_path.write_text(ACMEPAY_POLICY_CSL_UPDATED, encoding="utf-8")

    # Hot-reload detects the change
    reloaded = pm_reload.reload()
    assert reloaded is True, "reload() should return True when policy changed"
    assert pm_reload.hash != original_hash, "Hash must change after policy update"

    # Now $400k should be ALLOWED for managers
    eval_after = pm_reload.evaluate({
        "amount": 400000, "role": "MANAGER", "transaction_type": "TRANSFER",
        "is_weekend": "NO", "risk_level": "LOW", "destination": "DOMESTIC",
    })
    assert eval_after.result == "ALLOWED", "400k should be ALLOWED under new policy"

    # Run an agent decision with the updated policy
    agent_reload = ChimeraAgent(
        llm_provider=MockLLM(responses=[MANAGER_400K_AFTER_UPDATE]),
        policy_manager=pm_reload,
        audit_dir=str(audit_dir),
        agent_name="acmepay-agent",
        max_retries=1,
    )
    result_reload = agent_reload.decide("Approve $400k vendor payment after policy update")
    assert result_reload.result == "ALLOWED", \
        f"Post-reload $400k should be ALLOWED, got {result_reload.result}"
    decision_ids.append(result_reload.decision_id)

    # Total: 13 audit records
    assert len(list(audit_dir.glob("dec_*.json"))) == 13

    # ================================================================
    # PHASE 6: Audit & Compliance Reporting
    # ================================================================
    # AcmePay runs audit queries, generates statistics, exports data,
    # and creates Art. 86 explanation HTML for a blocked decision.

    query = AuditQuery(str(audit_dir))

    # 6.1: Filter by result
    blocked_records = query.filter(result="BLOCKED")
    allowed_records = query.filter(result="ALLOWED")
    assert len(blocked_records) == 7, f"Expected 7 blocked, got {len(blocked_records)}"
    assert len(allowed_records) == 6, f"Expected 6 allowed, got {len(allowed_records)}"

    # 6.2: Statistics
    stats = query.stats()
    assert stats.total_decisions == 13
    assert stats.allowed_count == 6
    assert stats.blocked_count == 7
    expected_block_rate = 7 / 13
    assert abs(stats.block_rate - expected_block_rate) < 0.01, \
        f"Block rate should be ~{expected_block_rate:.3f}, got {stats.block_rate:.3f}"
    assert stats.avg_duration_ms > 0, "Average duration must be > 0"

    # 6.3: Top violations
    violations = query.top_violations(n=10)
    assert len(violations) > 0, "Should have at least one violation type"
    violation_names = [name for name, count in violations]
    assert "analyst_view_only" in violation_names, \
        f"analyst_view_only should be in top violations, got {violation_names}"

    # 6.4: Export — JSON format
    json_export = str(reports_dir / "audit_export.json")
    query.export(json_export, format="json")
    assert Path(json_export).exists()
    exported_data = json.loads(Path(json_export).read_text())
    assert len(exported_data) == 13, f"Export should have 13 records, got {len(exported_data)}"

    # 6.5: Export — stats format
    stats_export = str(reports_dir / "stats_export.json")
    query.export(stats_export, format="stats")
    assert Path(stats_export).exists()
    stats_data = json.loads(Path(stats_export).read_text())
    assert stats_data["total_decisions"] == 13

    # 6.6: Art. 86 HTML explanation for blocked decision A (analyst violation)
    blocked_record_a = load_record(blocked_ids[0], audit_dir=str(audit_dir))
    html_content = generate_html(blocked_record_a)
    assert "<!DOCTYPE html>" in html_content
    assert blocked_ids[0] in html_content
    assert "BLOCKED" in html_content

    html_path = docs_dir / f"{blocked_ids[0]}_explanation.html"
    html_path.write_text(html_content, encoding="utf-8")
    assert html_path.exists()

    # ================================================================
    # PHASE 7: Annex IV Documentation
    # ================================================================
    # Generate EU AI Act Annex IV technical documentation
    # using real audit data — no hardcoded content.

    try:
        from chimera_runtime.docs import AnnexIVGenerator

        saved_config = load_config(str(config_path))
        gen = AnnexIVGenerator(
            config=saved_config,
            audit_dir=str(audit_dir),
            policy_path=str(policy_path),
        )

        annex_output = str(docs_dir / "annex_iv.md")
        gen.generate(output_path=annex_output)
        assert Path(annex_output).exists()

        annex_content = Path(annex_output).read_text()

        # Verify REAL data, not hardcoded placeholders
        assert "acmepay-agent" in annex_content, "Agent name must appear in Annex IV"
        assert "AcmePayGuard" in annex_content, "Domain name must appear in Annex IV"
        assert "Total Decisions" in annex_content, "Audit stats must be in Annex IV"
        assert "13" in annex_content, "Decision count (13) must appear"
        assert "Z3" in annex_content, "Z3 verifier must be mentioned (CSL backend)"
        assert "CSL-Core" in annex_content, "CSL-Core engine must be mentioned"

        # Status check
        status = gen.status()
        assert status["filled"] == 14, f"Expected 14/19 filled, got {status['filled']}"
        assert status["manual_required"] == 5
        assert status["has_audit_data"] is True
        assert status["has_policy_data"] is True

    except ImportError:
        pytest.skip("jinja2 not installed — skipping Annex IV tests")

    # ================================================================
    # PHASE 8: CLI Verification
    # ================================================================
    # Verify all key CLI commands work against the populated project.

    # 8.1: audit --stats
    r = runner.invoke(cli, [
        "--config", str(config_path),
        "audit", "--stats", "--audit-dir", str(audit_dir),
    ])
    assert r.exit_code == 0, f"audit --stats failed: {r.output}"

    # 8.2: audit --violations
    r = runner.invoke(cli, [
        "--config", str(config_path),
        "audit", "--violations", "--audit-dir", str(audit_dir),
    ])
    assert r.exit_code == 0, f"audit --violations failed: {r.output}"

    # 8.3: audit --result BLOCKED
    r = runner.invoke(cli, [
        "--config", str(config_path),
        "audit", "--result", "BLOCKED", "--audit-dir", str(audit_dir),
    ])
    assert r.exit_code == 0, f"audit --result BLOCKED failed: {r.output}"

    # 8.4: audit --export
    cli_export = str(reports_dir / "cli_export.json")
    r = runner.invoke(cli, [
        "--config", str(config_path),
        "audit", "--export", cli_export, "--audit-dir", str(audit_dir),
    ])
    assert r.exit_code == 0, f"audit --export failed: {r.output}"
    assert Path(cli_export).exists()

    # 8.5: explain --id (Art. 86 HTML via CLI)
    explain_output = str(docs_dir / "cli_explanation.html")
    r = runner.invoke(cli, [
        "--config", str(config_path),
        "explain", "--id", blocked_ids[0],
        "--output", explain_output,
        "--audit-dir", str(audit_dir),
    ])
    assert r.exit_code == 0, f"explain failed: {r.output}"
    assert Path(explain_output).exists()
    cli_html = Path(explain_output).read_text()
    assert "<!DOCTYPE html>" in cli_html

    # 8.6: docs generate (Annex IV via CLI)
    try:
        import jinja2  # noqa: F401
        cli_annex = str(docs_dir / "cli_annex_iv.md")
        r = runner.invoke(cli, [
            "--config", str(config_path),
            "docs", "generate",
            "--output", cli_annex,
            "--audit-dir", str(audit_dir),
            "--policy", str(policy_path),
        ])
        assert r.exit_code == 0, f"docs generate failed: {r.output}"
        assert Path(cli_annex).exists()
    except ImportError:
        pass

    # 8.7: docs status
    r = runner.invoke(cli, [
        "--config", str(config_path),
        "docs", "status", "--audit-dir", str(audit_dir),
    ])
    assert r.exit_code == 0, f"docs status failed: {r.output}"
    assert "/19" in r.output

    # ================================================================
    # STORY COMPLETE ✅
    # ================================================================
    # AcmePay has successfully:
    #   ✅ Initialized with Z3-verified CSL policy (6 constraints)
    #   ✅ Processed 5 legitimate transactions (ALLOWED)
    #   ✅ Blocked 7 policy violations (analyst/limit/weekend/ceiling)
    #   ✅ Recorded human override with justification
    #   ✅ Hot-reloaded updated policy (manager limit 250k→500k)
    #   ✅ Queried audit trail (7 blocked, 6 allowed, 53.8% block rate)
    #   ✅ Exported reports (JSON + stats + Art. 86 HTML)
    #   ✅ Generated Annex IV documentation with real data (14/19 sections)
    #   ✅ Verified all CLI commands work correctly
