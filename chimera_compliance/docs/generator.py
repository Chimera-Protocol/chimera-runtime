"""
chimera-compliance — Annex IV Documentation Generator

Generates EU AI Act Annex IV technical documentation by combining:
  - Agent configuration (name, version, LLM, policy settings)
  - Audit logs (performance metrics, violation stats)
  - Policy files (variables, constraints, verification status)

Auto-fills 14 of 19 Annex IV sections. Remaining 5 require manual input.

Usage:
    from chimera_compliance.docs import AnnexIVGenerator

    gen = AnnexIVGenerator(
        config=my_config,
        audit_dir="./audit_logs",
        policy_path="./policies/governance.csl",
    )

    # Generate the document
    path = gen.generate(output_path="./docs/annex_iv.md")

    # Check coverage status
    status = gen.status()
    print(f"{status['filled']}/19 sections auto-filled")

    # Refresh with latest data
    path = gen.refresh()
"""

from __future__ import annotations

import os
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from jinja2 import Environment, BaseLoader
    HAS_JINJA2 = True
except ImportError:
    HAS_JINJA2 = False

from ..models import AgentConfig, utc_now_iso, SCHEMA_VERSION
from ..audit.query import AuditQuery, AuditStats
from ..audit.storage import load_all_records


# ============================================================================
# SECTION DEFINITIONS
# ============================================================================

# Sections that are auto-filled from chimera-compliance data
AUTO_SECTIONS = [1, 2, 3, 4, 5, 6, 9, 11, 12, 13, 14, 15, 16, 17]

# Sections that require manual input
MANUAL_SECTIONS = [7, 8, 10, 18, 19]

SECTION_TITLES = {
    1: "General Description of the AI System",
    2: "Elements of the AI System and Development Process",
    3: "Monitoring, Functioning, and Control",
    4: "Appropriateness of Performance Metrics",
    5: "Risk Management System",
    6: "Description of Changes Throughout Lifecycle",
    7: "Harmonised Standards Applied",
    8: "Description of Data Used",
    9: "Human Oversight Measures",
    10: "Pre-determined Changes",
    11: "Validation and Testing Procedures",
    12: "Cybersecurity Measures",
    13: "Computing Infrastructure",
    14: "Description of Input Data",
    15: "Description of Output",
    16: "Post-Market Monitoring Plan",
    17: "Description of Changes",
    18: "Relevant Information About Datasets",
    19: "EU Declaration of Conformity",
}


# ============================================================================
# ERRORS
# ============================================================================

class DocsGeneratorError(Exception):
    """Raised when documentation generation fails."""
    pass


# ============================================================================
# GENERATOR
# ============================================================================

class AnnexIVGenerator:
    """
    Generates EU AI Act Annex IV technical documentation.

    Combines data from config, audit logs, and policy files
    to auto-fill 14 of 19 required sections.
    """

    def __init__(
        self,
        config: Optional[AgentConfig] = None,
        audit_dir: str = "./audit_logs",
        policy_path: Optional[str] = None,
        stats_period_days: int = 90,
    ):
        self._config = config or AgentConfig()
        self._audit_dir = audit_dir
        self._policy_path = policy_path or self._config.policy.file
        self._stats_period_days = stats_period_days
        self._last_output_path: Optional[str] = None

    # ========================================================================
    # GENERATE
    # ========================================================================

    def generate(
        self,
        output_path: str = "./docs/annex_iv_technical_documentation.md",
    ) -> str:
        """
        Generate Annex IV technical documentation.

        Requires ENTERPRISE tier license.

        Args:
            output_path: Where to write the Markdown file

        Returns:
            Path to the generated file

        Raises:
            DocsGeneratorError: If generation fails
            TierUpgradeRequired: If license tier is below ENTERPRISE
        """
        from ..licensing import require_tier as _rt, TierUpgradeRequired
        # Enterprise gate check
        from ..licensing import check_tier
        if not check_tier("enterprise"):
            raise TierUpgradeRequired(
                feature="Annex IV documentation generation",
                required_tier="enterprise",
                current_tier="free",
            )

        if not HAS_JINJA2:
            raise DocsGeneratorError(
                "Jinja2 is required for document generation. "
                "Install with: pip install jinja2"
            )

        # Collect all template variables
        context = self._build_context()

        # Load and render template
        template_content = self._load_template()
        try:
            env = Environment(loader=BaseLoader(), keep_trailing_newline=True)
            template = env.from_string(template_content)
            rendered = template.render(**context)
        except Exception as e:
            raise DocsGeneratorError(f"Template rendering failed: {e}") from e

        # Write output
        out_path = Path(output_path)
        try:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(rendered, encoding="utf-8")
        except OSError as e:
            raise DocsGeneratorError(f"Cannot write output file: {e}") from e

        self._last_output_path = str(out_path)
        return str(out_path)

    # ========================================================================
    # STATUS
    # ========================================================================

    def status(self) -> Dict[str, Any]:
        """
        Report documentation coverage status.

        Returns:
            Dict with filled/total counts, auto/manual section lists,
            and whether audit data is available.
        """
        has_audit = self._has_audit_data()
        has_policy = self._has_policy_data()

        # Effective filled sections (some auto sections need audit data)
        effective_auto = list(AUTO_SECTIONS)
        if not has_audit:
            # Sections 4, 6, 17 need audit data
            for s in [4, 6, 17]:
                if s in effective_auto:
                    effective_auto.remove(s)

        return {
            "filled": len(effective_auto),
            "total": 19,
            "manual_required": len(MANUAL_SECTIONS),
            "auto_sections": [
                {"section": s, "title": SECTION_TITLES[s], "status": "filled"}
                for s in effective_auto
            ],
            "manual_sections": [
                {"section": s, "title": SECTION_TITLES[s], "status": "manual_required"}
                for s in MANUAL_SECTIONS
            ],
            "pending_sections": [
                {"section": s, "title": SECTION_TITLES[s], "status": "needs_audit_data"}
                for s in AUTO_SECTIONS if s not in effective_auto
            ],
            "has_audit_data": has_audit,
            "has_policy_data": has_policy,
            "last_output_path": self._last_output_path,
        }

    # ========================================================================
    # REFRESH
    # ========================================================================

    def refresh(self, output_path: Optional[str] = None) -> str:
        """
        Re-generate documentation with latest data.

        Uses the same output path as the last generate() call,
        or the provided path.
        """
        path = output_path or self._last_output_path
        if path is None:
            path = "./docs/annex_iv_technical_documentation.md"
        return self.generate(output_path=path)

    # ========================================================================
    # INTERNAL — Context Builder
    # ========================================================================

    def _build_context(self) -> Dict[str, Any]:
        """Assemble all template variables from config, audit, and policy."""
        cfg = self._config
        ctx: Dict[str, Any] = {}

        # Agent identity
        ctx["agent_name"] = cfg.agent.name
        ctx["agent_version"] = cfg.agent.version
        ctx["schema_version"] = SCHEMA_VERSION
        ctx["generated_at"] = utc_now_iso()
        ctx["csl_core_version"] = self._get_csl_core_version()

        # ── Deployment mode detection ──
        is_standalone = cfg.llm.provider not in ("none", "external", "")
        ctx["is_standalone"] = is_standalone
        ctx["is_integration"] = not is_standalone

        # ── Policy backend detection ──
        policy_ext = Path(self._policy_path).suffix.lower()
        is_csl = policy_ext == ".csl"

        from ..policy import CSL_CORE_AVAILABLE
        ctx["csl_core_available"] = CSL_CORE_AVAILABLE
        ctx["has_z3"] = CSL_CORE_AVAILABLE and is_csl

        if is_csl and CSL_CORE_AVAILABLE:
            ctx["policy_backend"] = "csl-core"
            ctx["policy_engine_name"] = "CSL-Core (Chimera Specification Language)"
            ctx["verification_method"] = "Z3 SMT Solver — 4-stage formal verification"
        elif is_csl and not CSL_CORE_AVAILABLE:
            ctx["policy_backend"] = "csl-core (not installed)"
            ctx["policy_engine_name"] = "CSL-Core (not installed)"
            ctx["verification_method"] = "Not available — install chimera-compliance[csl]"
        else:
            ctx["policy_backend"] = "yaml-rule-engine"
            ctx["policy_engine_name"] = "YAML Rule Engine (built-in)"
            ctx["verification_method"] = "Syntax validation (rule-based)"

        # ── Architecture description (dynamic) ──
        if is_standalone and ctx["has_z3"]:
            ctx["architecture_desc"] = (
                "Neural (LLM) → Symbolic (CSL Policy Engine + Z3) → Audit Pipeline"
            )
            ctx["system_type"] = (
                "neuro-symbolic AI compliance framework that combines large language "
                "model (LLM) reasoning with Z3 formal policy verification"
            )
        elif is_standalone:
            ctx["architecture_desc"] = (
                "Neural (LLM) → Rule Engine (YAML Policy) → Audit Pipeline"
            )
            ctx["system_type"] = (
                "AI compliance framework that combines large language model (LLM) "
                "reasoning with rule-based policy enforcement"
            )
        elif ctx["has_z3"]:
            ctx["architecture_desc"] = (
                "External Agent → Symbolic (CSL Policy Engine + Z3) → Audit Pipeline"
            )
            ctx["system_type"] = (
                "plug-in compliance layer that validates external AI agent actions "
                "against formally verified policy constraints"
            )
        else:
            ctx["architecture_desc"] = (
                "External Agent → Rule Engine (YAML Policy) → Audit Pipeline"
            )
            ctx["system_type"] = (
                "plug-in compliance layer that validates external AI agent actions "
                "against rule-based policy constraints"
            )

        # ── Oversight mode inference ──
        if cfg.oversight.require_confirmation:
            ctx["oversight_mode"] = "interactive"
            ctx["oversight_mode_desc"] = (
                "Human confirmation required before every action execution"
            )
        else:
            ctx["oversight_mode"] = "auto"
            ctx["oversight_mode_desc"] = (
                "Automatic approval — no human in the loop (override available)"
            )

        # LLM config
        ctx["llm_provider"] = cfg.llm.provider
        ctx["llm_model"] = cfg.llm.model
        ctx["llm_temperature"] = cfg.llm.temperature
        ctx["candidates_per_attempt"] = cfg.llm.candidates_per_attempt
        ctx["max_retries"] = cfg.llm.max_retries

        # Policy config
        ctx["policy_file"] = self._policy_path
        ctx["auto_verify"] = cfg.policy.auto_verify

        # Policy data (variables, constraints, domain, hash)
        policy_data = self._get_policy_data()
        ctx.update(policy_data)

        # Audit config
        ctx["audit_enabled"] = cfg.audit.enabled
        ctx["audit_output_dir"] = cfg.audit.output_dir
        ctx["audit_format"] = cfg.audit.format
        ctx["audit_html_reports"] = cfg.audit.html_reports
        ctx["audit_retention_days"] = cfg.audit.retention_days

        # Oversight config
        ctx["require_confirmation"] = cfg.oversight.require_confirmation
        ctx["allow_override"] = cfg.oversight.allow_override
        ctx["policy_hot_reload"] = cfg.oversight.policy_hot_reload
        ctx["stop_on_consecutive_blocks"] = cfg.oversight.stop_on_consecutive_blocks

        # ── Runtime environment (dynamic) ──
        ctx["python_version"] = platform.python_version()
        ctx["os_platform"] = platform.platform()
        ctx["installed_deps"] = self._detect_installed_deps()

        # Audit stats
        audit_data = self._get_audit_data()
        ctx.update(audit_data)

        # Filled count
        ctx["filled_count"] = self.status()["filled"]

        return ctx

    def _get_policy_data(self) -> Dict[str, Any]:
        """Extract policy metadata: variables, constraints, domain, hash."""
        data: Dict[str, Any] = {
            "policy_hash": "N/A",
            "policy_domain": "N/A",
            "policy_variables": [],
            "policy_constraints": [],
            "policy_constraint_count": 0,
            "policy_variable_count": 0,
            "policy_verified": False,
            "policy_verification_errors": [],
        }

        try:
            from ..policy import PolicyManager
            pm = PolicyManager(self._policy_path, auto_verify=False)
            data["policy_hash"] = pm.hash
            data["policy_domain"] = pm.domain_name

            # Variables
            names = pm.variable_names
            domains = pm.variable_domains
            data["policy_variables"] = [
                (name, domains.get(name, "any"))
                for name in sorted(names)
            ]
            data["policy_variable_count"] = len(names)

            # Constraints
            data["policy_constraints"] = pm.constraint_names
            data["policy_constraint_count"] = len(pm.constraint_names)

            # Verification status
            try:
                ok, errors = pm.verify()
                data["policy_verified"] = ok
                data["policy_verification_errors"] = errors
            except Exception:
                data["policy_verified"] = False

        except Exception:
            pass

        return data

    def _get_audit_data(self) -> Dict[str, Any]:
        """Extract audit statistics and top violations."""
        data: Dict[str, Any] = {
            "has_audit_stats": False,
            "stats_period_days": self._stats_period_days,
            "stats_total_decisions": 0,
            "stats_allowed_count": 0,
            "stats_blocked_count": 0,
            "stats_human_override_count": 0,
            "stats_interrupted_count": 0,
            "stats_block_rate": "0.0",
            "stats_allow_rate": "0.0",
            "stats_avg_duration_ms": "0.0",
            "stats_avg_candidates": "0.0",
            "stats_avg_attempts": "0.0",
            "stats_total_violations": 0,
            "stats_period_start": "",
            "stats_period_end": "",
            "top_violations": [],
        }

        if not self._has_audit_data():
            return data

        try:
            query = AuditQuery(self._audit_dir)
            stats = query.stats(last_days=self._stats_period_days)

            if stats.total_decisions > 0:
                data["has_audit_stats"] = True
                data["stats_total_decisions"] = stats.total_decisions
                data["stats_allowed_count"] = stats.allowed_count
                data["stats_blocked_count"] = stats.blocked_count
                data["stats_human_override_count"] = stats.human_override_count
                data["stats_interrupted_count"] = stats.interrupted_count
                data["stats_block_rate"] = f"{stats.block_rate * 100:.1f}"
                data["stats_allow_rate"] = f"{stats.allow_rate * 100:.1f}"
                data["stats_avg_duration_ms"] = f"{stats.avg_duration_ms:.1f}"
                data["stats_avg_candidates"] = f"{stats.avg_candidates_per_decision:.1f}"
                data["stats_avg_attempts"] = f"{stats.avg_attempts_per_decision:.1f}"
                data["stats_total_violations"] = stats.total_violations
                data["stats_period_start"] = stats.period_start
                data["stats_period_end"] = stats.period_end

                data["top_violations"] = query.top_violations(n=10)

        except Exception:
            pass

        return data

    # ========================================================================
    # INTERNAL — Helpers
    # ========================================================================

    def _load_template(self) -> str:
        """Load the Annex IV Markdown template."""
        # First try the installed package location
        template_path = Path(__file__).parent / "templates" / "annex_iv.md"
        if template_path.exists():
            return template_path.read_text(encoding="utf-8")

        raise DocsGeneratorError(
            f"Annex IV template not found at {template_path}. "
            "Ensure the templates directory is installed."
        )

    def _has_audit_data(self) -> bool:
        """Check if audit directory has any records."""
        dir_path = Path(self._audit_dir)
        if not dir_path.exists():
            return False
        return any(dir_path.glob("dec_*.json"))

    def _has_policy_data(self) -> bool:
        """Check if policy file exists."""
        return Path(self._policy_path).exists()

    def _get_csl_core_version(self) -> str:
        """Get installed csl-core version."""
        try:
            import chimera_core
            return getattr(chimera_core, "__version__", "unknown")
        except ImportError:
            return "not installed"

    def _detect_installed_deps(self) -> List[Dict[str, str]]:
        """Detect actually installed dependencies and their versions."""
        deps = []
        dep_checks = [
            ("chimera-core", "chimera_core"),
            ("click", "click"),
            ("rich", "rich"),
            ("pyyaml", "yaml"),
            ("jinja2", "jinja2"),
            ("langchain-core", "langchain_core"),
            ("langgraph", "langgraph"),
            ("llama-index-core", "llama_index"),
            ("crewai", "crewai"),
            ("autogen-agentchat", "autogen_agentchat"),
            ("openai", "openai"),
            ("anthropic", "anthropic"),
            ("google-generativeai", "google.generativeai"),
        ]

        for pkg_name, import_name in dep_checks:
            try:
                mod = __import__(import_name.split(".")[0])
                if "." in import_name:
                    for part in import_name.split(".")[1:]:
                        mod = getattr(mod, part)
                # Prefer importlib.metadata for version to avoid deprecation
                version = self._get_pkg_version(pkg_name, mod)
                deps.append({"name": pkg_name, "version": version})
            except (ImportError, AttributeError):
                pass

        return deps

    @staticmethod
    def _get_pkg_version(pkg_name: str, mod: Any) -> str:
        """Get package version via importlib.metadata, fallback to __version__."""
        try:
            from importlib.metadata import version as meta_version
            return meta_version(pkg_name)
        except Exception:
            return getattr(mod, "__version__", "installed")
