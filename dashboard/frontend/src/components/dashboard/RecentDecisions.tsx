"use client";

import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { DecisionSummary } from "@/lib/types";

const resultColors: Record<string, string> = {
  ALLOWED: "bg-[#22c55e]/10 text-[#22c55e] border-[#22c55e]/30",
  BLOCKED: "bg-[#ef4444]/10 text-[#ef4444] border-[#ef4444]/30",
  HUMAN_OVERRIDE: "bg-[#f59e0b]/10 text-[#f59e0b] border-[#f59e0b]/30",
  INTERRUPTED: "bg-[#6b7280]/10 text-[#6b7280] border-[#6b7280]/30",
};

interface RecentDecisionsProps {
  decisions: DecisionSummary[];
  loading?: boolean;
}

export function RecentDecisions({ decisions, loading }: RecentDecisionsProps) {
  if (loading) {
    return (
      <Card className="border-[#1e1e2e] bg-[#111119]">
        <CardHeader>
          <CardTitle className="text-white">Recent Decisions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="h-12 animate-pulse rounded bg-[#1e1e2e]" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="border-[#1e1e2e] bg-[#111119]">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-white">Recent Decisions</CardTitle>
        <Link
          href="/decisions"
          className="text-sm text-[#6366f1] hover:text-[#818cf8] transition-colors"
        >
          View all
        </Link>
      </CardHeader>
      <CardContent>
        {decisions.length === 0 ? (
          <p className="text-center text-[#71717a] py-8">
            No decisions recorded yet. Run your first agent to see data here.
          </p>
        ) : (
          <div className="space-y-2">
            {decisions.slice(0, 8).map((d) => (
              <Link
                key={d.decision_id}
                href={`/decisions/${d.decision_id}`}
                className="flex items-center justify-between rounded-lg border border-[#1e1e2e] bg-[#0a0a0f] px-4 py-3 hover:border-[#2e2e3e] transition-colors"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <Badge
                    variant="outline"
                    className={resultColors[d.result] || resultColors.INTERRUPTED}
                  >
                    {d.result}
                  </Badge>
                  <span className="text-sm text-white truncate">
                    {d.action}
                  </span>
                  {d.agent_name && (
                    <span className="text-xs text-[#818cf8] font-mono">
                      {d.agent_name}
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-4 shrink-0">
                  <span className="text-xs text-[#71717a] font-mono">
                    {(d.duration_ms ?? 0).toFixed(1)}ms
                  </span>
                  <span className="text-xs text-[#71717a]">
                    {formatTime(d.timestamp)}
                  </span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function formatTime(ts: string): string {
  try {
    const d = new Date(ts);
    return d.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    });
  } catch {
    return ts;
  }
}
