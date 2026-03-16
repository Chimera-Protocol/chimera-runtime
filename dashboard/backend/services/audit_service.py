"""
Audit Service — wraps chimera_compliance.audit for the dashboard API.

All data comes from the existing JSON file-based audit storage.
The Python lib remains unlimited; tier limits are applied here (cloud dashboard only).
"""

from __future__ import annotations

import math
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

from chimera_compliance.audit.query import AuditQuery, AuditStats
from chimera_compliance.audit.storage import load_record, load_all_records
from chimera_compliance.audit.html_report import generate_html
from chimera_compliance.models import DecisionAuditRecord


# Tier-based limits for the cloud dashboard UI only.
# The local Python lib (pip install chimera-compliance) is NEVER limited.
TIER_LIMITS = {
    "free": {"max_days": 7, "max_records": 100, "full_detail": False},
    "pro": {"max_days": 90, "max_records": 10000, "full_detail": True},
    "enterprise": {"max_days": None, "max_records": None, "full_detail": True},
}


class AuditService:
    """Wraps AuditQuery with pagination and tier-based limits."""

    def __init__(self, audit_dir: str = "./audit_logs"):
        self._audit_dir = audit_dir
        self._query = AuditQuery(audit_dir)

    def refresh(self) -> None:
        """Force reload records from disk."""
        self._query.refresh()

    # ========================================================================
    # DECISIONS LIST (paginated)
    # ========================================================================

    def get_decisions(
        self,
        page: int = 1,
        limit: int = 20,
        result: Optional[str] = None,
        after: Optional[str] = None,
        before: Optional[str] = None,
        action: Optional[str] = None,
        agent: Optional[str] = None,
        tier: str = "free",
    ) -> Dict[str, Any]:
        """Get paginated decision list with tier-based filtering."""
        tier_config = TIER_LIMITS.get(tier, TIER_LIMITS["free"])

        # Apply tier date limit
        effective_after = after
        if tier_config["max_days"] is not None:
            cutoff = datetime.now(timezone.utc) - timedelta(days=tier_config["max_days"])
            cutoff_str = cutoff.strftime("%Y-%m-%dT%H:%M:%SZ")
            if effective_after is None or effective_after < cutoff_str:
                effective_after = cutoff_str

        records = self._query.filter(
            result=result,
            after=effective_after,
            before=before,
            action=action,
        )

        # Filter by agent name
        if agent:
            records = [r for r in records if r.agent.name == agent]

        # Apply tier record limit
        max_records = tier_config["max_records"]
        if max_records is not None:
            records = records[:max_records]

        total = len(records)
        total_pages = max(1, math.ceil(total / limit))
        start = (page - 1) * limit
        end = start + limit
        page_records = records[start:end]

        return {
            "items": [self._summarize(r) for r in page_records],
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
        }

    # ========================================================================
    # SINGLE DECISION
    # ========================================================================

    def get_decision(self, decision_id: str, tier: str = "free") -> Dict[str, Any]:
        """Get a single decision. Free: summary. Pro+: full detail."""
        record = load_record(decision_id, audit_dir=self._audit_dir)
        tier_config = TIER_LIMITS.get(tier, TIER_LIMITS["free"])

        if tier_config["full_detail"]:
            return record.to_dict()
        else:
            return self._summarize(record)

    # ========================================================================
    # STATS
    # ========================================================================

    def get_stats(self, tier: str = "free", last_days: Optional[int] = None) -> Dict[str, Any]:
        """Get aggregate stats with tier-based date window."""
        tier_config = TIER_LIMITS.get(tier, TIER_LIMITS["free"])

        if last_days is None:
            last_days = tier_config["max_days"]

        stats = self._query.stats(last_days=last_days)
        return stats.to_dict()

    # ========================================================================
    # VIOLATIONS
    # ========================================================================

    def get_violations(self, n: int = 10, tier: str = "free") -> List[Dict[str, Any]]:
        """Get top N constraint violations."""
        tier_config = TIER_LIMITS.get(tier, TIER_LIMITS["free"])

        records = None
        if tier_config["max_days"] is not None:
            cutoff = datetime.now(timezone.utc) - timedelta(days=tier_config["max_days"])
            cutoff_str = cutoff.strftime("%Y-%m-%dT%H:%M:%SZ")
            records = self._query.filter(after=cutoff_str)

        violations = self._query.top_violations(n=n, records=records)
        return [{"constraint": name, "count": count} for name, count in violations]

    # ========================================================================
    # AGENT STATS (Feature 3 — Multi-Agent)
    # ========================================================================

    def get_agent_stats(self, tier: str = "free") -> List[Dict[str, Any]]:
        """Get per-agent statistics."""
        tier_config = TIER_LIMITS.get(tier, TIER_LIMITS["free"])
        records = self._query.filter()

        # Apply tier date limit
        if tier_config["max_days"] is not None:
            cutoff = datetime.now(timezone.utc) - timedelta(days=tier_config["max_days"])
            cutoff_str = cutoff.strftime("%Y-%m-%dT%H:%M:%SZ")
            records = [r for r in records if r.timestamp >= cutoff_str]

        # Group by agent name
        agents: Dict[str, Dict[str, Any]] = {}
        for r in records:
            name = r.agent.name
            if name not in agents:
                agents[name] = {"total": 0, "allowed": 0, "blocked": 0, "latency_sum": 0.0}
            agents[name]["total"] += 1
            if r.decision.result == "ALLOWED":
                agents[name]["allowed"] += 1
            elif r.decision.result == "BLOCKED":
                agents[name]["blocked"] += 1
            agents[name]["latency_sum"] += r.performance.total_duration_ms

        result = []
        for name, stats in sorted(agents.items()):
            result.append({
                "name": name,
                "total": stats["total"],
                "allowed": stats["allowed"],
                "blocked": stats["blocked"],
                "avg_latency_ms": round(stats["latency_sum"] / stats["total"], 2) if stats["total"] > 0 else 0,
            })
        return result

    # ========================================================================
    # EXPORT
    # ========================================================================

    def export_records(
        self,
        format: str = "json",
        tier: str = "free",
        last_days: Optional[int] = None,
        result: Optional[str] = None,
    ) -> Any:
        """Export audit records as JSON-serializable data."""
        tier_config = TIER_LIMITS.get(tier, TIER_LIMITS["free"])

        effective_after = None
        days = last_days or tier_config.get("max_days")
        if days is not None:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
            effective_after = cutoff.strftime("%Y-%m-%dT%H:%M:%SZ")

        records = self._query.filter(result=result, after=effective_after)

        max_records = tier_config["max_records"]
        if max_records is not None:
            records = records[:max_records]

        if format == "compact":
            return [r.to_compact() for r in records]
        elif format == "stats":
            stats = self._query.stats(last_days=days)
            return stats.to_dict()
        else:  # json
            return [r.to_dict() for r in records]

    # ========================================================================
    # EXPLANATION (Art. 86)
    # ========================================================================

    def get_explanation_html(self, decision_id: str) -> str:
        """Generate Art. 86 HTML explanation for a single decision."""
        record = load_record(decision_id, audit_dir=self._audit_dir)
        return generate_html(record)

    # ========================================================================
    # HELPERS
    # ========================================================================

    @staticmethod
    def _summarize(record: DecisionAuditRecord) -> Dict[str, Any]:
        """Compact summary for free tier / list views."""
        violations = []
        for attempt in record.reasoning.attempts:
            for c in attempt.candidates:
                if c.policy_evaluation and c.policy_evaluation.violations:
                    for v in c.policy_evaluation.violations:
                        violations.append({
                            "constraint": v.constraint,
                            "explanation": v.explanation,
                        })

        return {
            "decision_id": record.decision_id,
            "timestamp": record.timestamp,
            "result": record.decision.result,
            "action": record.decision.action_taken,
            "policy_file": record.decision.policy_file,
            "duration_ms": record.performance.total_duration_ms,
            "total_candidates": record.reasoning.total_candidates,
            "total_attempts": record.reasoning.total_attempts,
            "agent_name": record.agent.name,
            "model": record.agent.model,
            "violations": violations,
        }
