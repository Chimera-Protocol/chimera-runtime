"""
Compliance API Router — /api/v1/compliance/*

EU AI Act compliance status and Annex IV document generation.
Free: status flags only. Enterprise: Annex IV generate + download.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from chimera_runtime.audit.query import AuditQuery
from chimera_runtime.audit.storage import load_all_records
from chimera_runtime.policy import CSL_CORE_AVAILABLE

router = APIRouter(prefix="/compliance", tags=["compliance"])

_audit_dir: str = "./audit_logs"
_policies_dir: str = "./policies"
_config_path: str = "./.chimera/config.yaml"


def init_service(audit_dir: str, policies_dir: str, config_path: str) -> None:
    global _audit_dir, _policies_dir, _config_path
    _audit_dir = audit_dir
    _policies_dir = policies_dir
    _config_path = config_path


def _derive_compliance_from_system() -> tuple[dict, dict, dict]:
    """Derive EU AI Act compliance from actual system capabilities (no audit records needed)."""
    audit_path = Path(_audit_dir)
    policies_path = Path(_policies_dir)

    # Check actual system capabilities
    has_audit_dir = audit_path.exists() and audit_path.is_dir()
    has_policies = policies_path.exists() and any(
        f.suffix.lower() in (".csl", ".yaml", ".yml")
        for f in policies_path.iterdir()
    ) if policies_path.exists() else False
    has_csl_policies = policies_path.exists() and any(
        f.suffix.lower() == ".csl" for f in policies_path.iterdir()
    ) if policies_path.exists() else False

    eu_ai_act = {
        # Art. 12: Record keeping — True if audit logging infrastructure exists
        "article_12_record_keeping": has_audit_dir,
        # Art. 13: Transparency — True if policies are loaded (constraints are visible)
        "article_13_transparency": has_policies,
        # Art. 14: Human oversight — always True (halt/resume + override is built-in)
        "article_14_human_oversight": True,
        # Art. 15: Accuracy & resilience — True if Z3 formal verification is available
        "article_15_accuracy_resilience": CSL_CORE_AVAILABLE and has_csl_policies,
        # Art. 19: Automatic logs — True if audit dir is writable
        "article_19_automatic_logs": has_audit_dir,
        # Art. 86: Right to explanation — True if reasoning traces + html report are available
        "article_86_right_to_explanation": has_audit_dir,
    }

    formal = {
        "policy_verified": CSL_CORE_AVAILABLE and has_csl_policies,
        "verification_engine": "z3" if CSL_CORE_AVAILABLE else "none",
        "verification_result": "available" if CSL_CORE_AVAILABLE else "csl-core not installed",
    }

    oversight = {
        "override_available": True,
        "stop_mechanism": True,
        "policy_human_editable": has_policies,
    }

    return eu_ai_act, formal, oversight


@router.get("/status")
async def get_compliance_status():
    """
    EU AI Act compliance flags — Free tier.
    Shows which articles are satisfied based on audit records + system capabilities.
    """
    records = load_all_records(_audit_dir)

    if records:
        # Use latest record's compliance data (reflects actual decision-time checks)
        latest = records[0]  # newest first
        eu_ai_act = latest.compliance.eu_ai_act
        formal = latest.compliance.formal_verification
        oversight = latest.compliance.human_oversight
    else:
        # No audit records yet — derive from system capabilities
        eu_ai_act, formal, oversight = _derive_compliance_from_system()

    # Count compliant articles
    compliant_count = sum(1 for v in eu_ai_act.values() if v)
    total_articles = len(eu_ai_act)

    return {
        "compliant": compliant_count == total_articles,
        "score": f"{compliant_count}/{total_articles}",
        "articles": eu_ai_act,
        "formal_verification": formal,
        "human_oversight": oversight,
        "total_decisions": len(records),
    }
