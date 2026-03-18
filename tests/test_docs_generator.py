"""
Tests for chimera_runtime.docs

Validates:
  - AnnexIVGenerator.generate() produces complete Markdown
  - Auto-filled sections (14/19) contain expected content
  - Manual sections (5/19) contain TODO markers
  - status() reports correct coverage
  - refresh() re-generates with latest data
  - Policy data extraction (variables, constraints, domain)
  - Audit stats integration (metrics, top violations)
  - Template rendering with and without audit data
"""

import json
import os
import pytest
from pathlib import Path
from typing import List

from chimera_runtime.docs import (
    AnnexIVGenerator,
    DocsGeneratorError,
    AUTO_SECTIONS,
    MANUAL_SECTIONS,
    SECTION_TITLES,
)
from chimera_runtime.models import (
    AgentConfig,
    AgentMetaConfig,
    AuditConfig,
    LLMConfig,
    OversightConfig,
    PolicyConfig,
)
from chimera_runtime.audit.storage import save_record


# ============================================================================
# FIXTURES
# ============================================================================

POLICY_DIR = Path(__file__).parent.parent / "policies"
GOVERNANCE_CSL = POLICY_DIR / "governance.csl"


def _csl_available() -> bool:
    try:
        from chimera_core import load_guard
        return GOVERNANCE_CSL.exists()
    except ImportError:
        return False


def _jinja2_available() -> bool:
    try:
        import jinja2
        return True
    except ImportError:
        return False


@pytest.fixture
def config():
    """Sample agent config for doc generation."""
    return AgentConfig(
        agent=AgentMetaConfig(name="test-chimera-runtime", version="0.2.0"),
        llm=LLMConfig(
            provider="openai",
            model="gpt-4o",
            temperature=0.7,
            max_retries=3,
            candidates_per_attempt=3,
        ),
        policy=PolicyConfig(
            file=str(GOVERNANCE_CSL),
            auto_verify=True,
        ),
        audit=AuditConfig(
            enabled=True,
            output_dir="./audit_logs",
            format="json",
            html_reports=True,
            retention_days=180,
        ),
        oversight=OversightConfig(
            require_confirmation=False,
            allow_override=True,
            policy_hot_reload=True,
            stop_on_consecutive_blocks=5,
        ),
    )


@pytest.fixture
def audit_dir(tmp_path):
    d = tmp_path / "audit_logs"
    d.mkdir()
    return str(d)


@pytest.fixture
def output_dir(tmp_path):
    d = tmp_path / "docs_output"
    d.mkdir()
    return str(d)


def _populate_audit(audit_dir: str, n_allowed: int = 4, n_blocked: int = 2):
    """Create sample audit records for testing."""
    from chimera_runtime.models import (
        AgentInfo, InputInfo, Attempt, Candidate, PolicyEvaluation,
        Violation, generate_decision_id, utc_now_iso,
    )
    from chimera_runtime.audit.recorder import build_audit_record

    for i in range(n_allowed):
        record = build_audit_record(
            agent_info=AgentInfo(
                name="test-agent", version="0.2.0", csl_core_version="0.3.0",
                model="gpt-4o", model_provider="openai", temperature=0.7,
            ),
            input_info=InputInfo(raw_request=f"Request {i}"),
            attempts=[Attempt(
                attempt_number=1,
                candidates=[Candidate(
                    candidate_id="cand_001",
                    strategy=f"Strategy {i}",
                    llm_reasoning="Good approach",
                    llm_confidence=0.85,
                    parameters={"amount": 150000},
                    policy_evaluation=PolicyEvaluation(
                        policy_file="governance.csl",
                        policy_hash="sha256:abc",
                        result="ALLOWED",
                        duration_ms=1.0,
                        violations=[],
                    ),
                )],
                outcome="ALL_PASSED",
            )],
            action_taken=f"Strategy {i}",
            result="ALLOWED",
            final_parameters={"amount": 150000},
            policy_file="governance.csl",
            policy_hash="sha256:abc",
            selected_candidate_id="cand_001",
            total_duration_ms=15.0,
        )
        save_record(record, audit_dir=audit_dir)

    for i in range(n_blocked):
        record = build_audit_record(
            agent_info=AgentInfo(
                name="test-agent", version="0.2.0", csl_core_version="0.3.0",
                model="gpt-4o", model_provider="openai", temperature=0.7,
            ),
            input_info=InputInfo(raw_request=f"Blocked request {i}"),
            attempts=[Attempt(
                attempt_number=1,
                candidates=[Candidate(
                    candidate_id="cand_001",
                    strategy=f"Bad strategy {i}",
                    llm_reasoning="Risky",
                    llm_confidence=0.6,
                    parameters={"amount": 500000},
                    policy_evaluation=PolicyEvaluation(
                        policy_file="governance.csl",
                        policy_hash="sha256:abc",
                        result="BLOCKED",
                        duration_ms=1.0,
                        violations=[Violation(
                            constraint="manager_approval_limit",
                            rule="amount > 250000",
                            trigger_values={"amount": 500000},
                            explanation="Exceeds MANAGER limit",
                        )],
                    ),
                )],
                outcome="ALL_BLOCKED",
            )],
            action_taken="BLOCKED",
            result="BLOCKED",
            final_parameters={},
            policy_file="governance.csl",
            policy_hash="sha256:abc",
            total_duration_ms=12.0,
        )
        save_record(record, audit_dir=audit_dir)


# ============================================================================
# SECTION DEFINITION TESTS
# ============================================================================

class TestSectionDefinitions:

    def test_auto_sections_count(self):
        assert len(AUTO_SECTIONS) == 14

    def test_manual_sections_count(self):
        assert len(MANUAL_SECTIONS) == 5

    def test_all_19_sections_covered(self):
        all_sections = sorted(AUTO_SECTIONS + MANUAL_SECTIONS)
        assert all_sections == list(range(1, 20))

    def test_manual_sections_are_correct(self):
        assert MANUAL_SECTIONS == [7, 8, 10, 18, 19]

    def test_section_titles_complete(self):
        assert len(SECTION_TITLES) == 19
        for i in range(1, 20):
            assert i in SECTION_TITLES


# ============================================================================
# GENERATE TESTS — WITH POLICY
# ============================================================================

@pytest.mark.skipif(not _csl_available(), reason="csl-core not installed")
@pytest.mark.skipif(not _jinja2_available(), reason="jinja2 not installed")
class TestGenerateWithPolicy:

    def test_generate_creates_file(self, config, output_dir):
        out = os.path.join(output_dir, "annex_iv.md")
        gen = AnnexIVGenerator(config=config)
        path = gen.generate(output_path=out)

        assert os.path.exists(path)
        assert path.endswith("annex_iv.md")

    def test_generate_markdown_header(self, config, output_dir):
        out = os.path.join(output_dir, "annex_iv.md")
        gen = AnnexIVGenerator(config=config)
        gen.generate(output_path=out)

        content = Path(out).read_text()
        assert "# EU AI Act — Annex IV Technical Documentation" in content
        assert "test-chimera-runtime" in content
        assert "0.2.0" in content

    def test_all_19_section_headers_present(self, config, output_dir):
        out = os.path.join(output_dir, "annex_iv.md")
        gen = AnnexIVGenerator(config=config)
        gen.generate(output_path=out)
        content = Path(out).read_text()

        for i in range(1, 20):
            assert f"## Section {i}" in content, f"Missing Section {i}"

    def test_auto_sections_have_content(self, config, output_dir):
        out = os.path.join(output_dir, "annex_iv.md")
        gen = AnnexIVGenerator(config=config)
        gen.generate(output_path=out)
        content = Path(out).read_text()

        # LLM config in Section 2
        assert "openai" in content
        assert "gpt-4o" in content
        assert "0.7" in content

        # Oversight in Section 9
        assert "agent.halt()" in content
        assert "Interactive" in content

        # Verification in Section 11
        assert "Z3" in content

    def test_manual_sections_have_todo(self, config, output_dir):
        out = os.path.join(output_dir, "annex_iv.md")
        gen = AnnexIVGenerator(config=config)
        gen.generate(output_path=out)
        content = Path(out).read_text()

        # Sections 7, 8, 10, 18, 19 should have manual markers
        assert "MANUAL INPUT REQUIRED" in content

    def test_policy_variables_in_output(self, config, output_dir):
        out = os.path.join(output_dir, "annex_iv.md")
        gen = AnnexIVGenerator(config=config)
        gen.generate(output_path=out)
        content = Path(out).read_text()

        # governance.csl has variables like amount, role
        assert "amount" in content
        assert "role" in content

    def test_policy_hash_in_output(self, config, output_dir):
        out = os.path.join(output_dir, "annex_iv.md")
        gen = AnnexIVGenerator(config=config)
        gen.generate(output_path=out)
        content = Path(out).read_text()

        assert "sha256:" in content

    def test_creates_parent_dirs(self, config, tmp_path):
        out = str(tmp_path / "deep" / "nested" / "annex_iv.md")
        gen = AnnexIVGenerator(config=config)
        path = gen.generate(output_path=out)
        assert os.path.exists(path)


# ============================================================================
# GENERATE TESTS — WITH AUDIT DATA
# ============================================================================

@pytest.mark.skipif(not _csl_available(), reason="csl-core not installed")
@pytest.mark.skipif(not _jinja2_available(), reason="jinja2 not installed")
class TestGenerateWithAudit:

    def test_audit_stats_in_output(self, config, audit_dir, output_dir):
        _populate_audit(audit_dir, n_allowed=4, n_blocked=2)

        out = os.path.join(output_dir, "annex_iv.md")
        gen = AnnexIVGenerator(config=config, audit_dir=audit_dir)
        gen.generate(output_path=out)
        content = Path(out).read_text()

        # Section 4 should have stats
        assert "Total Decisions" in content
        assert "6" in content  # 4 allowed + 2 blocked

    def test_top_violations_in_output(self, config, audit_dir, output_dir):
        _populate_audit(audit_dir, n_allowed=2, n_blocked=3)

        out = os.path.join(output_dir, "annex_iv.md")
        gen = AnnexIVGenerator(config=config, audit_dir=audit_dir)
        gen.generate(output_path=out)
        content = Path(out).read_text()

        assert "manager_approval_limit" in content

    def test_no_audit_shows_placeholder(self, config, output_dir, tmp_path):
        empty_audit = str(tmp_path / "empty_audit")
        os.makedirs(empty_audit, exist_ok=True)

        out = os.path.join(output_dir, "annex_iv.md")
        gen = AnnexIVGenerator(config=config, audit_dir=empty_audit)
        gen.generate(output_path=out)
        content = Path(out).read_text()

        assert "No audit data available" in content


# ============================================================================
# STATUS TESTS
# ============================================================================

@pytest.mark.skipif(not _csl_available(), reason="csl-core not installed")
class TestStatus:

    def test_status_without_audit(self, config, tmp_path):
        empty_audit = str(tmp_path / "no_audit")
        gen = AnnexIVGenerator(config=config, audit_dir=empty_audit)
        status = gen.status()

        assert status["total"] == 19
        assert status["manual_required"] == 5
        # Without audit, sections 4, 6, 17 drop out
        assert status["filled"] == 14 - 3  # 11
        assert len(status["pending_sections"]) == 3
        assert status["has_audit_data"] is False

    def test_status_with_audit(self, config, audit_dir):
        _populate_audit(audit_dir)
        gen = AnnexIVGenerator(config=config, audit_dir=audit_dir)
        status = gen.status()

        assert status["filled"] == 14
        assert status["has_audit_data"] is True
        assert len(status["pending_sections"]) == 0

    def test_status_auto_sections_listed(self, config, audit_dir):
        _populate_audit(audit_dir)
        gen = AnnexIVGenerator(config=config, audit_dir=audit_dir)
        status = gen.status()

        auto_nums = [s["section"] for s in status["auto_sections"]]
        for s in AUTO_SECTIONS:
            assert s in auto_nums

    def test_status_manual_sections_listed(self, config, audit_dir):
        gen = AnnexIVGenerator(config=config, audit_dir=audit_dir)
        status = gen.status()

        manual_nums = [s["section"] for s in status["manual_sections"]]
        assert manual_nums == MANUAL_SECTIONS


# ============================================================================
# REFRESH TESTS
# ============================================================================

@pytest.mark.skipif(not _csl_available(), reason="csl-core not installed")
@pytest.mark.skipif(not _jinja2_available(), reason="jinja2 not installed")
class TestRefresh:

    def test_refresh_uses_last_path(self, config, output_dir):
        out = os.path.join(output_dir, "annex_iv.md")
        gen = AnnexIVGenerator(config=config)
        gen.generate(output_path=out)

        # Modify something and refresh
        path = gen.refresh()
        assert path == out
        assert os.path.exists(path)

    def test_refresh_with_new_audit_data(self, config, audit_dir, output_dir):
        out = os.path.join(output_dir, "annex_iv.md")
        gen = AnnexIVGenerator(config=config, audit_dir=audit_dir)

        # Generate without audit data
        gen.generate(output_path=out)
        content1 = Path(out).read_text()
        assert "No audit data available" in content1

        # Add audit data and refresh
        _populate_audit(audit_dir)
        gen.refresh()
        content2 = Path(out).read_text()
        assert "Total Decisions" in content2

    def test_refresh_default_path(self, config, tmp_path):
        gen = AnnexIVGenerator(config=config)
        # No prior generate() — should use default path
        os.chdir(tmp_path)
        path = gen.refresh()
        assert os.path.exists(path)


# ============================================================================
# EDGE CASES
# ============================================================================

@pytest.mark.skipif(not _jinja2_available(), reason="jinja2 not installed")
class TestEdgeCases:

    def test_default_config(self, output_dir):
        """Generate with completely default config (no real policy)."""
        gen = AnnexIVGenerator(config=AgentConfig())
        out = os.path.join(output_dir, "annex_iv.md")
        path = gen.generate(output_path=out)

        assert os.path.exists(path)
        content = Path(out).read_text()
        assert "chimera-runtime" in content

    def test_nonexistent_policy_graceful(self, output_dir):
        """Should still generate even if policy file doesn't exist."""
        config = AgentConfig()
        config.policy.file = "/nonexistent/policy.csl"

        gen = AnnexIVGenerator(config=config)
        out = os.path.join(output_dir, "annex_iv.md")
        path = gen.generate(output_path=out)

        content = Path(out).read_text()
        assert "N/A" in content  # Policy hash falls back to N/A

    def test_coverage_string_in_header(self, config, output_dir):
        gen = AnnexIVGenerator(config=config)
        out = os.path.join(output_dir, "annex_iv.md")
        gen.generate(output_path=out)
        content = Path(out).read_text()

        assert "/19 sections auto-filled" in content
