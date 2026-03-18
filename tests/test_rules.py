"""
Tests for chimera_runtime.rules — YAML Rule Engine

Tests the lightweight policy evaluation engine that works without CSL-Core.
"""

import pytest
import yaml
from pathlib import Path

from chimera_runtime.rules import (
    YAMLRuleEngine,
    RuleEngineError,
    RuleParseError,
    _safe_eval,
    Rule,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def governance_yaml(tmp_path):
    """Create a governance YAML policy file."""
    content = {
        "domain": "GovernanceGuard",
        "variables": {
            "amount": "0..1000000",
            "role": "{ANALYST, MANAGER, DIRECTOR}",
        },
        "rules": [
            {
                "name": "analyst_no_spend",
                "when": "role == 'ANALYST' and amount > 0",
                "then": "BLOCK",
                "message": "Analysts cannot approve any spend",
            },
            {
                "name": "manager_limit",
                "when": "role == 'MANAGER' and amount > 250000",
                "then": "BLOCK",
                "message": "Managers limited to $250,000",
            },
            {
                "name": "absolute_ceiling",
                "when": "amount > 1000000",
                "then": "BLOCK",
                "message": "Absolute ceiling: $1,000,000",
            },
        ],
    }
    p = tmp_path / "governance.yaml"
    p.write_text(yaml.dump(content), encoding="utf-8")
    return str(p)


@pytest.fixture
def simple_yaml(tmp_path):
    content = {
        "domain": "SimpleGuard",
        "rules": [
            {
                "name": "high_score",
                "when": "score > 80",
                "then": "BLOCK",
                "message": "Score too high",
            },
        ],
    }
    p = tmp_path / "simple.yaml"
    p.write_text(yaml.dump(content), encoding="utf-8")
    return str(p)


# ============================================================================
# SAFE EVAL TESTS
# ============================================================================

class TestSafeEval:

    def test_simple_comparison(self):
        assert _safe_eval("amount > 100", {"amount": 200}) is True
        assert _safe_eval("amount > 100", {"amount": 50}) is False

    def test_equality(self):
        assert _safe_eval("role == 'ADMIN'", {"role": "ADMIN"}) is True
        assert _safe_eval("role == 'ADMIN'", {"role": "USER"}) is False

    def test_not_equal(self):
        assert _safe_eval("role != 'ADMIN'", {"role": "USER"}) is True

    def test_and_operator(self):
        ctx = {"role": "MANAGER", "amount": 300000}
        assert _safe_eval("role == 'MANAGER' and amount > 250000", ctx) is True
        assert _safe_eval("role == 'MANAGER' and amount > 500000", ctx) is False

    def test_or_operator(self):
        ctx = {"role": "CEO", "amount": 100}
        assert _safe_eval("role == 'CEO' or amount > 1000", ctx) is True
        assert _safe_eval("role == 'ANALYST' or amount > 1000", ctx) is False

    def test_not_operator(self):
        assert _safe_eval("not role == 'ADMIN'", {"role": "USER"}) is True

    def test_in_operator(self):
        assert _safe_eval("role in ('ADMIN', 'CEO')", {"role": "CEO"}) is True
        assert _safe_eval("role in ('ADMIN', 'CEO')", {"role": "USER"}) is False

    def test_numeric_comparisons(self):
        ctx = {"score": 75}
        assert _safe_eval("score >= 70", ctx) is True
        assert _safe_eval("score <= 80", ctx) is True
        assert _safe_eval("score < 75", ctx) is False

    def test_unknown_variable_raises(self):
        with pytest.raises(RuleParseError, match="Unknown variable"):
            _safe_eval("unknown > 0", {})

    def test_invalid_syntax_raises(self):
        with pytest.raises(RuleParseError, match="Invalid expression"):
            _safe_eval("!@#$%", {})

    def test_boolean_literals(self):
        assert _safe_eval("True", {}) is True
        assert _safe_eval("False", {}) is False


# ============================================================================
# RULE TESTS
# ============================================================================

class TestRule:

    def test_rule_triggers(self):
        rule = Rule("test", "amount > 100", "BLOCK", "Over limit")
        assert rule.evaluate({"amount": 200}) == "Over limit"

    def test_rule_passes(self):
        rule = Rule("test", "amount > 100", "BLOCK", "Over limit")
        assert rule.evaluate({"amount": 50}) is None

    def test_rule_with_default_message(self):
        rule = Rule("my_rule", "score > 90", "BLOCK")
        result = rule.evaluate({"score": 95})
        assert "my_rule" in result


# ============================================================================
# YAML RULE ENGINE TESTS
# ============================================================================

class TestYAMLRuleEngine:

    def test_load(self, governance_yaml):
        engine = YAMLRuleEngine(governance_yaml)
        assert engine.domain_name == "GovernanceGuard"
        assert engine.constraint_count == 3
        assert "analyst_no_spend" in engine.constraint_names

    def test_evaluate_allowed(self, governance_yaml):
        engine = YAMLRuleEngine(governance_yaml)
        result = engine.evaluate({"amount": 50000, "role": "MANAGER"})
        assert result.result == "ALLOWED"
        assert len(result.violations) == 0

    def test_evaluate_blocked(self, governance_yaml):
        engine = YAMLRuleEngine(governance_yaml)
        result = engine.evaluate({"amount": 300000, "role": "MANAGER"})
        assert result.result == "BLOCKED"
        assert len(result.violations) == 1
        assert result.violations[0].constraint == "manager_limit"

    def test_evaluate_multiple_violations(self, governance_yaml):
        engine = YAMLRuleEngine(governance_yaml)
        result = engine.evaluate({"amount": 1500000, "role": "ANALYST"})
        assert result.result == "BLOCKED"
        assert len(result.violations) >= 2

    def test_evaluate_analyst_blocked(self, governance_yaml):
        engine = YAMLRuleEngine(governance_yaml)
        result = engine.evaluate({"amount": 100, "role": "ANALYST"})
        assert result.result == "BLOCKED"
        assert result.violations[0].constraint == "analyst_no_spend"

    def test_dry_run(self, governance_yaml):
        engine = YAMLRuleEngine(governance_yaml, dry_run=True)
        result = engine.evaluate({"amount": 300000, "role": "MANAGER"})
        assert result.result == "ALLOWED"  # Dry run never blocks

    def test_hash(self, governance_yaml):
        engine = YAMLRuleEngine(governance_yaml)
        assert engine.hash.startswith("sha256:")

    def test_variable_names(self, governance_yaml):
        engine = YAMLRuleEngine(governance_yaml)
        assert "amount" in engine.variable_names
        assert "role" in engine.variable_names

    def test_variable_domains(self, governance_yaml):
        engine = YAMLRuleEngine(governance_yaml)
        assert "0..1000000" in engine.variable_domains.get("amount", "")

    def test_metadata(self, governance_yaml):
        engine = YAMLRuleEngine(governance_yaml)
        meta = engine.metadata
        assert meta["engine"] == "yaml-rule-engine"
        assert meta["domain_name"] == "GovernanceGuard"

    def test_verify(self, governance_yaml):
        engine = YAMLRuleEngine(governance_yaml)
        ok, messages = engine.verify()
        assert ok is True
        assert len(messages) > 0

    def test_file_not_found(self, tmp_path):
        with pytest.raises(RuleEngineError, match="not found"):
            YAMLRuleEngine(str(tmp_path / "nonexistent.yaml"))

    def test_invalid_yaml(self, tmp_path):
        p = tmp_path / "bad.yaml"
        p.write_text(": invalid: yaml: {{", encoding="utf-8")
        with pytest.raises(RuleEngineError):
            YAMLRuleEngine(str(p))

    def test_missing_when(self, tmp_path):
        content = {"rules": [{"name": "bad", "then": "BLOCK"}]}
        p = tmp_path / "bad.yaml"
        p.write_text(yaml.dump(content), encoding="utf-8")
        with pytest.raises(RuleEngineError, match="missing 'when'"):
            YAMLRuleEngine(str(p))

    def test_hot_reload(self, tmp_path):
        content = {
            "rules": [{"name": "r1", "when": "x > 10", "then": "BLOCK"}],
        }
        p = tmp_path / "reload.yaml"
        p.write_text(yaml.dump(content), encoding="utf-8")

        engine = YAMLRuleEngine(str(p))
        assert engine.constraint_count == 1

        # Modify file
        import time
        time.sleep(0.01)
        content["rules"].append({"name": "r2", "when": "x > 20", "then": "BLOCK"})
        p.write_text(yaml.dump(content), encoding="utf-8")

        reloaded = engine.reload()
        assert reloaded is True
        assert engine.constraint_count == 2

    def test_hot_reload_no_change(self, simple_yaml):
        engine = YAMLRuleEngine(simple_yaml)
        assert engine.reload() is False

    def test_loaded_property(self, governance_yaml):
        engine = YAMLRuleEngine(governance_yaml)
        assert engine.loaded is True

    def test_policy_path_property(self, governance_yaml):
        engine = YAMLRuleEngine(governance_yaml)
        assert governance_yaml in engine.policy_path

    def test_duration_tracked(self, governance_yaml):
        engine = YAMLRuleEngine(governance_yaml)
        result = engine.evaluate({"amount": 100, "role": "MANAGER"})
        assert result.duration_ms >= 0


# ============================================================================
# POLICY MANAGER WITH YAML BACKEND
# ============================================================================

class TestPolicyManagerYAML:
    """Test PolicyManager when using YAML backend."""

    def test_load_yaml(self, governance_yaml):
        from chimera_runtime.policy import PolicyManager
        pm = PolicyManager(governance_yaml)
        assert pm.backend == "yaml-rule-engine"
        assert pm.domain_name == "GovernanceGuard"

    def test_evaluate_yaml(self, governance_yaml):
        from chimera_runtime.policy import PolicyManager
        pm = PolicyManager(governance_yaml)
        result = pm.evaluate({"amount": 50000, "role": "MANAGER"})
        assert result.result == "ALLOWED"

    def test_evaluate_yaml_blocked(self, governance_yaml):
        from chimera_runtime.policy import PolicyManager
        pm = PolicyManager(governance_yaml)
        result = pm.evaluate({"amount": 300000, "role": "MANAGER"})
        assert result.result == "BLOCKED"

    def test_verify_yaml(self, governance_yaml):
        from chimera_runtime.policy import PolicyManager
        pm = PolicyManager(governance_yaml)
        ok, msgs = pm.verify()
        assert ok is True

    def test_constraint_names_yaml(self, governance_yaml):
        from chimera_runtime.policy import PolicyManager
        pm = PolicyManager(governance_yaml)
        assert "analyst_no_spend" in pm.constraint_names

    def test_unsupported_extension(self, tmp_path):
        from chimera_runtime.policy import PolicyManager, PolicyError
        p = tmp_path / "bad.txt"
        p.write_text("hello", encoding="utf-8")
        with pytest.raises(PolicyError, match="Unsupported"):
            PolicyManager(str(p))
