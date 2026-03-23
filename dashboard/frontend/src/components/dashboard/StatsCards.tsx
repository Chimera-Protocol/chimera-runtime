"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Activity, ShieldCheck, ShieldX, Clock, AlertTriangle } from "lucide-react";
import type { AuditStats } from "@/lib/types";

interface StatsCardsProps {
  stats: AuditStats | null;
  loading?: boolean;
}

export function StatsCards({ stats, loading }: StatsCardsProps) {
  const cards = [
    {
      label: "Total Decisions",
      value: stats?.total_decisions ?? 0,
      icon: Activity,
      color: "text-[#6366f1]",
      bg: "bg-[#6366f1]/10",
    },
    {
      label: "Allowed",
      value: stats?.allowed_count ?? 0,
      icon: ShieldCheck,
      color: "text-[#22c55e]",
      bg: "bg-[#22c55e]/10",
      sub: stats ? `${((stats.allow_rate ?? 0) * 100).toFixed(1)}%` : undefined,
    },
    {
      label: "Blocked",
      value: stats?.blocked_count ?? 0,
      icon: ShieldX,
      color: "text-[#ef4444]",
      bg: "bg-[#ef4444]/10",
      sub: stats ? `${((stats.block_rate ?? 0) * 100).toFixed(1)}%` : undefined,
    },
    {
      label: "Avg Latency",
      value: stats ? `${(stats.avg_duration_ms ?? stats.avg_latency_ms ?? 0).toFixed(1)}ms` : "0ms",
      icon: Clock,
      color: "text-[#f59e0b]",
      bg: "bg-[#f59e0b]/10",
    },
    {
      label: "Violations",
      value: stats?.total_violations ?? 0,
      icon: AlertTriangle,
      color: "text-[#ef4444]",
      bg: "bg-[#ef4444]/10",
    },
  ];

  if (loading) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        {Array.from({ length: 5 }).map((_, i) => (
          <Card key={i} className="border-[#1e1e2e] bg-[#111119]">
            <CardContent className="p-6">
              <div className="h-16 animate-pulse rounded bg-[#1e1e2e]" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
      {cards.map((card) => (
        <Card
          key={card.label}
          className="border-[#1e1e2e] bg-[#111119] hover:border-[#2e2e3e] transition-colors"
        >
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-[#71717a]">{card.label}</p>
                <p className="mt-1 text-2xl font-bold text-white">
                  {card.value}
                </p>
                {card.sub && (
                  <p className={`mt-0.5 text-xs ${card.color}`}>{card.sub}</p>
                )}
              </div>
              <div className={`rounded-lg p-2.5 ${card.bg}`}>
                <card.icon className={`h-5 w-5 ${card.color}`} />
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
