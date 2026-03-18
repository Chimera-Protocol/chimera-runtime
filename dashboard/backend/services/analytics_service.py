"""
Analytics Service — time-series aggregation over audit records.

Builds trend data, heatmaps, and performance distributions
from the existing DecisionAuditRecord data.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from chimera_runtime.audit.storage import load_all_records
from chimera_runtime.models import DecisionAuditRecord


class AnalyticsService:
    """Aggregation engine for dashboard charts."""

    def __init__(self, audit_dir: str = "./audit_logs"):
        self._audit_dir = audit_dir

    def _load_records(
        self, last_days: Optional[int] = None
    ) -> List[DecisionAuditRecord]:
        """Load and optionally filter records by date."""
        records = load_all_records(self._audit_dir)
        if last_days is not None:
            cutoff = datetime.now(timezone.utc) - timedelta(days=last_days)
            cutoff_str = cutoff.strftime("%Y-%m-%dT%H:%M:%SZ")
            records = [r for r in records if r.timestamp >= cutoff_str]
        return records

    # ========================================================================
    # DECISION TREND (line chart data)
    # ========================================================================

    def get_trend(
        self,
        granularity: str = "daily",
        last_days: int = 30,
    ) -> Dict[str, Any]:
        """Decision counts over time, grouped by result type."""
        records = self._load_records(last_days=last_days)

        buckets: Dict[str, Dict[str, int]] = defaultdict(
            lambda: {"ALLOWED": 0, "BLOCKED": 0, "HUMAN_OVERRIDE": 0, "INTERRUPTED": 0, "total": 0}
        )

        for r in records:
            key = self._bucket_key(r.timestamp, granularity)
            result = r.decision.result
            buckets[key][result] = buckets[key].get(result, 0) + 1
            buckets[key]["total"] += 1

        # Sort by date
        sorted_keys = sorted(buckets.keys())
        return {
            "granularity": granularity,
            "last_days": last_days,
            "data": [{"date": k, **buckets[k]} for k in sorted_keys],
        }

    # ========================================================================
    # BLOCK RATE HEATMAP (hour x day-of-week)
    # ========================================================================

    def get_heatmap(self, last_days: int = 30) -> Dict[str, Any]:
        """Block rate by hour-of-day and day-of-week."""
        records = self._load_records(last_days=last_days)

        # Matrix: [day_of_week][hour] -> {blocked, total}
        matrix: Dict[int, Dict[int, Dict[str, int]]] = defaultdict(
            lambda: defaultdict(lambda: {"blocked": 0, "total": 0})
        )

        for r in records:
            try:
                dt = datetime.fromisoformat(r.timestamp.replace("Z", "+00:00"))
                dow = dt.weekday()  # 0=Monday, 6=Sunday
                hour = dt.hour
                matrix[dow][hour]["total"] += 1
                if r.decision.result == "BLOCKED":
                    matrix[dow][hour]["blocked"] += 1
            except (ValueError, AttributeError):
                continue

        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        data = []
        for dow in range(7):
            for hour in range(24):
                cell = matrix[dow][hour]
                rate = cell["blocked"] / cell["total"] if cell["total"] > 0 else 0
                data.append({
                    "day": days[dow],
                    "day_index": dow,
                    "hour": hour,
                    "block_rate": round(rate, 4),
                    "total": cell["total"],
                    "blocked": cell["blocked"],
                })

        return {"last_days": last_days, "data": data}

    # ========================================================================
    # VIOLATION TREND
    # ========================================================================

    def get_violation_trend(self, last_days: int = 30) -> Dict[str, Any]:
        """Violation frequency over time."""
        records = self._load_records(last_days=last_days)

        buckets: Dict[str, Counter] = defaultdict(Counter)

        for r in records:
            key = self._bucket_key(r.timestamp, "daily")
            for attempt in r.reasoning.attempts:
                for c in attempt.candidates:
                    if c.policy_evaluation and c.policy_evaluation.violations:
                        for v in c.policy_evaluation.violations:
                            buckets[key][v.constraint] += 1

        sorted_keys = sorted(buckets.keys())
        return {
            "last_days": last_days,
            "data": [
                {"date": k, "violations": dict(buckets[k])}
                for k in sorted_keys
            ],
        }

    # ========================================================================
    # PERFORMANCE DISTRIBUTION
    # ========================================================================

    def get_performance(self, last_days: int = 30) -> Dict[str, Any]:
        """Latency distribution: total, llm, policy eval durations."""
        records = self._load_records(last_days=last_days)

        total_ms = []
        llm_ms = []
        policy_ms = []

        for r in records:
            perf = r.performance
            total_ms.append(perf.total_duration_ms)
            llm_ms.append(perf.llm_duration_ms)
            policy_ms.append(perf.policy_evaluation_ms)

        return {
            "last_days": last_days,
            "total_duration_ms": self._distribution_stats(total_ms),
            "llm_duration_ms": self._distribution_stats(llm_ms),
            "policy_evaluation_ms": self._distribution_stats(policy_ms),
            "raw": {
                "total": total_ms,
                "llm": llm_ms,
                "policy": policy_ms,
            },
        }

    # ========================================================================
    # HELPERS
    # ========================================================================

    # ========================================================================
    # LLM COST ESTIMATOR
    # ========================================================================

    COST_PER_SECOND: Dict[str, float] = {
        "gpt-4o": 0.005, "gpt-4o-mini": 0.0005, "gpt-4": 0.01,
        "gpt-3.5-turbo": 0.0003, "claude-3-opus": 0.015,
        "claude-sonnet-4-20250514": 0.003, "claude-3-haiku": 0.0005,
        "gemini-pro": 0.002, "gemini-1.5-pro": 0.003, "demo": 0.0,
    }

    def get_cost_estimate(self, last_days: int = 30) -> Dict[str, Any]:
        """Estimate LLM costs from audit records."""
        records = self._load_records(last_days=last_days)
        cost_by_model: Dict[str, float] = defaultdict(float)
        cost_by_day: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"cost": 0.0, "decisions": 0}
        )
        total_cost = 0.0
        for r in records:
            model = (r.agent.model or "unknown").lower()
            llm_sec = r.performance.llm_duration_ms / 1000.0
            rate = 0.001
            for key, val in self.COST_PER_SECOND.items():
                if key in model:
                    rate = val
                    break
            cost = llm_sec * rate
            cost_by_model[r.agent.model or "unknown"] += cost
            total_cost += cost
            day = self._bucket_key(r.timestamp, "daily")
            cost_by_day[day]["cost"] += cost
            cost_by_day[day]["decisions"] += 1

        n = len(records)
        return {
            "last_days": last_days,
            "total_estimated_cost_usd": round(total_cost, 4),
            "average_cost_per_decision": round(total_cost / n, 6) if n else 0,
            "cost_by_model": {k: round(v, 4) for k, v in sorted(cost_by_model.items(), key=lambda x: -x[1])},
            "cost_by_day": [
                {"date": d, "cost": round(cost_by_day[d]["cost"], 4), "decisions": cost_by_day[d]["decisions"]}
                for d in sorted(cost_by_day.keys())
            ],
            "total_decisions": n,
        }

    @staticmethod
    def _bucket_key(timestamp: str, granularity: str) -> str:
        """Convert ISO timestamp to bucket key."""
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return "unknown"

        if granularity == "hourly":
            return dt.strftime("%Y-%m-%dT%H:00")
        elif granularity == "weekly":
            # Start of week (Monday)
            start = dt - timedelta(days=dt.weekday())
            return start.strftime("%Y-%m-%d")
        else:  # daily
            return dt.strftime("%Y-%m-%d")

    @staticmethod
    def _distribution_stats(values: List[float]) -> Dict[str, Any]:
        """Compute distribution statistics."""
        if not values:
            return {"min": 0, "max": 0, "mean": 0, "median": 0, "p95": 0, "p99": 0, "count": 0}

        sorted_vals = sorted(values)
        n = len(sorted_vals)
        return {
            "min": round(sorted_vals[0], 3),
            "max": round(sorted_vals[-1], 3),
            "mean": round(sum(sorted_vals) / n, 3),
            "median": round(sorted_vals[n // 2], 3),
            "p95": round(sorted_vals[int(n * 0.95)], 3) if n > 1 else round(sorted_vals[0], 3),
            "p99": round(sorted_vals[int(n * 0.99)], 3) if n > 1 else round(sorted_vals[0], 3),
            "count": n,
        }
