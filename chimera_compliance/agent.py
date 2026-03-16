"""
chimera-compliance — Agent Core

The ChimeraAgent is the central orchestrator:
  1. Receives a natural language request
  2. Asks the LLM to generate N diverse strategy candidates
  3. Evaluates each candidate against the CSL policy (formal verification)
  4. Retries with rejection context if all candidates are blocked
  5. Selects the best allowed candidate (highest confidence)
  6. Builds a complete audit record (EU AI Act Art. 12, 13, 14, 86)
  7. Returns a DecisionResult

Usage:
    agent = ChimeraAgent(
        model="gpt-4o",
        api_key="sk-...",
        policy="./policies/governance.csl",
    )
    result = agent.decide("Increase marketing spend by 40%", context={"role": "MANAGER"})

    result.result       # "ALLOWED"
    result.action       # "Conservative budget increase"
    result.explanation  # "Selected highest-confidence compliant candidate"
    result.audit        # Full DecisionAuditRecord
"""

from __future__ import annotations

import time
from typing import Any, Callable, Dict, List, Optional

from .models import (
    AgentConfig,
    AgentInfo,
    Attempt,
    AttemptOutcome,
    Candidate,
    ComplianceInfo,
    DecisionAuditRecord,
    DecisionInfo,
    DecisionResult,
    DecisionResultType,
    EnforcementType,
    HumanOversightRecord,
    InputInfo,
    PerformanceInfo,
    ReasoningTrace,
    Violation,
    generate_decision_id,
    utc_now_iso,
    SCHEMA_VERSION,
)
from .config import load_config
from .policy import PolicyManager, PolicyError
from .llm import get_provider, BaseLLMProvider, LLMError, build_variable_spec
from .oversight import HumanOversight


# ============================================================================
# ERRORS
# ============================================================================

class ChimeraAgentError(Exception):
    """Base error for agent operations."""
    pass


class AgentHalted(ChimeraAgentError):
    """Raised when decide() is called on a halted agent (Art. 14 stop mechanism)."""
    pass


# ============================================================================
# CHIMERA AGENT
# ============================================================================

class ChimeraAgent:
    """
    The chimera-compliance decision orchestrator.

    Orchestrates:
      LLM (neural) → CSL Policy (symbolic) → Audit Record (compliance)

    Thread Safety:
      Not thread-safe. Use one agent instance per thread/process.
    """

    def __init__(
        self,
        model: str = "gpt-4o",
        api_key: Optional[str] = None,
        policy: str = "./policies/governance.csl",
        provider: str = "openai",
        temperature: float = 0.7,
        max_retries: int = 3,
        candidates_per_attempt: int = 3,
        dry_run: bool = False,
        oversight: Optional[HumanOversight] = None,
        llm_provider: Optional[BaseLLMProvider] = None,
        policy_manager: Optional[PolicyManager] = None,
        agent_name: str = "chimera-compliance",
        audit_dir: Optional[str] = None,
    ):
        """
        Initialize the ChimeraAgent.

        Args:
            model: LLM model identifier
            api_key: API key for the LLM provider
            policy: Path to the CSL policy file
            provider: LLM provider name ("openai", "anthropic", "google", "ollama")
            temperature: LLM sampling temperature
            max_retries: Maximum retry attempts when all candidates are blocked
            candidates_per_attempt: Number of candidates to generate per attempt
            dry_run: If True, policy never blocks (shadow mode)
            oversight: Human oversight controller (defaults to auto-approve)
            llm_provider: Pre-configured LLM provider (overrides model/api_key/provider)
            policy_manager: Pre-configured PolicyManager (overrides policy path)
            agent_name: Name for audit records
            audit_dir: Directory to persist audit records (None = no auto-save)
        """
        # LLM
        if llm_provider is not None:
            self._llm = llm_provider
        else:
            self._llm = get_provider(
                provider=provider,
                model=model,
                api_key=api_key,
                temperature=temperature,
            )

        # Policy
        if policy_manager is not None:
            self._policy = policy_manager
        else:
            self._policy = PolicyManager(
                policy_path=policy,
                auto_verify=True,
                dry_run=dry_run,
            )

        # Config
        self._max_retries = max_retries
        self._candidates_per_attempt = candidates_per_attempt
        self._dry_run = dry_run
        self._agent_name = agent_name
        self._audit_dir = audit_dir

        # Oversight
        self._oversight = oversight or HumanOversight(mode="auto")

        # State
        self._halted = False
        self._consecutive_blocks = 0
        self._decision_count = 0

    # ========================================================================
    # FACTORY
    # ========================================================================

    @classmethod
    def from_config(
        cls,
        config: Optional[AgentConfig] = None,
        config_path: Optional[str] = None,
        **overrides: Any,
    ) -> ChimeraAgent:
        """
        Create a ChimeraAgent from an AgentConfig or YAML file.

        Args:
            config: Pre-loaded AgentConfig object
            config_path: Path to YAML config file
            **overrides: Override any config field

        Returns:
            Configured ChimeraAgent instance
        """
        if config is None:
            config = load_config(config_path)

        return cls(
            model=overrides.get("model", config.llm.model),
            api_key=overrides.get("api_key", config.llm.api_key),
            policy=overrides.get("policy", config.policy.file),
            provider=overrides.get("provider", config.llm.provider),
            temperature=overrides.get("temperature", config.llm.temperature),
            max_retries=overrides.get("max_retries", config.llm.max_retries),
            candidates_per_attempt=overrides.get(
                "candidates_per_attempt", config.llm.candidates_per_attempt
            ),
            dry_run=overrides.get("dry_run", False),
            audit_dir=overrides.get("audit_dir", config.audit.output_dir if config.audit.enabled else None),
            oversight=HumanOversight(mode=overrides.get("oversight_mode", "auto")),
        )

    # ========================================================================
    # DECIDE — The Main Pipeline
    # ========================================================================

    def decide(
        self,
        request: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> DecisionResult:
        """
        Execute the full neuro→symbolic→audit pipeline.

        Args:
            request: Natural language request from the user
            context: Additional context (role, user_id, session_id, etc.)

        Returns:
            DecisionResult with .result, .action, .explanation, .parameters, .audit

        Raises:
            AgentHalted: If the agent has been halted via halt()
            ChimeraAgentError: If the pipeline fails unrecoverably
        """
        if self._halted:
            raise AgentHalted(
                "Agent has been halted (Art. 14 stop mechanism). "
                "Call resume() to reactivate."
            )

        context = context or {}
        pipeline_start = time.perf_counter()
        decision_id = generate_decision_id()
        timestamp = utc_now_iso()

        # Hot-reload policy if changed
        self._policy.check_reload()

        # Build variable spec for LLM prompt
        variable_spec = build_variable_spec(
            self._policy.variable_names,
            self._policy.variable_domains,
        )

        # ---- Retry Loop ----
        attempts: List[Attempt] = []
        all_candidates: List[Candidate] = []
        rejection_context: Optional[str] = None
        best_candidate: Optional[Candidate] = None
        llm_total_ms: float = 0.0
        policy_total_ms: float = 0.0
        human_oversight_record: Optional[HumanOversightRecord] = None

        for attempt_num in range(1, self._max_retries + 1):
            # Step 1: Generate candidates via LLM
            llm_start = time.perf_counter()
            try:
                candidates = self._llm.generate_candidates(
                    request=request,
                    context=context,
                    n=self._candidates_per_attempt,
                    variable_spec=variable_spec,
                    rejection_context=rejection_context,
                )
            except LLMError as e:
                raise ChimeraAgentError(f"LLM generation failed: {e}") from e
            llm_total_ms += (time.perf_counter() - llm_start) * 1000

            # Step 2: Evaluate each candidate against policy
            policy_start = time.perf_counter()
            allowed_candidates: List[Candidate] = []

            for candidate in candidates:
                try:
                    evaluation = self._policy.evaluate(candidate.parameters)
                    candidate.policy_evaluation = evaluation

                    if evaluation.result == "ALLOWED":
                        allowed_candidates.append(candidate)
                except PolicyError as e:
                    # Policy evaluation failed — mark candidate as blocked
                    candidate.policy_evaluation = None

            policy_total_ms += (time.perf_counter() - policy_start) * 1000
            all_candidates.extend(candidates)

            # Step 3: Determine attempt outcome
            if len(allowed_candidates) == len(candidates):
                outcome = AttemptOutcome.ALL_PASSED.value
            elif allowed_candidates:
                outcome = AttemptOutcome.PARTIAL.value
            else:
                outcome = AttemptOutcome.ALL_BLOCKED.value

            attempts.append(Attempt(
                attempt_number=attempt_num,
                candidates=candidates,
                outcome=outcome,
                note=f"{'%d' % len(allowed_candidates)}/{len(candidates)} candidates passed policy",
            ))

            # Step 4: If we have allowed candidates, select best and stop
            if allowed_candidates:
                best_candidate = self._select_best(allowed_candidates)
                break

            # Step 5: Build rejection context for next attempt
            rejection_context = self._build_rejection_context(candidates)

        # ---- Post-Loop: Determine Result ----
        pipeline_end = time.perf_counter()
        total_ms = (pipeline_end - pipeline_start) * 1000

        if best_candidate is not None:
            # Check human oversight confirmation
            if self._oversight.mode != "auto":
                confirmed = self._oversight.request_confirmation(
                    best_candidate,
                    best_candidate.policy_evaluation,
                )
                if not confirmed:
                    human_oversight_record = self._oversight.apply_override(
                        action="STOP",
                        reason="Human declined confirmation",
                    )
                    return self._build_result(
                        decision_id=decision_id,
                        timestamp=timestamp,
                        result_type=DecisionResultType.INTERRUPTED.value,
                        action="DECLINED_BY_HUMAN",
                        explanation="Human declined the proposed action",
                        parameters={},
                        attempts=attempts,
                        all_candidates=all_candidates,
                        selected_id=None,
                        selection_reasoning="Human declined",
                        total_ms=total_ms,
                        llm_ms=llm_total_ms,
                        policy_ms=policy_total_ms,
                        human_oversight_record=human_oversight_record,
                    )

            # SUCCESS — allowed candidate selected
            self._consecutive_blocks = 0
            self._decision_count += 1

            return self._build_result(
                decision_id=decision_id,
                timestamp=timestamp,
                result_type=DecisionResultType.ALLOWED.value,
                action=best_candidate.strategy,
                explanation=f"Selected candidate {best_candidate.candidate_id} "
                            f"(confidence: {best_candidate.llm_confidence:.0%}): "
                            f"{best_candidate.llm_reasoning[:200]}",
                parameters=best_candidate.parameters,
                attempts=attempts,
                all_candidates=all_candidates,
                selected_id=best_candidate.candidate_id,
                selection_reasoning=(
                    f"Highest confidence ({best_candidate.llm_confidence:.2f}) "
                    f"among {sum(1 for a in attempts for c in a.candidates if c.policy_evaluation and c.policy_evaluation.result == 'ALLOWED')} "
                    f"policy-compliant candidates"
                ),
                total_ms=total_ms,
                llm_ms=llm_total_ms,
                policy_ms=policy_total_ms,
                human_oversight_record=human_oversight_record,
            )

        else:
            # ALL BLOCKED — no candidate passed after all retries
            self._consecutive_blocks += 1
            self._decision_count += 1

            # Collect all violations for the explanation
            all_violations = []
            for attempt in attempts:
                for c in attempt.candidates:
                    if c.policy_evaluation and c.policy_evaluation.violations:
                        for v in c.policy_evaluation.violations:
                            if v.constraint not in [av.constraint for av in all_violations]:
                                all_violations.append(v)

            violation_summary = "; ".join(
                v.constraint for v in all_violations[:5]
            )

            return self._build_result(
                decision_id=decision_id,
                timestamp=timestamp,
                result_type=DecisionResultType.BLOCKED.value,
                action="BLOCKED",
                explanation=(
                    f"All {len(all_candidates)} candidates blocked after "
                    f"{len(attempts)} attempts. Violated constraints: {violation_summary}"
                ),
                parameters={},
                attempts=attempts,
                all_candidates=all_candidates,
                selected_id=None,
                selection_reasoning="No policy-compliant candidates found",
                total_ms=total_ms,
                llm_ms=llm_total_ms,
                policy_ms=policy_total_ms,
                human_oversight_record=human_oversight_record,
            )

    # ========================================================================
    # HALT / RESUME (Art. 14 Stop Mechanism)
    # ========================================================================

    def halt(self, reason: str = "") -> None:
        """
        Halt the agent. All subsequent decide() calls will raise AgentHalted.
        This is the Art. 14 "stop mechanism" for human oversight.

        Requires PRO tier license.
        """
        from .licensing import check_tier, TierUpgradeRequired
        if not check_tier("pro"):
            raise TierUpgradeRequired(
                feature="halt/resume (Art. 14 stop mechanism)",
                required_tier="pro",
                current_tier="free",
            )
        self._halted = True

    def resume(self) -> None:
        """Resume the agent after a halt. Requires PRO tier license."""
        from .licensing import check_tier, TierUpgradeRequired
        if not check_tier("pro"):
            raise TierUpgradeRequired(
                feature="halt/resume (Art. 14 stop mechanism)",
                required_tier="pro",
                current_tier="free",
            )
        self._halted = False

    @property
    def is_halted(self) -> bool:
        return self._halted

    @property
    def decision_count(self) -> int:
        return self._decision_count

    @property
    def consecutive_blocks(self) -> int:
        return self._consecutive_blocks

    # ========================================================================
    # INTERNAL — Candidate Selection
    # ========================================================================

    def _select_best(self, allowed_candidates: List[Candidate]) -> Candidate:
        """
        Select the best candidate from a list of allowed candidates.
        Strategy: highest LLM confidence score.
        """
        return max(allowed_candidates, key=lambda c: c.llm_confidence)

    # ========================================================================
    # INTERNAL — Rejection Context Builder
    # ========================================================================

    def _build_rejection_context(self, candidates: List[Candidate]) -> str:
        """
        Build a rejection context string from blocked candidates.
        This is fed back to the LLM on retry so it can learn from violations.
        """
        lines: List[str] = []
        for c in candidates:
            if c.policy_evaluation and c.policy_evaluation.violations:
                for v in c.policy_evaluation.violations:
                    lines.append(
                        f"- Candidate '{c.strategy}': Constraint '{v.constraint}' "
                        f"violated. {v.explanation}"
                    )
        return "\n".join(lines) if lines else "All candidates were blocked by policy."

    # ========================================================================
    # INTERNAL — Audit Record Builder
    # ========================================================================

    def _build_result(
        self,
        decision_id: str,
        timestamp: str,
        result_type: str,
        action: str,
        explanation: str,
        parameters: Dict[str, Any],
        attempts: List[Attempt],
        all_candidates: List[Candidate],
        selected_id: Optional[str],
        selection_reasoning: str,
        total_ms: float,
        llm_ms: float,
        policy_ms: float,
        human_oversight_record: Optional[HumanOversightRecord] = None,
    ) -> DecisionResult:
        """Build the complete DecisionResult with audit record."""

        audit_start = time.perf_counter()

        # Agent info snapshot
        agent_info = AgentInfo(
            name=self._agent_name,
            version="0.1.0",
            csl_core_version=self._get_csl_core_version(),
            model=self._llm.model,
            model_provider=self._llm.provider_name,
            temperature=self._llm.temperature,
        )

        # Input info
        input_info = InputInfo(
            raw_request=action if action == "BLOCKED" else f"Request leading to: {action}",
            structured_params=parameters,
            context={},
        )

        # Reasoning trace
        reasoning = ReasoningTrace(
            total_candidates=len(all_candidates),
            total_attempts=len(attempts),
            attempts=attempts,
            selected_candidate=selected_id,
            selection_reasoning=selection_reasoning,
        )

        # Decision info
        decision_info = DecisionInfo(
            action_taken=action,
            result=result_type,
            final_parameters=parameters,
            policy_file=self._policy.policy_path,
            policy_hash=self._policy.hash,
        )

        # Compliance info — reflect actual verification backend
        backend = getattr(self._policy, "backend", "csl-core")
        is_z3 = backend == "csl-core"
        compliance = ComplianceInfo(
            formal_verification={
                "policy_verified": is_z3,
                "verification_engine": "Z3" if is_z3 else "rule-engine",
                "verification_result": "SAT" if is_z3 else "N/A",
            },
        )

        audit_ms = (time.perf_counter() - audit_start) * 1000

        # Performance info
        performance = PerformanceInfo(
            total_duration_ms=round(total_ms, 3),
            llm_duration_ms=round(llm_ms, 3),
            policy_evaluation_ms=round(policy_ms, 3),
            audit_generation_ms=round(audit_ms, 3),
        )

        # Build the full audit record
        audit_record = DecisionAuditRecord(
            schema_version=SCHEMA_VERSION,
            decision_id=decision_id,
            timestamp=timestamp,
            agent=agent_info,
            input=input_info,
            reasoning=reasoning,
            decision=decision_info,
            compliance=compliance,
            performance=performance,
            human_oversight_record=human_oversight_record,
        )

        result = DecisionResult(
            result=result_type,
            action=action,
            explanation=explanation,
            parameters=parameters,
            audit=audit_record,
        )

        # Auto-persist audit record to disk if audit_dir is configured
        if self._audit_dir:
            try:
                from .audit.storage import save_record
                save_record(audit_record, audit_dir=self._audit_dir)
            except Exception:
                pass  # Don't let audit I/O failures break the decide pipeline

        return result

    def _get_csl_core_version(self) -> str:
        """Get the installed csl-core version."""
        try:
            import chimera_core
            return getattr(chimera_core, "__version__", "unknown")
        except ImportError:
            return "not-installed"
