"""
Audit Service — wraps chimera_runtime.audit for the dashboard API.

Supports both legacy mode (all records from filesystem) and
user-isolated mode (records from StorageBackend per user_id).
Pro+ tier only for cloud pipeline; free tier is local-only.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from chimera_runtime.audit.query import AuditQuery, AuditStats
from chimera_runtime.audit.storage import load_record, load_all_records
from chimera_runtime.audit.html_report import generate_html
from chimera_runtime.models import DecisionAuditRecord

from .storage_service import StorageBackend


# Tier-based limits for the cloud dashboard UI only.
# The local Python lib (pip install chimera-runtime) is NEVER limited.
TIER_LIMITS = {
    "free": {"max_days": 7, "max_records": 100, "full_detail": False},
    "pro": {"max_days": 90, "max_records": 10000, "full_detail": True},
    "enterprise": {"max_days": None, "max_records": None, "full_detail": True},
}


class AuditService:
    """Wraps AuditQuery with pagination, user isolation, and tier-based limits."""

    def __init__(self, audit_dir: str = "./audit_logs", storage: Optional[StorageBackend] = None):
        self._audit_dir = audit_dir
        self._storage = storage
        # Legacy query engine (for backward compat when no storage backend)
        self._query = AuditQuery(audit_dir)

    def refresh(self) -> None:
        """Force reload records from disk (legacy mode only)."""
        self._query.refresh()

    def _load_user_records(self, user_id: Optional[int] = None) -> List[DecisionAuditRecord]:
        """Load records for a specific user from storage backend, or all records in legacy mode."""
        if user_id is not None and self._storage is not None:
            # User-isolated mode: load from storage backend
            raw_records = self._storage.list_records(user_id)
            records = []
            for raw in raw_records:
                try:
                    records.append(DecisionAuditRecord.from_dict(raw))
                except Exception:
                    continue
            return records
        else:
            # Legacy mode: load all from filesystem
            self._query.refresh()
            return self._query.filter()

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
        user_id: Optional[int] = None,
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

        records = self._load_user_records(user_id)

        # Apply filters
        if result:
            records = [r for r in records if r.decision.result == result]
        if effective_after:
            records = [r for r in records if r.timestamp >= effective_after]
        if before:
            records = [r for r in records if r.timestamp <= before]
        if action:
            records = [r for r in records if action.lower() in (r.decision.action_taken or "").lower()]
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

    def get_decision(self, decision_id: str, tier: str = "free", user_id: Optional[int] = None) -> Dict[str, Any]:
        """Get a single decision. Free: summary. Pro+: full detail."""
        tier_config = TIER_LIMITS.get(tier, TIER_LIMITS["free"])

        if user_id is not None and self._storage is not None:
            raw = self._storage.load(user_id, decision_id)
            record = DecisionAuditRecord.from_dict(raw)
        else:
            record = load_record(decision_id, audit_dir=self._audit_dir)

        if tier_config["full_detail"]:
            return record.to_dict()
        else:
            return self._summarize(record)

    # ========================================================================
    # STATS
    # ========================================================================

    def get_stats(self, tier: str = "free", last_days: Optional[int] = None, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Get aggregate stats with tier-based date window."""
        tier_config = TIER_LIMITS.get(tier, TIER_LIMITS["free"])

        if last_days is None:
            last_days = tier_config["max_days"]

        records = self._load_user_records(user_id)

        # Apply date filter
        if last_days is not None:
            cutoff = datetime.now(timezone.utc) - timedelta(days=last_days)
            cutoff_str = cutoff.strftime("%Y-%m-%dT%H:%M:%SZ")
            records = [r for r in records if r.timestamp >= cutoff_str]

        # Compute stats manually
        total = len(records)
        allowed = sum(1 for r in records if r.decision.result == "ALLOWED")
        blocked = sum(1 for r in records if r.decision.result == "BLOCKED")
        overrides = sum(1 for r in records if r.decision.result == "HUMAN_OVERRIDE")
        interrupted = sum(1 for r in records if r.decision.result == "INTERRUPTED")

        latencies = [r.performance.total_duration_ms for r in records]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0

        violations = {}
        for r in records:
            for attempt in r.reasoning.attempts:
                for c in attempt.candidates:
                    if c.policy_evaluation and c.policy_evaluation.violations:
                        for v in c.policy_evaluation.violations:
                            violations[v.constraint] = violations.get(v.constraint, 0) + 1

        allow_rate = round(allowed / total, 4) if total > 0 else 0
        block_rate_val = round(blocked / total, 4) if total > 0 else 0

        return {
            "total_decisions": total,
            "allowed": allowed,
            "allowed_count": allowed,
            "blocked": blocked,
            "blocked_count": blocked,
            "human_overrides": overrides,
            "human_override_count": overrides,
            "interrupted": interrupted,
            "interrupted_count": interrupted,
            "allow_rate": allow_rate,
            "block_rate": block_rate_val,
            "avg_latency_ms": round(avg_latency, 2),
            "avg_duration_ms": round(avg_latency, 2),
            "total_violations": sum(violations.values()),
            "top_violations": sorted(violations.items(), key=lambda x: -x[1])[:5],
            "last_days": last_days,
        }

    # ========================================================================
    # VIOLATIONS
    # ========================================================================

    def get_violations(self, n: int = 10, tier: str = "free", user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get top N constraint violations."""
        tier_config = TIER_LIMITS.get(tier, TIER_LIMITS["free"])

        records = self._load_user_records(user_id)

        if tier_config["max_days"] is not None:
            cutoff = datetime.now(timezone.utc) - timedelta(days=tier_config["max_days"])
            cutoff_str = cutoff.strftime("%Y-%m-%dT%H:%M:%SZ")
            records = [r for r in records if r.timestamp >= cutoff_str]

        violations: Dict[str, int] = {}
        for r in records:
            for attempt in r.reasoning.attempts:
                for c in attempt.candidates:
                    if c.policy_evaluation and c.policy_evaluation.violations:
                        for v in c.policy_evaluation.violations:
                            violations[v.constraint] = violations.get(v.constraint, 0) + 1

        sorted_violations = sorted(violations.items(), key=lambda x: -x[1])[:n]
        return [{"constraint": name, "count": count} for name, count in sorted_violations]

    # ========================================================================
    # AGENT STATS (Feature 3 — Multi-Agent)
    # ========================================================================

    def get_agent_stats(self, tier: str = "free", user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get per-agent statistics."""
        tier_config = TIER_LIMITS.get(tier, TIER_LIMITS["free"])
        records = self._load_user_records(user_id)

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
        user_id: Optional[int] = None,
    ) -> Any:
        """Export audit records as JSON-serializable data."""
        tier_config = TIER_LIMITS.get(tier, TIER_LIMITS["free"])

        records = self._load_user_records(user_id)

        # Apply date filter
        days = last_days or tier_config.get("max_days")
        if days is not None:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
            cutoff_str = cutoff.strftime("%Y-%m-%dT%H:%M:%SZ")
            records = [r for r in records if r.timestamp >= cutoff_str]

        # Apply result filter
        if result:
            records = [r for r in records if r.decision.result == result]

        max_records = tier_config["max_records"]
        if max_records is not None:
            records = records[:max_records]

        if format == "compact":
            return [r.to_compact() for r in records]
        elif format == "stats":
            return self.get_stats(tier=tier, last_days=days, user_id=user_id)
        else:  # json
            return [r.to_dict() for r in records]

    # ========================================================================
    # EXPLANATION (Art. 86)
    # ========================================================================

    def get_explanation_html(self, decision_id: str, user_id: Optional[int] = None) -> str:
        """Generate Art. 86 HTML explanation for a single decision."""
        if user_id is not None and self._storage is not None:
            raw = self._storage.load(user_id, decision_id)
            record = DecisionAuditRecord.from_dict(raw)
        else:
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
