"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { ProGate } from "@/components/pro-gate";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer, CartesianGrid, Legend,
} from "recharts";
import { BarChart3, TrendingUp, Zap, Lock, DollarSign, Flame, Calendar } from "lucide-react";
import type { TrendDataPoint, HeatmapCell } from "@/lib/types";

const DATE_OPTIONS = [
  { label: "7d", value: 7 },
  { label: "14d", value: 14 },
  { label: "30d", value: 30 },
  { label: "60d", value: 60 },
  { label: "90d", value: 90 },
];

const VIOLATION_COLORS = ["#6366f1", "#ef4444", "#f59e0b", "#22c55e", "#818cf8", "#f472b6"];

export default function AnalyticsPage() {
  const { user } = useAuth();
  const [lastDays, setLastDays] = useState(30);
  const [trend, setTrend] = useState<TrendDataPoint[]>([]);
  const [heatmap, setHeatmap] = useState<HeatmapCell[]>([]);
  const [violationTrend, setViolationTrend] = useState<
    Array<{ date: string; violations: Record<string, number> }>
  >([]);
  const [costData, setCostData] = useState<{
    total_estimated_cost_usd: number;
    average_cost_per_decision: number;
    cost_by_model: Record<string, number>;
    cost_by_day: Array<{ date: string; cost: number; decisions: number }>;
    total_decisions: number;
  } | null>(null);
  const [performance, setPerformance] = useState<{
    total_duration_ms: { mean: number; p95: number; median: number; count: number };
    llm_duration_ms: { mean: number; p95: number; median: number; count: number };
    policy_evaluation_ms: { mean: number; p95: number; median: number; count: number };
  } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchAnalytics() {
      setLoading(true);
      try {
        const [trendData, perfData, heatmapData, violData, costResult] =
          await Promise.all([
            api.getTrend("daily", lastDays),
            api.getPerformance(lastDays),
            api.getHeatmap(lastDays),
            api.getViolationTrend(lastDays),
            api.getCostEstimate(lastDays),
          ]);
        setTrend(trendData.data);
        setPerformance(perfData);
        setHeatmap(heatmapData.data);
        setViolationTrend(violData.data);
        setCostData(costResult);
      } catch (err) {
        console.error("Failed to fetch analytics:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchAnalytics();
  }, [lastDays]);

  const tooltipStyle = {
    contentStyle: {
      backgroundColor: "#111119",
      border: "1px solid #1e1e2e",
      borderRadius: 8,
      color: "#e4e4e7",
      fontSize: 12,
    },
  };

  return (
    <div className="space-y-6">
      {/* Header + Date Range */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <BarChart3 className="h-6 w-6 text-[#6366f1]" />
            Analytics
          </h1>
          <p className="mt-1 text-sm text-[#71717a]">
            Decision trends, performance, violation patterns, and cost estimates
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Calendar className="h-4 w-4 text-[#71717a]" />
          <div className="flex rounded-lg border border-[#1e1e2e] overflow-hidden">
            {DATE_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                onClick={() => setLastDays(opt.value)}
                className={`px-3 py-1.5 text-xs font-medium transition-colors ${
                  lastDays === opt.value
                    ? "bg-[#6366f1] text-white"
                    : "bg-[#111119] text-[#71717a] hover:text-white"
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
          <Badge variant="outline" className="border-[#6366f1]/30 bg-[#6366f1]/10 text-[#818cf8]">
            PRO
          </Badge>
        </div>
      </div>

      {/* 1. Decision Trend */}
      <Card className="border-[#1e1e2e] bg-[#111119]">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-[#6366f1]" />
            Decision Trend ({lastDays} days)
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="h-80 animate-pulse rounded bg-[#1e1e2e]" />
          ) : trend.length > 0 ? (
            <ResponsiveContainer width="100%" height={320}>
              <LineChart data={trend}>
                <CartesianGrid stroke="#1e1e2e" strokeDasharray="3 3" />
                <XAxis dataKey="date" tick={{ fill: "#71717a", fontSize: 11 }} tickFormatter={(v) => v.slice(5)} />
                <YAxis tick={{ fill: "#71717a", fontSize: 11 }} />
                <Tooltip {...tooltipStyle} />
                <Legend wrapperStyle={{ color: "#71717a", fontSize: 12 }} />
                <Line type="monotone" dataKey="ALLOWED" stroke="#22c55e" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="BLOCKED" stroke="#ef4444" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="total" stroke="#6366f1" strokeWidth={2} strokeDasharray="5 5" dot={false} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-80 flex items-center justify-center text-[#71717a]">No trend data available.</div>
          )}
        </CardContent>
      </Card>

      {/* 2. Block Rate Heatmap */}
      <ProGate feature="Block Rate Heatmap">
        <Card className="border-[#1e1e2e] bg-[#111119]">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Flame className="h-5 w-5 text-[#ef4444]" />
              Block Rate Heatmap
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? <div className="h-48 animate-pulse rounded bg-[#1e1e2e]" /> : <HeatmapGrid data={heatmap} />}
          </CardContent>
        </Card>
      </ProGate>

      {/* 3. Violation Trend */}
      <ProGate feature="Violation Trend">
        <Card className="border-[#1e1e2e] bg-[#111119]">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Zap className="h-5 w-5 text-[#f59e0b]" />
              Violation Frequency
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? <div className="h-64 animate-pulse rounded bg-[#1e1e2e]" /> : (
              <ViolationTrendChart data={violationTrend} tooltipStyle={tooltipStyle} />
            )}
          </CardContent>
        </Card>
      </ProGate>

      {/* 4. Performance */}
      <div className="grid gap-4 sm:grid-cols-3">
        {performance && (
          <>
            <PerfCard label="Total Latency" mean={performance.total_duration_ms.mean} p95={performance.total_duration_ms.p95} median={performance.total_duration_ms.median} count={performance.total_duration_ms.count} color="#6366f1" />
            <PerfCard label="LLM Duration" mean={performance.llm_duration_ms.mean} p95={performance.llm_duration_ms.p95} median={performance.llm_duration_ms.median} count={performance.llm_duration_ms.count} color="#f59e0b" />
            <PerfCard label="Policy Evaluation" mean={performance.policy_evaluation_ms.mean} p95={performance.policy_evaluation_ms.p95} median={performance.policy_evaluation_ms.median} count={performance.policy_evaluation_ms.count} color="#22c55e" />
          </>
        )}
      </div>

      {/* 5. LLM Cost Estimator */}
      <ProGate feature="LLM Cost Estimator">
        <Card className="border-[#1e1e2e] bg-[#111119]">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <DollarSign className="h-5 w-5 text-[#22c55e]" />
              LLM Cost Estimator
              <Badge variant="outline" className="border-[#71717a]/30 text-[#71717a] text-[10px]">ESTIMATE</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading || !costData ? <div className="h-48 animate-pulse rounded bg-[#1e1e2e]" /> : (
              <div className="space-y-6">
                <div className="grid gap-4 sm:grid-cols-3">
                  <StatBox label="Total Estimated" value={`$${costData.total_estimated_cost_usd.toFixed(2)}`} color="#22c55e" />
                  <StatBox label="Per Decision" value={`$${costData.average_cost_per_decision.toFixed(4)}`} color="#818cf8" />
                  <StatBox label="Decisions" value={String(costData.total_decisions)} color="#e4e4e7" />
                </div>
                {Object.keys(costData.cost_by_model).length > 0 && (
                  <div>
                    <p className="text-xs text-[#71717a] mb-2">Cost by Model</p>
                    <div className="space-y-2">
                      {Object.entries(costData.cost_by_model).map(([model, cost]) => {
                        const pct = costData.total_estimated_cost_usd > 0 ? (cost / costData.total_estimated_cost_usd) * 100 : 0;
                        return (
                          <div key={model} className="flex items-center gap-3">
                            <span className="text-xs font-mono text-[#a1a1aa] w-32 truncate">{model}</span>
                            <div className="flex-1 h-2 rounded-full bg-[#1e1e2e] overflow-hidden">
                              <div className="h-full rounded-full bg-[#6366f1]" style={{ width: `${pct}%` }} />
                            </div>
                            <span className="text-xs font-mono text-[#e4e4e7] w-16 text-right">${cost.toFixed(3)}</span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
                {costData.cost_by_day.length > 0 && (
                  <ResponsiveContainer width="100%" height={200}>
                    <LineChart data={costData.cost_by_day}>
                      <CartesianGrid stroke="#1e1e2e" strokeDasharray="3 3" />
                      <XAxis dataKey="date" tick={{ fill: "#71717a", fontSize: 10 }} tickFormatter={(v) => v.slice(5)} />
                      <YAxis tick={{ fill: "#71717a", fontSize: 10 }} tickFormatter={(v) => `$${v}`} />
                      <Tooltip {...tooltipStyle} formatter={(v) => [`$${Number(v).toFixed(4)}`, "Cost"]} />
                      <Line type="monotone" dataKey="cost" stroke="#22c55e" strokeWidth={2} dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </ProGate>

      {/* Enterprise Teaser */}
      <Card className="border-[#f59e0b]/20 bg-[#f59e0b]/5">
        <CardContent className="flex items-center justify-between py-4">
          <div className="flex items-center gap-3">
            <Lock className="h-5 w-5 text-[#f59e0b]" />
            <div>
              <p className="text-sm font-medium text-white">Real-Time WebSocket Monitoring</p>
              <p className="text-xs text-[#71717a]">Enterprise: live decision feed, compliance calendar, SIEM integration.</p>
            </div>
          </div>
          <Badge variant="outline" className="border-[#f59e0b]/30 text-[#f59e0b]">ENTERPRISE</Badge>
        </CardContent>
      </Card>
    </div>
  );
}

/* ── Sub Components ────────────────────────────────────────────── */

function HeatmapGrid({ data }: { data: HeatmapCell[] }) {
  const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
  const hours = Array.from({ length: 24 }, (_, i) => i);
  const cellMap = new Map<string, HeatmapCell>();
  for (const cell of data) cellMap.set(`${cell.day_index}-${cell.hour}`, cell);

  return (
    <div className="overflow-x-auto">
      <div className="min-w-[600px]">
        <div className="flex ml-10 mb-1">
          {hours.filter((_, i) => i % 3 === 0).map((h) => (
            <span key={h} className="text-[10px] text-[#71717a]" style={{ width: `${100/8}%` }}>{h}:00</span>
          ))}
        </div>
        {days.map((day, dayIdx) => (
          <div key={day} className="flex items-center gap-1 mb-0.5">
            <span className="text-[10px] text-[#71717a] w-8 text-right">{day}</span>
            <div className="flex flex-1 gap-px">
              {hours.map((hour) => {
                const cell = cellMap.get(`${dayIdx}-${hour}`);
                const rate = cell?.block_rate || 0;
                const total = cell?.total || 0;
                return (
                  <div key={hour}
                    className="flex-1 h-6 rounded-sm cursor-pointer hover:ring-1 hover:ring-white/30"
                    style={{ backgroundColor: total === 0 ? "#1e1e2e" : `rgba(239, 68, 68, ${Math.max(0.1, rate)})` }}
                    title={`${day} ${hour}:00 — ${(rate * 100).toFixed(0)}% blocked (${cell?.blocked || 0}/${total})`}
                  />
                );
              })}
            </div>
          </div>
        ))}
        <div className="flex items-center justify-end gap-2 mt-2">
          <span className="text-[10px] text-[#71717a]">0%</span>
          {[0.1, 0.25, 0.5, 0.75, 1].map((v) => (
            <div key={v} className="w-4 h-3 rounded-sm" style={{ backgroundColor: `rgba(239, 68, 68, ${v})` }} />
          ))}
          <span className="text-[10px] text-[#71717a]">100%</span>
        </div>
      </div>
    </div>
  );
}

function ViolationTrendChart({ data, tooltipStyle }: {
  data: Array<{ date: string; violations: Record<string, number> }>;
  tooltipStyle: Record<string, unknown>;
}) {
  if (!data || data.length === 0) {
    return <div className="h-64 flex items-center justify-center text-[#71717a]">No violation data available.</div>;
  }
  const constraintSet = new Set<string>();
  for (const d of data) for (const k of Object.keys(d.violations)) constraintSet.add(k);
  const constraints = Array.from(constraintSet);
  const chartData = data.map((d) => ({ date: d.date, ...d.violations }));

  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={chartData}>
        <CartesianGrid stroke="#1e1e2e" strokeDasharray="3 3" />
        <XAxis dataKey="date" tick={{ fill: "#71717a", fontSize: 10 }} tickFormatter={(v) => v.slice(5)} />
        <YAxis tick={{ fill: "#71717a", fontSize: 10 }} />
        <Tooltip contentStyle={(tooltipStyle as Record<string, Record<string, unknown>>).contentStyle} />
        <Legend wrapperStyle={{ color: "#71717a", fontSize: 11 }} />
        {constraints.map((c, i) => (
          <Bar key={c} dataKey={c} stackId="a" fill={VIOLATION_COLORS[i % VIOLATION_COLORS.length]} />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}

function PerfCard({ label, mean, p95, median, count, color }: {
  label: string; mean: number; p95: number; median: number; count: number; color: string;
}) {
  return (
    <Card className="border-[#1e1e2e] bg-[#111119]">
      <CardContent className="p-4">
        <div className="flex items-center gap-2 mb-3">
          <Zap className="h-4 w-4" style={{ color }} />
          <span className="text-sm text-[#71717a]">{label}</span>
        </div>
        <p className="text-2xl font-bold text-white">{mean.toFixed(1)}ms</p>
        <div className="mt-2 grid grid-cols-3 gap-2 text-xs">
          <div><span className="text-[#71717a]">Median</span><p className="text-[#e4e4e7] font-mono">{median.toFixed(1)}ms</p></div>
          <div><span className="text-[#71717a]">P95</span><p className="text-[#e4e4e7] font-mono">{p95.toFixed(1)}ms</p></div>
          <div><span className="text-[#71717a]">Count</span><p className="text-[#e4e4e7] font-mono">{count}</p></div>
        </div>
      </CardContent>
    </Card>
  );
}

function StatBox({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div className="rounded-lg border border-[#1e1e2e] bg-[#0a0a0f] p-4 text-center">
      <p className="text-xs text-[#71717a]">{label}</p>
      <p className="text-2xl font-bold" style={{ color }}>{value}</p>
    </div>
  );
}
