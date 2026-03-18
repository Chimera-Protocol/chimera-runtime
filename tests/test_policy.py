"""
Tests for chimera_runtime.policy

Validates:
  - Policy loading from .csl files via csl-core
  - Evaluation returns correct ALLOWED/BLOCKED results
  - Violations are correctly mapped to chimera-runtime Violation objects
  - SHA256 hash computation and tamper detection
  - Hot-reload detects file changes
  - Metadata extraction (domain name, constraints, variables)
  - Error handling for missing/invalid policies
"""

import tempfile
from pathlib import Path

import pytest

from chimera_runtime.policy import (
    PolicyManager,
    PolicyError,
    PolicyFileNotFoundError,
)
from chimera_runtime.models import PolicyEvaluation, Violation


# ============================================================================
# FIXTURES
# ============================================================================

GOVERNANCE_POLICY = """\
CONFIG {
  ENFORCEMENT_MODE: BLOCK
  CHECK_LOGICAL_CONSISTENCY: TRUE
}

DOMAIN GovernanceGuard {
  VARIABLES {
    amount: 0..1000000
    role: {"ANALYST", "MANAGER", "DIRECTOR", "VP", "CEO"}
    channel: {"DIGITAL", "TV", "PRINT", "RADIO", "ALL"}
    is_weekend: {"YES", "NO"}
    urgency: {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
  }

  STATE_CONSTRAINT analyst_no_spend {
    WHEN role == "ANALYST"
    THEN amount <= 0
  }

  STATE_CONSTRAINT manager_approval_limit {
    WHEN role == "MANAGER"
    THEN amount <= 250000
  }

  STATE_CONSTRAINT single_channel_cap {
    WHEN channel != "ALL"
    THEN amount <= 300000
  }

  STATE_CONSTRAINT weekend_freeze {
    WHEN is_weekend == "YES"
    THEN urgency == "CRITICAL"
  }

  STATE_CONSTRAINT absolute_ceiling {
    ALWAYS True
    THEN amount <= 1000000
  }
}
"""

SIMPLE_POLICY = """\
CONFIG {
  ENFORCEMENT_MODE: BLOCK
  CHECK_LOGICAL_CONSISTENCY: TRUE
}

DOMAIN SimpleGuard {
  VARIABLES {
    score: 0..100
    allowed: {"YES", "NO"}
  }

  STATE_CONSTRAINT high_score_block {
    WHEN score > 80
    THEN allowed == "YES"
  }
}
"""


@pytest.fixture
def tmp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


@pytest.fixture
def governance_csl(tmp_dir):
    path = tmp_dir / "governance.csl"
    path.write_text(GOVERNANCE_POLICY)
    return path


@pytest.fixture
def simple_csl(tmp_dir):
    path = tmp_dir / "simple.csl"
    path.write_text(SIMPLE_POLICY)
    return path


@pytest.fixture
def governance_pm(governance_csl):
    return PolicyManager(str(governance_csl))


@pytest.fixture
def simple_pm(simple_csl):
    return PolicyManager(str(simple_csl))


# ============================================================================
# LOADING TESTS
# ============================================================================

class TestPolicyLoading:
    def test_load_valid_policy(self, governance_csl):
        pm = PolicyManager(str(governance_csl))
        assert pm.loaded is True

    def test_load_missing_file_raises(self, tmp_dir):
        with pytest.raises(PolicyFileNotFoundError):
            PolicyManager(str(tmp_dir / "nonexistent.csl"))

    def test_load_invalid_policy_raises(self, tmp_dir):
        path = tmp_dir / "bad.csl"
        path.write_text("THIS IS NOT VALID CSL")
        with pytest.raises(PolicyError):
            PolicyManager(str(path))


# ============================================================================
# EVALUATION TESTS
# ============================================================================

class TestPolicyEvaluation:
    def test_allowed_within_limits(self, governance_pm):
        result = governance_pm.evaluate({
            "amount": 200000,
            "role": "MANAGER",
            "channel": "DIGITAL",
            "is_weekend": "NO",
            "urgency": "MEDIUM",
        })
        assert isinstance(result, PolicyEvaluation)
        assert result.result == "ALLOWED"
        assert len(result.violations) == 0
        assert result.duration_ms > 0

    def test_blocked_exceeds_limit(self, governance_pm):
        result = governance_pm.evaluate({
            "amount": 300000,
            "role": "MANAGER",
            "channel": "DIGITAL",
            "is_weekend": "NO",
            "urgency": "MEDIUM",
        })
        assert result.result == "BLOCKED"
        assert len(result.violations) > 0

    def test_blocked_analyst_any_spend(self, governance_pm):
        result = governance_pm.evaluate({
            "amount": 100,
            "role": "ANALYST",
            "channel": "DIGITAL",
            "is_weekend": "NO",
            "urgency": "LOW",
        })
        assert result.result == "BLOCKED"

    def test_blocked_weekend_non_critical(self, governance_pm):
        result = governance_pm.evaluate({
            "amount": 100000,
            "role": "DIRECTOR",
            "channel": "ALL",
            "is_weekend": "YES",
            "urgency": "MEDIUM",
        })
        assert result.result == "BLOCKED"

    def test_allowed_weekend_critical(self, governance_pm):
        result = governance_pm.evaluate({
            "amount": 100000,
            "role": "DIRECTOR",
            "channel": "ALL",
            "is_weekend": "YES",
            "urgency": "CRITICAL",
        })
        assert result.result == "ALLOWED"

    def test_blocked_exceeds_ceiling(self, governance_pm):
        result = governance_pm.evaluate({
            "amount": 1500000,
            "role": "CEO",
            "channel": "ALL",
            "is_weekend": "NO",
            "urgency": "HIGH",
        })
        assert result.result == "BLOCKED"

    def test_simple_policy_allowed(self, simple_pm):
        result = simple_pm.evaluate({"score": 50, "allowed": "NO"})
        assert result.result == "ALLOWED"

    def test_simple_policy_blocked(self, simple_pm):
        result = simple_pm.evaluate({"score": 90, "allowed": "NO"})
        assert result.result == "BLOCKED"

    def test_simple_policy_high_allowed(self, simple_pm):
        result = simple_pm.evaluate({"score": 90, "allowed": "YES"})
        assert result.result == "ALLOWED"


# ============================================================================
# POLICY EVALUATION RESULT FORMAT
# ============================================================================

class TestEvaluationFormat:
    def test_policy_file_in_result(self, governance_pm, governance_csl):
        result = governance_pm.evaluate({
            "amount": 200000, "role": "MANAGER",
            "channel": "ALL", "is_weekend": "NO", "urgency": "LOW",
        })
        assert str(governance_csl.resolve()) in result.policy_file

    def test_policy_hash_format(self, governance_pm):
        result = governance_pm.evaluate({
            "amount": 200000, "role": "MANAGER",
            "channel": "ALL", "is_weekend": "NO", "urgency": "LOW",
        })
        assert result.policy_hash.startswith("sha256:")
        assert len(result.policy_hash) == len("sha256:") + 64

    def test_violations_are_violation_objects(self, governance_pm):
        result = governance_pm.evaluate({
            "amount": 300000, "role": "MANAGER",
            "channel": "DIGITAL", "is_weekend": "NO", "urgency": "MEDIUM",
        })
        assert result.result == "BLOCKED"
        for v in result.violations:
            assert isinstance(v, Violation)
            assert isinstance(v.constraint, str)
            assert isinstance(v.rule, str)
            assert isinstance(v.trigger_values, dict)

    def test_serialization_roundtrip(self, governance_pm):
        result = governance_pm.evaluate({
            "amount": 300000, "role": "MANAGER",
            "channel": "DIGITAL", "is_weekend": "NO", "urgency": "MEDIUM",
        })
        d = result.to_dict()
        restored = PolicyEvaluation.from_dict(d)
        assert restored.result == result.result
        assert restored.policy_hash == result.policy_hash
        assert len(restored.violations) == len(result.violations)


# ============================================================================
# HASH AND METADATA TESTS
# ============================================================================

class TestPolicyMetadata:
    def test_hash_is_sha256(self, governance_pm):
        assert governance_pm.hash.startswith("sha256:")
        hex_part = governance_pm.hash.split(":")[1]
        assert len(hex_part) == 64

    def test_hash_changes_with_content(self, tmp_dir):
        path = tmp_dir / "test.csl"
        path.write_text(SIMPLE_POLICY)
        pm1 = PolicyManager(str(path))
        hash1 = pm1.hash

        path.write_text(GOVERNANCE_POLICY)
        pm2 = PolicyManager(str(path))
        hash2 = pm2.hash

        assert hash1 != hash2

    def test_domain_name(self, governance_pm):
        assert governance_pm.domain_name == "GovernanceGuard"

    def test_simple_domain_name(self, simple_pm):
        assert simple_pm.domain_name == "SimpleGuard"

    def test_metadata_dict(self, governance_pm):
        meta = governance_pm.metadata
        assert "policy_file" in meta
        assert "policy_hash" in meta
        assert "domain_name" in meta
        assert meta["domain_name"] == "GovernanceGuard"

    def test_policy_path_absolute(self, governance_pm, governance_csl):
        assert Path(governance_pm.policy_path).is_absolute()


# ============================================================================
# HOT-RELOAD TESTS
# ============================================================================

class TestHotReload:
    def test_reload_unchanged_returns_false(self, governance_pm):
        assert governance_pm.reload() is False

    def test_reload_changed_content_returns_true(self, governance_pm, tmp_dir):
        # Get the path and modify it
        path = Path(governance_pm.policy_path)
        original_hash = governance_pm.hash

        # Write different policy
        path.write_text(SIMPLE_POLICY)
        reloaded = governance_pm.reload()

        assert reloaded is True
        assert governance_pm.hash != original_hash
        assert governance_pm.domain_name == "SimpleGuard"

    def test_reload_deleted_file_raises(self, governance_pm):
        path = Path(governance_pm.policy_path)
        path.unlink()  # Delete the file
        with pytest.raises(PolicyFileNotFoundError):
            governance_pm.reload()

    def test_check_reload_swallows_errors(self, governance_pm):
        path = Path(governance_pm.policy_path)
        path.unlink()
        # Should not raise
        result = governance_pm.check_reload()
        assert result is False


# ============================================================================
# DRY RUN MODE
# ============================================================================

class TestDryRun:
    def test_dry_run_never_blocks(self, tmp_dir):
        path = tmp_dir / "simple.csl"
        path.write_text(SIMPLE_POLICY)
        pm = PolicyManager(str(path), dry_run=True)

        # This would normally be BLOCKED (score > 80, allowed != "YES")
        result = pm.evaluate({"score": 90, "allowed": "NO"})
        assert result.result == "ALLOWED"
