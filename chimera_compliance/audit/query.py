"""
chimera-compliance — Audit Query

Query and aggregate audit records for reporting and compliance.

Usage:
    query = AuditQuery("./audit_logs")

    # Filter
    blocked = query.filter(result="BLOCKED")
    recent = query.filter(after="2026-01-01T00:00:00Z")

    # Stats
    stats = query.stats(last_days=30)
    stats.total_decisions      # 142
    stats.allowed_count        # 128
    stats.blocked_count        # 14
    stats.block_rate           # 0.0986

    # Top violations
    top = query.top_violations(n=5)
    # [("manager_approval_limit", 8), ("weekend_restriction", 3), ...]

    # Export
    query.export("./reports/audit_export.json", format="json")
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..models import DecisionAuditRecord
from .storage import load_all_records


# ============================================================================
# STATS DATACLASS
# ============================================================================

@dataclass
class AuditStats:
    """Aggregate statistics for a set of audit records."""
    total_decisions: int = 0
    allowed_count: int = 0
    blocked_count: int = 0
    human_override_count: int = 0
    interrupted_count: int = 0
    avg_duration_ms: float = 0.0
    avg_candidates_per_decision: float = 0.0
    avg_attempts_per_decision: float = 0.0
    total_violations: int = 0
    period_start: str = ""
    period_end: str = ""

    @property
    def block_rate(self) -> float:
        """Fraction of decisions that were blocked."""
        if self.total_decisions == 0:
            return 0.0
        return self.blocked_count / self.total_decisions

    @property
    def allow_rate(self) -> float:
        """Fraction of decisions that were allowed."""
        if self.total_decisions == 0:
            return 0.0
        return self.allowed_count / self.total_decisions

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_decisions": self.total_decisions,
            "allowed_count": self.allowed_count,
            "blocked_count": self.blocked_count,
            "human_override_count": self.human_override_count,
            "interrupted_count": self.interrupted_count,
            "block_rate": round(self.block_rate, 4),
            "allow_rate": round(self.allow_rate, 4),
            "avg_duration_ms": round(self.avg_duration_ms, 3),
            "avg_candidates_per_decision": round(self.avg_candidates_per_decision, 2),
            "avg_attempts_per_decision": round(self.avg_attempts_per_decision, 2),
            "total_violations": self.total_violations,
            "period_start": self.period_start,
            "period_end": self.period_end,
        }


# ============================================================================
# AUDIT QUERY
# ============================================================================

class AuditQuery:
    """
    Query engine for audit records.

    Loads all records from disk, then provides filter/stats/export.
    Records are cached on first access — call refresh() to reload.
    """

    def __init__(self, audit_dir: str = "./audit_logs"):
        self._audit_dir = audit_dir
        self._records: Optional[List[DecisionAuditRecord]] = None

    @property
    def records(self) -> List[DecisionAuditRecord]:
        """Lazy-load all records from disk."""
        if self._records is None:
            self._records = load_all_records(self._audit_dir)
        return self._records

    def refresh(self) -> None:
        """Force reload records from disk."""
        self._records = None

    # ========================================================================
    # FILTER
    # ========================================================================

    def filter(
        self,
        result: Optional[str] = None,
        after: Optional[str] = None,
        before: Optional[str] = None,
        policy_file: Optional[str] = None,
        action: Optional[str] = None,
    ) -> List[DecisionAuditRecord]:
        """
        Filter audit records by criteria.

        Args:
            result: Filter by decision result ("ALLOWED", "BLOCKED", etc.)
            after: Only records with timestamp >= this ISO datetime
            before: Only records with timestamp <= this ISO datetime
            policy_file: Only records using this policy file (substring match)
            action: Only records with this action_taken (substring match)

        Returns:
            Filtered list of records (newest first)
        """
        filtered = list(self.records)

        if result is not None:
            result_upper = result.upper()
            filtered = [r for r in filtered if r.decision.result == result_upper]

        if after is not None:
            filtered = [r for r in filtered if r.timestamp >= after]

        if before is not None:
            filtered = [r for r in filtered if r.timestamp <= before]

        if policy_file is not None:
            filtered = [r for r in filtered if policy_file in r.decision.policy_file]

        if action is not None:
            action_lower = action.lower()
            filtered = [r for r in filtered if action_lower in r.decision.action_taken.lower()]

        return filtered

    # ========================================================================
    # STATS
    # ========================================================================

    def stats(
        self,
        last_days: Optional[int] = None,
        records: Optional[List[DecisionAuditRecord]] = None,
    ) -> AuditStats:
        """
        Compute aggregate statistics.

        Args:
            last_days: If set, only include records from the last N days
            records: If set, compute stats on these records instead of all

        Returns:
            AuditStats with counts, rates, averages
        """
        if records is None:
            records = list(self.records)

        if last_days is not None:
            cutoff = datetime.now(timezone.utc) - timedelta(days=last_days)
            cutoff_str = cutoff.strftime("%Y-%m-%dT%H:%M:%S") + "Z"
            records = [r for r in records if r.timestamp >= cutoff_str]

        if not records:
            return AuditStats()

        allowed = sum(1 for r in records if r.decision.result == "ALLOWED")
        blocked = sum(1 for r in records if r.decision.result == "BLOCKED")
        overrides = sum(1 for r in records if r.decision.result == "HUMAN_OVERRIDE")
        interrupted = sum(1 for r in records if r.decision.result == "INTERRUPTED")

        durations = [r.performance.total_duration_ms for r in records]
        avg_duration = sum(durations) / len(durations) if durations else 0.0

        total_candidates = [r.reasoning.total_candidates for r in records]
        avg_candidates = sum(total_candidates) / len(total_candidates) if total_candidates else 0.0

        total_attempts = [r.reasoning.total_attempts for r in records]
        avg_attempts = sum(total_attempts) / len(total_attempts) if total_attempts else 0.0

        # Count violations across all records
        violation_count = 0
        for r in records:
            for attempt in r.reasoning.attempts:
                for c in attempt.candidates:
                    if c.policy_evaluation and c.policy_evaluation.violations:
                        violation_count += len(c.policy_evaluation.violations)

        timestamps = sorted(r.timestamp for r in records)

        return AuditStats(
            total_decisions=len(records),
            allowed_count=allowed,
            blocked_count=blocked,
            human_override_count=overrides,
            interrupted_count=interrupted,
            avg_duration_ms=avg_duration,
            avg_candidates_per_decision=avg_candidates,
            avg_attempts_per_decision=avg_attempts,
            total_violations=violation_count,
            period_start=timestamps[0] if timestamps else "",
            period_end=timestamps[-1] if timestamps else "",
        )

    # ========================================================================
    # TOP VIOLATIONS
    # ========================================================================

    def top_violations(
        self,
        n: int = 10,
        records: Optional[List[DecisionAuditRecord]] = None,
    ) -> List[Tuple[str, int]]:
        """
        Get the most frequently triggered constraint violations.

        Args:
            n: Number of top violations to return
            records: If set, analyze these records instead of all

        Returns:
            List of (constraint_name, count) tuples, most frequent first
        """
        if records is None:
            records = self.records

        counter: Counter = Counter()
        for r in records:
            for attempt in r.reasoning.attempts:
                for c in attempt.candidates:
                    if c.policy_evaluation and c.policy_evaluation.violations:
                        for v in c.policy_evaluation.violations:
                            counter[v.constraint] += 1

        return counter.most_common(n)

    # ========================================================================
    # EXPORT
    # ========================================================================

    def export(
        self,
        path: str,
        format: str = "json",
        records: Optional[List[DecisionAuditRecord]] = None,
    ) -> str:
        """
        Export audit records to a file.

        Requires PRO tier license.

        Args:
            path: Output file path
            format: "json" for full records, "compact" for compact format,
                    "stats" for statistics summary
            records: If set, export these records instead of all

        Returns:
            Path to the exported file

        Raises:
            TierUpgradeRequired: If license tier is below PRO
        """
        from ..licensing import check_tier, TierUpgradeRequired
        if not check_tier("pro"):
            raise TierUpgradeRequired(
                feature="audit export",
                required_tier="pro",
                current_tier="free",
            )

        if records is None:
            records = self.records

        out_path = Path(path)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        if format == "json":
            data = [r.to_dict() for r in records]
            out_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        elif format == "compact":
            data = [r.to_compact() for r in records]
            out_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        elif format == "stats":
            stats_data = self.stats(records=records).to_dict()
            violations = self.top_violations(n=20, records=records)
            stats_data["top_violations"] = [
                {"constraint": name, "count": count}
                for name, count in violations
            ]
            out_path.write_text(
                json.dumps(stats_data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        else:
            raise ValueError(f"Unknown export format: '{format}'. Use 'json', 'compact', or 'stats'.")

        return str(out_path)
