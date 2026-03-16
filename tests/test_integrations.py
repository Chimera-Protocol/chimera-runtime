"""
Tests for chimera_compliance.integrations

Tests the core ComplianceGuard and integration base classes.
Framework-specific tests (LangChain, etc.) are skipped if the framework is not installed.
"""

import pytest
import yaml
from pathlib import Path

from chimera_compliance.integrations import ComplianceGuard
from chimera_compliance.integrations.base import ComplianceError, ActionGuardMixin
from chimera_compliance.integrations.autogen import guard_function_call


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def policy_yaml(tmp_path):
    """Create a simple YAML policy for testing integrations."""
    content = {
        "domain": "IntegrationTest",
        "rules": [
            {
                "name": "amount_limit",
                "when": "amount > 10000",
                "then": "BLOCK",
                "message": "Amount exceeds $10,000 limit",
            },
            {
                "name": "admin_required",
                "when": "role == 'USER' and amount > 1000",
                "then": "BLOCK",
                "message": "Users limited to $1,000",
            },
        ],
    }
    p = tmp_path / "test_policy.yaml"
    p.write_text(yaml.dump(content), encoding="utf-8")
    return str(p)


@pytest.fixture
def audit_dir(tmp_path):
    d = tmp_path / "audit_logs"
    d.mkdir()
    return str(d)


# ============================================================================
# COMPLIANCE GUARD TESTS
# ============================================================================

class TestComplianceGuard:

    def test_check_allowed(self, policy_yaml, audit_dir):
        guard = ComplianceGuard(policy=policy_yaml, audit_dir=audit_dir)
        result = guard.check("transfer", {"amount": 500, "role": "USER"})
        assert result.result == "ALLOWED"

    def test_check_blocked(self, policy_yaml, audit_dir):
        guard = ComplianceGuard(policy=policy_yaml, audit_dir=audit_dir)
        result = guard.check("transfer", {"amount": 5000, "role": "USER"})
        assert result.result == "BLOCKED"
        assert len(result.violations) > 0

    def test_check_creates_audit_record(self, policy_yaml, audit_dir):
        guard = ComplianceGuard(policy=policy_yaml, audit_dir=audit_dir)
        guard.check("transfer", {"amount": 500, "role": "ADMIN"})

        audit_files = list(Path(audit_dir).glob("*.json"))
        assert len(audit_files) == 1

    def test_check_with_context(self, policy_yaml, audit_dir):
        guard = ComplianceGuard(policy=policy_yaml, audit_dir=audit_dir)
        result = guard.check(
            "transfer",
            {"amount": 500, "role": "ADMIN"},
            context={"source": "test"},
        )
        assert result.result == "ALLOWED"

    def test_policy_manager_accessible(self, policy_yaml, audit_dir):
        guard = ComplianceGuard(policy=policy_yaml, audit_dir=audit_dir)
        assert guard.policy_manager is not None
        assert guard.policy_manager.domain_name == "IntegrationTest"


# ============================================================================
# COMPLIANCE ERROR TESTS
# ============================================================================

class TestComplianceError:

    def test_error_message(self, policy_yaml, audit_dir):
        guard = ComplianceGuard(policy=policy_yaml, audit_dir=audit_dir)
        result = guard.check("transfer", {"amount": 5000, "role": "USER"})

        error = ComplianceError(result)
        assert "BLOCKED" in str(error)
        assert result.violations[0].explanation in str(error)

    def test_error_has_evaluation(self, policy_yaml, audit_dir):
        guard = ComplianceGuard(policy=policy_yaml, audit_dir=audit_dir)
        result = guard.check("transfer", {"amount": 5000, "role": "USER"})
        error = ComplianceError(result)
        assert error.evaluation is result


# ============================================================================
# ACTION GUARD MIXIN TESTS
# ============================================================================

class TestActionGuardMixin:

    def test_mixin_raise_on_block(self, policy_yaml, audit_dir):
        class TestGuard(ActionGuardMixin):
            def __init__(self):
                self._guard = ComplianceGuard(
                    policy=policy_yaml, audit_dir=audit_dir
                )

        g = TestGuard()
        with pytest.raises(ComplianceError):
            g._check_compliance("test", {"amount": 50000, "role": "USER"})

    def test_mixin_return_on_block(self, policy_yaml, audit_dir):
        class TestGuard(ActionGuardMixin):
            def __init__(self):
                self._guard = ComplianceGuard(
                    policy=policy_yaml, audit_dir=audit_dir
                )

        g = TestGuard()
        result = g._check_compliance(
            "test", {"amount": 50000, "role": "USER"}, on_block="return"
        )
        assert result.result == "BLOCKED"

    def test_mixin_allowed(self, policy_yaml, audit_dir):
        class TestGuard(ActionGuardMixin):
            def __init__(self):
                self._guard = ComplianceGuard(
                    policy=policy_yaml, audit_dir=audit_dir
                )

        g = TestGuard()
        result = g._check_compliance("test", {"amount": 500, "role": "ADMIN"})
        assert result.result == "ALLOWED"


# ============================================================================
# AUTOGEN DECORATOR TESTS (no autogen import needed)
# ============================================================================

class TestGuardFunctionCall:

    def test_allowed_function_call(self, policy_yaml):
        @guard_function_call(policy=policy_yaml)
        def approve_spend(amount: int, role: str) -> str:
            return f"Approved ${amount}"

        result = approve_spend(amount=500, role="ADMIN")
        assert result == "Approved $500"

    def test_blocked_function_call(self, policy_yaml):
        @guard_function_call(policy=policy_yaml)
        def approve_spend(amount: int, role: str) -> str:
            return f"Approved ${amount}"

        with pytest.raises(ComplianceError):
            approve_spend(amount=50000, role="USER")

    def test_param_mapping(self, policy_yaml):
        @guard_function_call(
            policy=policy_yaml,
            param_mapping={"amt": "amount", "user_role": "role"},
        )
        def transfer(amt: int, user_role: str) -> str:
            return f"Transferred ${amt}"

        result = transfer(amt=500, user_role="ADMIN")
        assert result == "Transferred $500"

    def test_param_mapping_blocked(self, policy_yaml):
        @guard_function_call(
            policy=policy_yaml,
            param_mapping={"amt": "amount", "user_role": "role"},
        )
        def transfer(amt: int, user_role: str) -> str:
            return f"Transferred ${amt}"

        with pytest.raises(ComplianceError):
            transfer(amt=50000, user_role="USER")
