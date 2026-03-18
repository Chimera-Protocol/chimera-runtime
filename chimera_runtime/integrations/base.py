"""
chimera-runtime — Base Integration

Shared logic for all agent framework integrations.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from ..models import PolicyEvaluation


class ComplianceError(Exception):
    """Raised when an action is blocked by the compliance guard."""

    def __init__(self, evaluation: PolicyEvaluation):
        self.evaluation = evaluation
        violations = "; ".join(v.explanation for v in evaluation.violations)
        super().__init__(f"Action BLOCKED: {violations}")


class ActionGuardMixin:
    """
    Mixin for tool/action wrappers that need compliance checking.

    Subclasses must set self._guard (ComplianceGuard) and can call
    _check_compliance() before executing any action.
    """

    def _check_compliance(
        self,
        action_name: str,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        on_block: str = "raise",
    ) -> PolicyEvaluation:
        """
        Check if an action is allowed by the compliance policy.

        Args:
            action_name: Name of the tool/action
            parameters: Parameters to check
            context: Optional context
            on_block: What to do if blocked — "raise" (default) or "return"

        Returns:
            PolicyEvaluation

        Raises:
            ComplianceError: If blocked and on_block="raise"
        """
        evaluation = self._guard.check(action_name, parameters, context)

        if evaluation.result == "BLOCKED" and on_block == "raise":
            raise ComplianceError(evaluation)

        return evaluation
