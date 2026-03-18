"""
chimera-runtime — Deterministic Runtime for AI Agents

Every AI decision enforced — not suggested. Backed by formal verification. Executed by design.

Quick Start:
    from chimera_runtime import ChimeraAgent

    agent = ChimeraAgent(
        model="gpt-4o",
        api_key="sk-...",
        policy="./policies/governance.csl",
    )
    result = agent.decide("Increase marketing spend by 40%", context={"role": "MANAGER"})
    result.result       # "ALLOWED" or "BLOCKED"
    result.action       # Action taken
    result.explanation  # Why this decision was made
    result.audit        # Full DecisionAuditRecord
"""

__version__ = "1.0.0"
__author__ = "Chimera Protocol"
__license__ = "Apache-2.0"

# CSL-Core availability flag
from .policy import CSL_CORE_AVAILABLE

# YAML Rule Engine (always available)
from .rules import YAMLRuleEngine, RuleEngineError

# Core models always available
from .models import (
    # Config
    AgentConfig,
    LLMConfig,
    PolicyConfig,
    AuditConfig,
    OversightConfig,

    # Decision pipeline
    DecisionResult,
    DecisionAuditRecord,
    PolicyEvaluation,
    Candidate,
    Attempt,
    Violation,
    ReasoningTrace,

    # Info objects
    AgentInfo,
    InputInfo,
    DecisionInfo,
    ComplianceInfo,
    PerformanceInfo,
    HumanOversightRecord,

    # Enums
    DecisionResultType,
    AttemptOutcome,
    EnforcementType,

    # Helpers
    generate_decision_id,
    generate_candidate_id,
    utc_now_iso,
)

# Config
from .config import load_config, save_config, validate_config, ConfigError

# Policy
from .policy import PolicyManager, PolicyError, PolicyFileNotFoundError

# LLM
from .llm import (
    get_provider,
    BaseLLMProvider,
    LLMError,
    LLMAuthenticationError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMResponseParseError,
    build_variable_spec,
)

# Agent
from .agent import ChimeraAgent, ChimeraAgentError, AgentHalted

# Oversight
from .oversight import HumanOversight, OversightError

# Audit
from .audit import (
    build_audit_record, save_record, load_record, load_all_records,
    enforce_retention, AuditStorageError, AuditQuery, AuditStats,
    generate_html,
)

# Docs
from .docs import AnnexIVGenerator, DocsGeneratorError

# Licensing
from .licensing import (
    ChimeraLicense,
    LicenseError,
    LicenseTier,
    TierUpgradeRequired,
    activate_license,
    check_tier,
    get_license,
)

__all__ = [
    # Package info
    "__version__",

    # Agent (primary API)
    "ChimeraAgent",
    "ChimeraAgentError",
    "AgentHalted",

    # Oversight
    "HumanOversight",
    "OversightError",

    # Config
    "AgentConfig",
    "LLMConfig",
    "PolicyConfig",
    "AuditConfig",
    "OversightConfig",
    "load_config",
    "save_config",
    "validate_config",
    "ConfigError",

    # Policy
    "PolicyManager",
    "PolicyError",
    "PolicyFileNotFoundError",

    # LLM
    "get_provider",
    "BaseLLMProvider",
    "LLMError",
    "LLMAuthenticationError",
    "LLMRateLimitError",
    "LLMTimeoutError",
    "LLMResponseParseError",
    "build_variable_spec",

    # Decision pipeline
    "DecisionResult",
    "DecisionAuditRecord",
    "PolicyEvaluation",
    "Candidate",
    "Attempt",
    "Violation",
    "ReasoningTrace",

    # Info objects
    "AgentInfo",
    "InputInfo",
    "DecisionInfo",
    "ComplianceInfo",
    "PerformanceInfo",
    "HumanOversightRecord",

    # Enums
    "DecisionResultType",
    "AttemptOutcome",
    "EnforcementType",

    # Helpers
    "generate_decision_id",
    "generate_candidate_id",
    "utc_now_iso",
    
    # Audit
    "build_audit_record", 
    "save_record", 
    "load_record", 
    "load_all_records",
    "enforce_retention", 
    "AuditStorageError", 
    "AuditQuery", 
    "AuditStats",
    "generate_html",
    
    # Docs
    "AnnexIVGenerator",
    "DocsGeneratorError",

    # Rule engine
    "YAMLRuleEngine",
    "RuleEngineError",
    "CSL_CORE_AVAILABLE",

    # Licensing
    "ChimeraLicense",
    "LicenseError",
    "LicenseTier",
    "TierUpgradeRequired",
    "activate_license",
    "check_tier",
    "get_license",
]
