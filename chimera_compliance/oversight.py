"""
chimera-compliance — Human Oversight

EU AI Act Article 14 compliance: humans can confirm, override, or stop decisions.

Two modes:
  - Interactive: blocks on stdin for human confirmation (CLI/REPL use)
  - SDK/Callback: accepts a callable for programmatic confirmation

Usage:
    # Interactive mode (CLI)
    oversight = HumanOversight(mode="interactive")

    # SDK mode (programmatic)
    oversight = HumanOversight(mode="sdk", confirm_callback=my_callback)

    # Request confirmation before executing an allowed action
    approved = oversight.request_confirmation(candidate, evaluation)

    # Human override: change the decision
    record = oversight.apply_override(action="BLOCK", reason="Too risky for Q4")
"""

from __future__ import annotations

import sys
from typing import Any, Callable, Dict, Optional

from .models import (
    Candidate,
    PolicyEvaluation,
    HumanOversightRecord,
    utc_now_iso,
)


# ============================================================================
# ERRORS
# ============================================================================

class OversightError(Exception):
    """Raised when an oversight operation fails."""
    pass


class OversightTimeoutError(OversightError):
    """Raised when human confirmation times out."""
    pass


# ============================================================================
# TYPE ALIAS
# ============================================================================

# Callback signature: (candidate, evaluation) → bool
ConfirmCallback = Callable[[Candidate, Optional[PolicyEvaluation]], bool]


# ============================================================================
# HUMAN OVERSIGHT
# ============================================================================

class HumanOversight:
    """
    Human oversight controller for chimera-compliance.

    Provides Art. 14 compliance:
      - request_confirmation(): human must approve before action executes
      - apply_override(): human can change the decision
      - stop(): human can halt the agent entirely

    Modes:
      - "interactive": blocks on stdin, prints to stdout (for CLI/REPL)
      - "sdk": uses a callback function (for programmatic integration)
      - "auto": no human in the loop, always approves (for testing/batch)
    """

    def __init__(
        self,
        mode: str = "auto",
        confirm_callback: Optional[ConfirmCallback] = None,
    ):
        if mode not in ("interactive", "sdk", "auto"):
            raise OversightError(
                f"Unknown oversight mode: '{mode}'. "
                f"Must be 'interactive', 'sdk', or 'auto'."
            )

        self.mode = mode
        self._confirm_callback = confirm_callback

        if mode == "sdk" and confirm_callback is None:
            raise OversightError(
                "SDK mode requires a confirm_callback function."
            )

    # ========================================================================
    # CONFIRMATION
    # ========================================================================

    def request_confirmation(
        self,
        candidate: Candidate,
        evaluation: Optional[PolicyEvaluation] = None,
    ) -> bool:
        """
        Request human confirmation for an action.

        Returns True if the human approves, False if rejected.
        In 'auto' mode, always returns True.
        """
        if self.mode == "auto":
            return True

        if self.mode == "sdk":
            return self._confirm_callback(candidate, evaluation)

        # Interactive mode: stdin
        return self._interactive_confirm(candidate, evaluation)

    def _interactive_confirm(
        self,
        candidate: Candidate,
        evaluation: Optional[PolicyEvaluation] = None,
    ) -> bool:
        """Display decision details and ask for confirmation via stdin."""
        print("\n" + "=" * 60)
        print("  HUMAN OVERSIGHT — Confirmation Required")
        print("=" * 60)
        print(f"  Strategy:   {candidate.strategy}")
        print(f"  Confidence: {candidate.llm_confidence:.0%}")
        print(f"  Parameters: {candidate.parameters}")

        if evaluation:
            print(f"  Policy:     {evaluation.result}")
            if evaluation.violations:
                print(f"  Violations: {len(evaluation.violations)}")
                for v in evaluation.violations:
                    print(f"    - {v.constraint}: {v.explanation}")

        print(f"\n  Reasoning:  {candidate.llm_reasoning[:200]}")
        print("=" * 60)

        try:
            response = input("  Approve this action? [y/N]: ").strip().lower()
            return response in ("y", "yes")
        except (EOFError, KeyboardInterrupt):
            return False

    # ========================================================================
    # OVERRIDE
    # ========================================================================

    def apply_override(
        self,
        action: str,
        reason: str = "",
    ) -> HumanOversightRecord:
        """
        Create a human override record.

        Args:
            action: What the human decided — "CONFIRM", "OVERRIDE", "STOP"
            reason: Why the human made this choice

        Returns:
            HumanOversightRecord for inclusion in the audit trail
        """
        if action not in ("CONFIRM", "OVERRIDE", "STOP"):
            raise OversightError(
                f"Invalid override action: '{action}'. "
                f"Must be 'CONFIRM', 'OVERRIDE', or 'STOP'."
            )

        override_decision = ""
        if action == "OVERRIDE":
            override_decision = "HUMAN_OVERRIDE"

        return HumanOversightRecord(
            action=action,
            reason=reason,
            override_decision=override_decision,
            timestamp=utc_now_iso(),
        )

    # ========================================================================
    # INTERACTIVE OVERRIDE (for CLI)
    # ========================================================================

    def request_override_interactive(
        self,
        candidate: Candidate,
    ) -> Optional[HumanOversightRecord]:
        """
        In interactive mode, ask the human if they want to override.
        Returns None if no override, or a HumanOversightRecord if overridden.
        """
        if self.mode != "interactive":
            return None

        print("\n  All candidates were BLOCKED by policy.")
        print("  You can override this decision if needed.")

        try:
            response = input("  Override and allow? [y/N]: ").strip().lower()
            if response in ("y", "yes"):
                reason = input("  Reason for override: ").strip()
                return self.apply_override(action="OVERRIDE", reason=reason)
        except (EOFError, KeyboardInterrupt):
            pass

        return None
