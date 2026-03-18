"""
chimera-runtime — Agent Framework Integrations

Plug chimera-runtime into any AI agent framework:
  - LangChain: wrap_tools(), ChimeraCallbackHandler
  - LangGraph: compliance_node()
  - LlamaIndex: ChimeraToolSpec, ChimeraCallbackHandler
  - CrewAI: wrap_crew_tools()
  - AutoGen: ChimeraRuntimeAgent

Each integration is optional — install the framework you need:
    pip install chimera-runtime[langchain]
    pip install chimera-runtime[langgraph]
    pip install chimera-runtime[llamaindex]
    pip install chimera-runtime[crewai]
    pip install chimera-runtime[autogen]
"""

from __future__ import annotations

from typing import Dict, Any, List, Optional

from ..policy import PolicyManager, PolicyError
from ..models import PolicyEvaluation, Violation
from ..audit.recorder import build_audit_record
from ..audit.storage import save_record
from ..models import AgentInfo, InputInfo, Attempt, Candidate, AttemptOutcome


def _get_version() -> str:
    from .. import __version__
    return __version__


__all__ = [
    "ComplianceGuard",
]


class ComplianceGuard:
    """
    Core compliance guard shared by all integrations.

    Wraps policy evaluation + audit recording into a single call.
    Every integration uses this under the hood.
    """

    def __init__(
        self,
        policy: str,
        audit_dir: str = "./audit_logs",
        dry_run: bool = False,
        auto_verify: bool = True,
    ):
        self._policy_manager = PolicyManager(
            policy, auto_verify=auto_verify, dry_run=dry_run
        )
        self._audit_dir = audit_dir
        self._dry_run = dry_run

    def check(
        self,
        action_name: str,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> PolicyEvaluation:
        """
        Evaluate an action against the policy.

        Args:
            action_name: Name of the tool/action being invoked
            parameters: Parameters to evaluate against policy
            context: Optional additional context

        Returns:
            PolicyEvaluation with result (ALLOWED/BLOCKED) and violations
        """
        self._policy_manager.check_reload()
        evaluation = self._policy_manager.evaluate(parameters)

        # Record audit
        try:
            record = build_audit_record(
                agent_info=AgentInfo(
                    name="chimera-runtime-guard",
                    version=_get_version(),
                    csl_core_version="N/A",
                    model="integration",
                    model_provider="external",
                    temperature=0.0,
                ),
                input_info=InputInfo(
                    raw_request=f"Tool call: {action_name}",
                    structured_params=parameters,
                    context=context or {},
                ),
                attempts=[Attempt(
                    attempt_number=1,
                    candidates=[Candidate(
                        candidate_id="ext_001",
                        strategy=action_name,
                        llm_reasoning="External agent tool call",
                        llm_confidence=1.0,
                        parameters=parameters,
                        policy_evaluation=evaluation,
                    )],
                    outcome=(
                        AttemptOutcome.ALL_PASSED
                        if evaluation.result == "ALLOWED"
                        else AttemptOutcome.ALL_BLOCKED
                    ),
                )],
                action_taken=action_name,
                result=evaluation.result,
                final_parameters=parameters if evaluation.result == "ALLOWED" else {},
                policy_file=self._policy_manager.policy_path,
                policy_hash=self._policy_manager.hash,
                total_duration_ms=evaluation.duration_ms,
            )
            save_record(record, audit_dir=self._audit_dir)
        except Exception:
            pass  # Don't let audit failures break the guard

        return evaluation

    @property
    def policy_manager(self) -> PolicyManager:
        return self._policy_manager
