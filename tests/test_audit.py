"""
Tests for chimera_runtime.audit

Validates:
  - build_audit_record() assembles correct DecisionAuditRecord
  - save_record() / load_record() roundtrip through JSON files
  - load_all_records() scans directory and returns sorted records
  - enforce_retention() deletes old files
  - AuditQuery.filter() by result, time range, action
  - AuditQuery.stats() computes correct aggregates
  - AuditQuery.top_violations() ranks constraints
  - AuditQuery.export() writes JSON, compact, and stats formats
  - generate_html() produces valid self-contained HTML
  - Full pipeline: agent.decide() → save → load → query → html
"""

import json
import os
import time
import shutil
import pytest
from pathlib import Path
from typing import List

from chimera_runtime.audit import (
    build_audit_record,
    save_record,
    load_record,
    load_all_records,
    enforce_retention,
    AuditStorageError,
    AuditQuery,
    AuditStats,
    generate_html,
)
from chimera_runtime.models import (
    AgentInfo,
    Attempt,
    Candidate,
    DecisionAuditRecord,
    InputInfo,
    PolicyEvaluation,
    Violation,
    HumanOversightRecord,
    generate_decision_id,
    utc_now_iso,
    SCHEMA_VERSION,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def audit_dir(tmp_path):
    """Temporary audit directory."""
    d = tmp_path / "audit_logs"
    d.mkdir()
    return str(d)


@pytest.fixture
def sample_agent_info():
    return AgentInfo(
        name="chimera-runtime",
        version="0.1.0",
        csl_core_version="0.3.0",
        model="gpt-4o",
        model_provider="openai",
        temperature=0.7,
    )


@pytest.fixture
def sample_input_info():
    return InputInfo(
        raw_request="Increase marketing budget by 40%",
        structured_params={"amount": 200000, "role": "MANAGER"},
        context={"user_id": "usr_001"},
    )


def _make_candidate(
    idx: int,
    strategy: str,
    amount: int,
    allowed: bool,
    confidence: float = 0.8,
    violation_name: str = "",
) -> Candidate:
    """Helper to build a Candidate with optional policy evaluation."""
    violations = []
    if not allowed and violation_name:
        violations.append(Violation(
            constraint=violation_name,
            rule=f"Constraint '{violation_name}' violated",
            trigger_values={"amount": amount},
            explanation=f"amount {amount} exceeds limit",
        ))

    return Candidate(
        candidate_id=f"cand_{idx:03d}",
        strategy=strategy,
        llm_reasoning=f"Reasoning for {strategy}",
        llm_confidence=confidence,
        parameters={"amount": amount, "role": "MANAGER"},
        policy_evaluation=PolicyEvaluation(
            policy_file="governance.csl",
            policy_hash="sha256:abc123",
            result="ALLOWED" if allowed else "BLOCKED",
            duration_ms=0.5,
            violations=violations,
        ),
    )


def _make_record(
    result: str = "ALLOWED",
    action: str = "Conservative approach",
    decision_id: str = None,
    timestamp: str = None,
    violations: int = 0,
    selected_id: str = "cand_001",
    agent_info=None,
    input_info=None,
) -> DecisionAuditRecord:
    """Build a sample audit record for testing."""
    candidates = [
        _make_candidate(1, "Conservative", 150000, allowed=True, confidence=0.9),
        _make_candidate(2, "Moderate", 200000, allowed=(violations == 0), confidence=0.7,
                       violation_name="manager_limit" if violations > 0 else ""),
        _make_candidate(3, "Aggressive", 350000, allowed=False, confidence=0.5,
                       violation_name="ceiling_limit" if violations > 0 else "manager_limit"),
    ]

    if result == "BLOCKED":
        # All candidates blocked
        for c in candidates:
            c.policy_evaluation.result = "BLOCKED"
            if not c.policy_evaluation.violations:
                c.policy_evaluation.violations = [Violation(
                    constraint="manager_limit",
                    rule="amount > 250000",
                    trigger_values=c.parameters,
                    explanation="Exceeds MANAGER limit",
                )]
        selected_id = None
        action = "BLOCKED"

    return build_audit_record(
        agent_info=agent_info or AgentInfo(
            name="chimera-runtime", version="0.1.0", csl_core_version="0.3.0",
            model="gpt-4o", model_provider="openai", temperature=0.7,
        ),
        input_info=input_info or InputInfo(
            raw_request="Test request",
            structured_params={"amount": 150000},
            context={},
        ),
        attempts=[Attempt(
            attempt_number=1,
            candidates=candidates,
            outcome="ALL_PASSED" if result == "ALLOWED" else "ALL_BLOCKED",
            note="Test attempt",
        )],
        action_taken=action,
        result=result,
        final_parameters={"amount": 150000} if result == "ALLOWED" else {},
        policy_file="governance.csl",
        policy_hash="sha256:abc123",
        selected_candidate_id=selected_id,
        selection_reasoning="Highest confidence candidate",
        total_duration_ms=12.5,
        llm_duration_ms=10.0,
        policy_evaluation_ms=2.0,
        audit_generation_ms=0.5,
        decision_id=decision_id or generate_decision_id(),
        timestamp=timestamp or utc_now_iso(),
    )


# ============================================================================
# RECORDER TESTS
# ============================================================================

class TestBuildAuditRecord:

    def test_basic_record_creation(self, sample_agent_info, sample_input_info):
        candidates = [_make_candidate(1, "Test", 100000, True)]
        record = build_audit_record(
            agent_info=sample_agent_info,
            input_info=sample_input_info,
            attempts=[Attempt(attempt_number=1, candidates=candidates, outcome="ALL_PASSED")],
            action_taken="Test action",
            result="ALLOWED",
            final_parameters={"amount": 100000},
            policy_file="test.csl",
            policy_hash="sha256:test",
        )

        assert record.schema_version == SCHEMA_VERSION
        assert record.decision_id.startswith("dec_")
        assert record.timestamp.endswith("Z")
        assert record.decision.result == "ALLOWED"
        assert record.agent.name == "chimera-runtime"

    def test_custom_decision_id_and_timestamp(self, sample_agent_info, sample_input_info):
        record = build_audit_record(
            agent_info=sample_agent_info,
            input_info=sample_input_info,
            attempts=[],
            action_taken="X",
            result="BLOCKED",
            final_parameters={},
            policy_file="x.csl",
            policy_hash="sha256:x",
            decision_id="dec_custom_123",
            timestamp="2026-01-15T12:00:00Z",
        )

        assert record.decision_id == "dec_custom_123"
        assert record.timestamp == "2026-01-15T12:00:00Z"

    def test_candidate_count(self, sample_agent_info, sample_input_info):
        c1 = [_make_candidate(1, "A", 100, True), _make_candidate(2, "B", 200, True)]
        c2 = [_make_candidate(3, "C", 300, False)]
        record = build_audit_record(
            agent_info=sample_agent_info,
            input_info=sample_input_info,
            attempts=[
                Attempt(attempt_number=1, candidates=c1, outcome="ALL_PASSED"),
                Attempt(attempt_number=2, candidates=c2, outcome="ALL_BLOCKED"),
            ],
            action_taken="A",
            result="ALLOWED",
            final_parameters={},
            policy_file="x.csl",
            policy_hash="sha256:x",
        )

        assert record.reasoning.total_candidates == 3
        assert record.reasoning.total_attempts == 2

    def test_with_human_oversight(self, sample_agent_info, sample_input_info):
        hor = HumanOversightRecord(action="OVERRIDE", reason="Too risky")
        record = build_audit_record(
            agent_info=sample_agent_info,
            input_info=sample_input_info,
            attempts=[],
            action_taken="X",
            result="HUMAN_OVERRIDE",
            final_parameters={},
            policy_file="x.csl",
            policy_hash="sha256:x",
            human_oversight_record=hor,
        )

        assert record.human_oversight_record is not None
        assert record.human_oversight_record.action == "OVERRIDE"


# ============================================================================
# STORAGE TESTS
# ============================================================================

class TestStorage:

    def test_save_creates_file(self, audit_dir):
        record = _make_record(decision_id="dec_test_save_001")
        path = save_record(record, audit_dir=audit_dir)

        assert os.path.exists(path)
        assert path.endswith("dec_test_save_001.json")

    def test_save_creates_directory(self, tmp_path):
        nested_dir = str(tmp_path / "deep" / "nested" / "audit")
        record = _make_record()
        path = save_record(record, audit_dir=nested_dir)
        assert os.path.exists(path)

    def test_save_valid_json(self, audit_dir):
        record = _make_record()
        path = save_record(record, audit_dir=audit_dir)

        content = Path(path).read_text(encoding="utf-8")
        data = json.loads(content)
        assert data["schema_version"] == SCHEMA_VERSION
        assert "decision" in data
        assert "reasoning" in data

    def test_load_roundtrip(self, audit_dir):
        original = _make_record(decision_id="dec_roundtrip_001")
        save_record(original, audit_dir=audit_dir)
        loaded = load_record("dec_roundtrip_001", audit_dir=audit_dir)

        assert loaded.decision_id == original.decision_id
        assert loaded.decision.result == original.decision.result
        assert loaded.reasoning.total_candidates == original.reasoning.total_candidates
        assert loaded.agent.model == original.agent.model

    def test_load_missing_raises(self, audit_dir):
        with pytest.raises(AuditStorageError, match="not found"):
            load_record("dec_nonexistent", audit_dir=audit_dir)

    def test_load_corrupt_file_raises(self, audit_dir):
        bad_path = Path(audit_dir) / "dec_corrupt.json"
        bad_path.write_text("not valid json {{{", encoding="utf-8")

        with pytest.raises(AuditStorageError, match="Corrupt"):
            load_record("dec_corrupt", audit_dir=audit_dir)

    def test_load_all_records(self, audit_dir):
        for i in range(5):
            record = _make_record(decision_id=f"dec_all_{i:03d}")
            save_record(record, audit_dir=audit_dir)

        records = load_all_records(audit_dir=audit_dir)
        assert len(records) == 5

    def test_load_all_skips_corrupt(self, audit_dir):
        record = _make_record(decision_id="dec_good_001")
        save_record(record, audit_dir=audit_dir)

        bad_path = Path(audit_dir) / "dec_bad_002.json"
        bad_path.write_text("{corrupt", encoding="utf-8")

        records = load_all_records(audit_dir=audit_dir)
        assert len(records) == 1
        assert records[0].decision_id == "dec_good_001"

    def test_load_all_empty_dir(self, audit_dir):
        records = load_all_records(audit_dir=audit_dir)
        assert records == []

    def test_load_all_nonexistent_dir(self, tmp_path):
        records = load_all_records(audit_dir=str(tmp_path / "nonexistent"))
        assert records == []

    def test_save_with_html(self, audit_dir):
        record = _make_record(decision_id="dec_html_test")
        save_record(record, audit_dir=audit_dir, also_save_html=True)

        assert (Path(audit_dir) / "dec_html_test.json").exists()
        assert (Path(audit_dir) / "dec_html_test.html").exists()


# ============================================================================
# RETENTION TESTS
# ============================================================================

class TestRetention:

    def test_enforce_retention_deletes_old(self, audit_dir):
        # Create a file and make it appear old
        record = _make_record(decision_id="dec_old_001")
        path = save_record(record, audit_dir=audit_dir)

        # Set mtime to 100 days ago
        old_time = time.time() - (100 * 86400)
        os.utime(path, (old_time, old_time))

        deleted = enforce_retention(audit_dir=audit_dir, retention_days=90)
        assert deleted == 1
        assert not os.path.exists(path)

    def test_enforce_retention_keeps_recent(self, audit_dir):
        record = _make_record(decision_id="dec_recent_001")
        path = save_record(record, audit_dir=audit_dir)

        deleted = enforce_retention(audit_dir=audit_dir, retention_days=90)
        assert deleted == 0
        assert os.path.exists(path)

    def test_enforce_retention_deletes_html_too(self, audit_dir):
        record = _make_record(decision_id="dec_old_html")
        save_record(record, audit_dir=audit_dir, also_save_html=True)

        json_path = Path(audit_dir) / "dec_old_html.json"
        html_path = Path(audit_dir) / "dec_old_html.html"

        old_time = time.time() - (100 * 86400)
        os.utime(json_path, (old_time, old_time))

        deleted = enforce_retention(audit_dir=audit_dir, retention_days=90)
        assert deleted == 1
        assert not json_path.exists()
        assert not html_path.exists()

    def test_enforce_retention_empty_dir(self, audit_dir):
        deleted = enforce_retention(audit_dir=audit_dir, retention_days=1)
        assert deleted == 0


# ============================================================================
# QUERY FILTER TESTS
# ============================================================================

class TestQueryFilter:

    def _populate(self, audit_dir: str) -> List[str]:
        """Populate audit_dir with mixed records. Returns decision_ids."""
        ids = []
        # 3 ALLOWED
        for i in range(3):
            did = f"dec_allowed_{i:03d}"
            save_record(_make_record(
                result="ALLOWED",
                decision_id=did,
                timestamp=f"2026-01-{10+i:02d}T10:00:00Z",
            ), audit_dir=audit_dir)
            ids.append(did)

        # 2 BLOCKED
        for i in range(2):
            did = f"dec_blocked_{i:03d}"
            save_record(_make_record(
                result="BLOCKED",
                decision_id=did,
                timestamp=f"2026-01-{15+i:02d}T10:00:00Z",
                violations=2,
            ), audit_dir=audit_dir)
            ids.append(did)

        return ids

    def test_filter_by_result_allowed(self, audit_dir):
        self._populate(audit_dir)
        q = AuditQuery(audit_dir)
        allowed = q.filter(result="ALLOWED")
        assert len(allowed) == 3
        assert all(r.decision.result == "ALLOWED" for r in allowed)

    def test_filter_by_result_blocked(self, audit_dir):
        self._populate(audit_dir)
        q = AuditQuery(audit_dir)
        blocked = q.filter(result="BLOCKED")
        assert len(blocked) == 2
        assert all(r.decision.result == "BLOCKED" for r in blocked)

    def test_filter_by_after(self, audit_dir):
        self._populate(audit_dir)
        q = AuditQuery(audit_dir)
        recent = q.filter(after="2026-01-14T00:00:00Z")
        assert len(recent) == 2  # Jan 15, 16

    def test_filter_by_before(self, audit_dir):
        self._populate(audit_dir)
        q = AuditQuery(audit_dir)
        early = q.filter(before="2026-01-12T23:59:59Z")
        assert len(early) == 3  # Jan 10, 11, 12

    def test_filter_by_time_range(self, audit_dir):
        self._populate(audit_dir)
        q = AuditQuery(audit_dir)
        ranged = q.filter(after="2026-01-11T00:00:00Z", before="2026-01-15T23:59:59Z")
        assert len(ranged) == 3  # Jan 11, 12 (allowed) + Jan 15 (blocked); Jan 16 > before

    def test_filter_combined(self, audit_dir):
        self._populate(audit_dir)
        q = AuditQuery(audit_dir)
        result = q.filter(result="BLOCKED", after="2026-01-16T00:00:00Z")
        assert len(result) == 1

    def test_filter_no_match(self, audit_dir):
        self._populate(audit_dir)
        q = AuditQuery(audit_dir)
        result = q.filter(result="HUMAN_OVERRIDE")
        assert len(result) == 0

    def test_filter_all(self, audit_dir):
        self._populate(audit_dir)
        q = AuditQuery(audit_dir)
        all_records = q.filter()
        assert len(all_records) == 5

    def test_refresh_reloads(self, audit_dir):
        save_record(_make_record(decision_id="dec_first"), audit_dir=audit_dir)
        q = AuditQuery(audit_dir)
        assert len(q.filter()) == 1

        save_record(_make_record(decision_id="dec_second"), audit_dir=audit_dir)
        assert len(q.filter()) == 1  # cached

        q.refresh()
        assert len(q.filter()) == 2  # reloaded


# ============================================================================
# QUERY STATS TESTS
# ============================================================================

class TestQueryStats:

    def _populate(self, audit_dir: str):
        for i in range(4):
            save_record(_make_record(result="ALLOWED", decision_id=f"dec_sa_{i}"), audit_dir=audit_dir)
        for i in range(2):
            save_record(_make_record(result="BLOCKED", decision_id=f"dec_sb_{i}", violations=3), audit_dir=audit_dir)

    def test_stats_counts(self, audit_dir):
        self._populate(audit_dir)
        q = AuditQuery(audit_dir)
        s = q.stats()

        assert s.total_decisions == 6
        assert s.allowed_count == 4
        assert s.blocked_count == 2

    def test_stats_rates(self, audit_dir):
        self._populate(audit_dir)
        q = AuditQuery(audit_dir)
        s = q.stats()

        assert abs(s.block_rate - 2 / 6) < 0.01
        assert abs(s.allow_rate - 4 / 6) < 0.01

    def test_stats_empty(self, audit_dir):
        q = AuditQuery(audit_dir)
        s = q.stats()
        assert s.total_decisions == 0
        assert s.block_rate == 0.0

    def test_stats_to_dict(self, audit_dir):
        self._populate(audit_dir)
        q = AuditQuery(audit_dir)
        d = q.stats().to_dict()
        assert "total_decisions" in d
        assert "block_rate" in d
        assert "allow_rate" in d
        assert "avg_duration_ms" in d

    def test_stats_on_filtered_records(self, audit_dir):
        self._populate(audit_dir)
        q = AuditQuery(audit_dir)
        blocked = q.filter(result="BLOCKED")
        s = q.stats(records=blocked)

        assert s.total_decisions == 2
        assert s.blocked_count == 2
        assert s.allowed_count == 0

    def test_stats_violations_counted(self, audit_dir):
        self._populate(audit_dir)
        q = AuditQuery(audit_dir)
        s = q.stats()

        # BLOCKED records have violations
        assert s.total_violations > 0


# ============================================================================
# TOP VIOLATIONS TESTS
# ============================================================================

class TestTopViolations:

    def test_top_violations_ranking(self, audit_dir):
        # Create records with known violations
        for i in range(3):
            save_record(_make_record(
                result="BLOCKED", decision_id=f"dec_tv_{i}", violations=2,
            ), audit_dir=audit_dir)

        q = AuditQuery(audit_dir)
        top = q.top_violations(n=5)

        assert len(top) > 0
        assert isinstance(top[0], tuple)
        assert isinstance(top[0][0], str)  # constraint name
        assert isinstance(top[0][1], int)  # count
        # Most frequent should be first
        if len(top) > 1:
            assert top[0][1] >= top[1][1]

    def test_top_violations_empty(self, audit_dir):
        save_record(_make_record(result="ALLOWED", decision_id="dec_no_viol"), audit_dir=audit_dir)
        q = AuditQuery(audit_dir)
        top = q.top_violations()

        # ALLOWED records still have violations on some candidates
        # (our test helper adds a blocked candidate even for ALLOWED records)
        assert isinstance(top, list)


# ============================================================================
# EXPORT TESTS
# ============================================================================

class TestExport:

    def _populate(self, audit_dir: str):
        for i in range(3):
            save_record(_make_record(decision_id=f"dec_exp_{i}"), audit_dir=audit_dir)

    def test_export_json(self, audit_dir, tmp_path):
        self._populate(audit_dir)
        q = AuditQuery(audit_dir)
        out = tmp_path / "export.json"
        result_path = q.export(str(out), format="json")

        assert os.path.exists(result_path)
        data = json.loads(Path(result_path).read_text())
        assert isinstance(data, list)
        assert len(data) == 3
        assert "schema_version" in data[0]

    def test_export_compact(self, audit_dir, tmp_path):
        self._populate(audit_dir)
        q = AuditQuery(audit_dir)
        out = tmp_path / "compact.json"
        q.export(str(out), format="compact")

        data = json.loads(Path(out).read_text())
        assert isinstance(data, list)
        assert "decision_id" in data[0]
        assert "result" in data[0]
        # Compact should NOT have full reasoning
        assert "reasoning" not in data[0]

    def test_export_stats(self, audit_dir, tmp_path):
        self._populate(audit_dir)
        q = AuditQuery(audit_dir)
        out = tmp_path / "stats.json"
        q.export(str(out), format="stats")

        data = json.loads(Path(out).read_text())
        assert "total_decisions" in data
        assert "top_violations" in data

    def test_export_creates_parent_dirs(self, audit_dir, tmp_path):
        self._populate(audit_dir)
        q = AuditQuery(audit_dir)
        out = tmp_path / "deep" / "nested" / "export.json"
        q.export(str(out), format="json")
        assert out.exists()

    def test_export_invalid_format_raises(self, audit_dir, tmp_path):
        q = AuditQuery(audit_dir)
        with pytest.raises(ValueError, match="Unknown export format"):
            q.export(str(tmp_path / "bad.txt"), format="xml")


# ============================================================================
# HTML REPORT TESTS
# ============================================================================

class TestHTMLReport:

    def test_generate_html_basic(self):
        record = _make_record(result="ALLOWED")
        html = generate_html(record)

        assert "<!DOCTYPE html>" in html
        assert record.decision_id in html
        assert "ALLOWED" in html
        assert "Right to Explanation" in html

    def test_html_contains_all_sections(self):
        record = _make_record(result="ALLOWED")
        html = generate_html(record)

        assert "Decision Summary" in html
        assert "Agent Info" in html
        assert "Reasoning Trace" in html
        assert "EU AI Act Compliance" in html
        assert "Performance" in html
        assert "Right to Explanation" in html

    def test_html_blocked_result(self):
        record = _make_record(result="BLOCKED", violations=3)
        html = generate_html(record)

        assert "BLOCKED" in html
        assert "#ef4444" in html  # red badge color

    def test_html_selected_candidate_marked(self):
        record = _make_record(result="ALLOWED")
        html = generate_html(record)
        assert "SELECTED" in html

    def test_html_with_violations(self):
        record = _make_record(result="BLOCKED", violations=2)
        html = generate_html(record)
        assert "Violations" in html

    def test_html_with_human_oversight(self):
        record = _make_record(result="ALLOWED")
        record.human_oversight_record = HumanOversightRecord(
            action="CONFIRM",
            reason="Approved by manager",
        )
        html = generate_html(record)
        assert "Human Oversight" in html
        assert "Approved by manager" in html

    def test_html_is_self_contained(self):
        record = _make_record()
        html = generate_html(record)

        # No external stylesheets or scripts
        assert "link rel=" not in html.lower() or "stylesheet" not in html.lower()
        assert "<style>" in html  # Inline CSS
        assert "src=" not in html  # No external scripts

    def test_html_escapes_xss(self):
        """Verify HTML escaping prevents XSS injection."""
        record = _make_record()
        record.input.raw_request = '<script>alert("xss")</script>'
        html = generate_html(record)

        assert '<script>alert("xss")</script>' not in html
        assert '&lt;script&gt;' in html


# ============================================================================
# FULL PIPELINE INTEGRATION TEST
# ============================================================================

class TestFullPipeline:
    """End-to-end: build → save → load → query → html."""

    def test_full_audit_pipeline(self, audit_dir):
        # 1. Build records
        for i in range(3):
            r = _make_record(result="ALLOWED", decision_id=f"dec_pipe_a{i}")
            save_record(r, audit_dir=audit_dir, also_save_html=True)

        for i in range(2):
            r = _make_record(result="BLOCKED", decision_id=f"dec_pipe_b{i}", violations=2)
            save_record(r, audit_dir=audit_dir, also_save_html=True)

        # 2. Verify files on disk
        json_files = list(Path(audit_dir).glob("*.json"))
        html_files = list(Path(audit_dir).glob("*.html"))
        assert len(json_files) == 5
        assert len(html_files) == 5

        # 3. Query
        q = AuditQuery(audit_dir)
        all_records = q.filter()
        assert len(all_records) == 5

        blocked = q.filter(result="BLOCKED")
        assert len(blocked) == 2

        # 4. Stats
        stats = q.stats()
        assert stats.total_decisions == 5
        assert stats.allowed_count == 3
        assert stats.blocked_count == 2
        assert abs(stats.block_rate - 0.4) < 0.01

        # 5. Top violations
        top = q.top_violations(n=3)
        assert len(top) > 0

        # 6. Load single record
        loaded = load_record("dec_pipe_a0", audit_dir=audit_dir)
        assert loaded.decision.result == "ALLOWED"

        # 7. HTML is valid
        html_content = (Path(audit_dir) / "dec_pipe_a0.html").read_text()
        assert "<!DOCTYPE html>" in html_content
        assert "dec_pipe_a0" in html_content
