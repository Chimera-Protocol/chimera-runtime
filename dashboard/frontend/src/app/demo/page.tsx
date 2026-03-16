"use client";

import { useState } from "react";
import Link from "next/link";
import { AuthNav } from "@/components/layout/AuthNav";
import {
  Shield,
  ArrowRight,
  Brain,
  FileCheck,
  CheckCircle2,
  XCircle,
  FileText,
  BarChart3,
  Lock,
  ChevronDown,
  AlertTriangle,
  Play,
  Activity,
  Zap,
  TrendingUp,
  Clock,
  Eye,
  PauseCircle,
  PlayCircle,
  FlaskConical,
  Info,
} from "lucide-react";

// ── Pipeline Demo Steps ──────────────────────────────────────────

const pipelineSteps = [
  {
    id: 1,
    title: "Agent Request",
    subtitle: "AI agent receives a task",
    icon: Brain,
    color: "#818cf8",
  },
  {
    id: 2,
    title: "LLM Processing",
    subtitle: "Language model generates candidates",
    icon: Brain,
    color: "#f59e0b",
  },
  {
    id: 3,
    title: "Policy Evaluation",
    subtitle: "CSL policy checked with Z3 formal verification",
    icon: FileCheck,
    color: "#6366f1",
  },
  {
    id: 4,
    title: "Decision",
    subtitle: "Compliance guard makes final decision",
    icon: Shield,
    color: "#ef4444",
  },
  {
    id: 5,
    title: "Audit Record",
    subtitle: "Immutable compliance record generated",
    icon: FileText,
    color: "#22c55e",
  },
];

// ── Demo Scenarios ───────────────────────────────────────────────

const scenarios = {
  blocked: {
    label: "Blocked Transfer",
    request: "Transfer $500,000 via DIGITAL channel for tax optimization",
    params: { amount: 500000, role: "MANAGER", channel: "DIGITAL", department: "FINANCE", is_weekend: "NO", urgency: "LOW" },
    candidates: [
      { strategy: "Direct wire transfer via SWIFT", confidence: 0.82 },
      { strategy: "Staged transfer via intermediary", confidence: 0.65 },
      { strategy: "Internal ledger adjustment", confidence: 0.45 },
    ],
    constraints: [
      { name: "manager_approval_limit", status: "PASS", detail: "500,000 <= 500,000 limit" },
      { name: "single_channel_cap", status: "FAIL", detail: "500,000 > 300,000 DIGITAL cap" },
      { name: "analyst_no_spend", status: "SKIP", detail: "role != ANALYST" },
      { name: "weekend_freeze", status: "PASS", detail: "is_weekend = NO" },
      { name: "absolute_ceiling", status: "PASS", detail: "500,000 <= 1,000,000" },
    ],
    result: "BLOCKED" as const,
    reason: "single_channel_cap: Single DIGITAL channel transfer cannot exceed $300,000",
    violations: 1,
  },
  allowed: {
    label: "Approved Budget",
    request: "Approve $120,000 marketing budget across ALL channels",
    params: { amount: 120000, role: "DIRECTOR", channel: "ALL", department: "MARKETING", is_weekend: "NO", urgency: "MEDIUM" },
    candidates: [
      { strategy: "Multi-channel campaign allocation", confidence: 0.91 },
      { strategy: "Phased rollout with A/B testing", confidence: 0.78 },
    ],
    constraints: [
      { name: "director_approval_limit", status: "PASS", detail: "120,000 <= 500,000 limit" },
      { name: "single_channel_cap", status: "SKIP", detail: "channel = ALL (not single)" },
      { name: "analyst_no_spend", status: "SKIP", detail: "role != ANALYST" },
      { name: "weekend_freeze", status: "PASS", detail: "is_weekend = NO" },
      { name: "absolute_ceiling", status: "PASS", detail: "120,000 <= 1,000,000" },
    ],
    result: "ALLOWED" as const,
    reason: "All constraints satisfied — transaction approved",
    violations: 0,
  },
  weekend: {
    label: "Weekend Block",
    request: "Process $50,000 equipment purchase on Saturday",
    params: { amount: 50000, role: "VP", channel: "DIGITAL", department: "OPERATIONS", is_weekend: "YES", urgency: "LOW" },
    candidates: [
      { strategy: "Standard procurement workflow", confidence: 0.88 },
    ],
    constraints: [
      { name: "vp_approval_limit", status: "PASS", detail: "50,000 <= 750,000 limit" },
      { name: "single_channel_cap", status: "PASS", detail: "50,000 <= 300,000 cap" },
      { name: "weekend_freeze", status: "FAIL", detail: "is_weekend=YES but urgency != CRITICAL" },
      { name: "absolute_ceiling", status: "PASS", detail: "50,000 <= 1,000,000" },
    ],
    result: "BLOCKED" as const,
    reason: "weekend_freeze: No budget changes on weekends unless urgency is CRITICAL",
    violations: 1,
  },
};

type ScenarioKey = keyof typeof scenarios;

// ── Free Tier Demo Cards (mock data) ─────────────────────────────

const freeDemo = {
  stats: {
    total_decisions: 847,
    allowed: 612,
    blocked: 198,
    overridden: 37,
    block_rate: "23.4%",
    avg_latency_ms: 42.7,
  },
  recentDecisions: [
    { id: "dec_7a3f", result: "ALLOWED", action: "budget_approval", agent: "FinanceBot", duration: 38, time: "2m ago" },
    { id: "dec_8b2c", result: "BLOCKED", action: "wire_transfer", agent: "PaymentAgent", duration: 45, time: "5m ago" },
    { id: "dec_9c4d", result: "ALLOWED", action: "report_generate", agent: "AnalyticsBot", duration: 22, time: "12m ago" },
    { id: "dec_1e5f", result: "BLOCKED", action: "data_export", agent: "DataAgent", duration: 51, time: "18m ago" },
    { id: "dec_2f6g", result: "ALLOWED", action: "user_query", agent: "SupportBot", duration: 19, time: "25m ago" },
  ],
  compliance: {
    article_12: true,
    article_13: true,
    article_14: true,
    article_15: true,
    article_19: true,
    article_86: true,
  },
};

// ── Pro Tier Demo Data ───────────────────────────────────────────

const proDemo = {
  // 30-day trend data for a more impressive chart
  trendData: [
    { day: "Mar 1", allowed: 82, blocked: 14 },
    { day: "Mar 2", allowed: 95, blocked: 18 },
    { day: "Mar 3", allowed: 78, blocked: 12 },
    { day: "Mar 4", allowed: 110, blocked: 22 },
    { day: "Mar 5", allowed: 125, blocked: 28 },
    { day: "Mar 6", allowed: 118, blocked: 31 },
    { day: "Mar 7", allowed: 45, blocked: 8 },
    { day: "Mar 8", allowed: 92, blocked: 15 },
    { day: "Mar 9", allowed: 135, blocked: 34 },
    { day: "Mar 10", allowed: 148, blocked: 38 },
    { day: "Mar 11", allowed: 142, blocked: 29 },
    { day: "Mar 12", allowed: 156, blocked: 42 },
    { day: "Mar 13", allowed: 168, blocked: 45 },
    { day: "Mar 14", allowed: 52, blocked: 10 },
    { day: "Mar 15", allowed: 105, blocked: 19 },
    { day: "Mar 16", allowed: 175, blocked: 48 },
    { day: "Mar 17", allowed: 189, blocked: 55 },
    { day: "Mar 18", allowed: 162, blocked: 38 },
    { day: "Mar 19", allowed: 198, blocked: 62 },
    { day: "Mar 20", allowed: 210, blocked: 58 },
    { day: "Mar 21", allowed: 65, blocked: 12 },
    { day: "Mar 22", allowed: 145, blocked: 28 },
    { day: "Mar 23", allowed: 225, blocked: 65 },
    { day: "Mar 24", allowed: 238, blocked: 72 },
    { day: "Mar 25", allowed: 215, blocked: 55 },
    { day: "Mar 26", allowed: 245, blocked: 68 },
    { day: "Mar 27", allowed: 258, blocked: 75 },
    { day: "Mar 28", allowed: 72, blocked: 15 },
    { day: "Mar 29", allowed: 178, blocked: 42 },
    { day: "Mar 30", allowed: 275, blocked: 82 },
  ],
  heatmapData: [
    [2, 1, 0, 0, 0, 3, 5, 12, 18, 22, 25, 20, 15, 19, 24, 21, 18, 14, 8, 5, 3, 2, 1, 1],
    [1, 0, 0, 0, 1, 4, 8, 15, 21, 28, 30, 25, 18, 22, 27, 24, 20, 16, 10, 6, 4, 2, 1, 0],
    [0, 1, 0, 0, 0, 2, 6, 14, 20, 26, 28, 23, 17, 21, 26, 22, 19, 13, 9, 5, 3, 1, 0, 0],
  ],
  reasoningTrace: {
    decision_id: "dec_8b2c",
    result: "BLOCKED",
    agent: "PaymentAgent",
    action: "wire_transfer",
    llm_model: "gpt-4o",
    llm_duration_ms: 1247,
    policy_evaluation_ms: 0.08,
    total_duration_ms: 1289,
    candidates: [
      { strategy: "Direct SWIFT transfer", selected: true, confidence: 0.82 },
      { strategy: "ACH batch transfer", selected: false, confidence: 0.71 },
    ],
    violations: [
      { constraint: "single_channel_cap", explanation: "Amount $500,000 exceeds single channel cap of $300,000 for DIGITAL" },
    ],
    policy_hash: "sha256:9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
  },
  agents: [
    { name: "PaymentAgent", total: 234, allowed: 178, blocked: 56, halted: false },
    { name: "FinanceBot", total: 312, allowed: 289, blocked: 23, halted: false },
    { name: "DataAgent", total: 156, allowed: 98, blocked: 58, halted: true },
    { name: "SupportBot", total: 145, allowed: 142, blocked: 3, halted: false },
  ],
};

export default function DemoPage() {
  const [activeStep, setActiveStep] = useState(0);
  const [activeTab, setActiveTab] = useState<"pipeline" | "free" | "pro">("pipeline");
  const [scenario, setScenario] = useState<ScenarioKey>("blocked");

  const sc = scenarios[scenario];

  return (
    <div className="min-h-screen bg-[#0a0a0f]">
      {/* Nav */}
      <nav className="fixed top-0 left-0 right-0 z-50 border-b border-[#1e1e2e] bg-[#0a0a0f]/90 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
          <Link href="/" className="flex items-center gap-2">
            <Shield className="h-6 w-6 text-[#6366f1]" />
            <span className="text-lg font-bold text-white">Chimera.</span>
          </Link>
          <div className="flex items-center gap-4">
            <Link href="/docs" className="text-sm text-[#71717a] hover:text-white transition">
              Docs
            </Link>
            <AuthNav />
          </div>
        </div>
      </nav>

      <div className="mx-auto max-w-5xl px-6 pt-28 pb-20">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-white mb-3">
            Interactive Demo
          </h1>
          <p className="text-[#71717a] max-w-2xl mx-auto">
            Explore how Chimera Compliance works — from pipeline flow to dashboard features.
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="flex justify-center gap-2 mb-8">
          {[
            { key: "pipeline" as const, label: "Pipeline Flow", icon: Activity },
            { key: "free" as const, label: "Free Dashboard", icon: Eye },
            { key: "pro" as const, label: "Pro Dashboard", icon: Zap },
          ].map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`flex items-center gap-2 rounded-lg border px-4 py-2.5 text-sm transition ${
                  activeTab === tab.key
                    ? "border-[#6366f1] bg-[#6366f1]/10 text-[#818cf8]"
                    : "border-[#1e1e2e] text-[#71717a] hover:border-[#2e2e3e] hover:text-white"
                }`}
              >
                <Icon className="h-4 w-4" />
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* ══════════════ Pipeline Flow Tab ══════════════ */}
        {activeTab === "pipeline" && (
          <>
            {/* Scenario Selector */}
            <div className="flex justify-center gap-2 mb-6">
              {(Object.entries(scenarios) as [ScenarioKey, typeof scenarios.blocked][]).map(([key, s]) => (
                <button
                  key={key}
                  onClick={() => { setScenario(key); setActiveStep(0); }}
                  className={`rounded-lg border px-3 py-1.5 text-xs font-medium transition ${
                    scenario === key
                      ? s.result === "BLOCKED"
                        ? "border-[#ef4444]/40 bg-[#ef4444]/10 text-[#ef4444]"
                        : "border-[#22c55e]/40 bg-[#22c55e]/10 text-[#22c55e]"
                      : "border-[#1e1e2e] text-[#71717a] hover:border-[#2e2e3e]"
                  }`}
                >
                  {s.label}
                </button>
              ))}
            </div>

            {/* Timeline */}
            <div className="space-y-4">
              {pipelineSteps.map((step, i) => {
                const Icon = step.icon;
                const isActive = i === activeStep;
                const isPast = i < activeStep;

                return (
                  <div key={step.id}>
                    <button
                      onClick={() => setActiveStep(i)}
                      className={`w-full flex items-center gap-4 rounded-xl border p-4 transition ${
                        isActive
                          ? "border-[#6366f1]/50 bg-[#111119]"
                          : isPast
                          ? "border-[#1e1e2e] bg-[#111119]/50"
                          : "border-[#1e1e2e] bg-[#0a0a0f] hover:border-[#2e2e3e]"
                      }`}
                    >
                      <div
                        className="flex h-10 w-10 items-center justify-center rounded-full border shrink-0"
                        style={{
                          borderColor: isActive || isPast ? step.color : "#1e1e2e",
                          backgroundColor: isActive ? `${step.color}15` : "transparent",
                        }}
                      >
                        {isPast ? (
                          <CheckCircle2 className="h-5 w-5" style={{ color: step.color }} />
                        ) : (
                          <Icon className="h-5 w-5" style={{ color: isActive ? step.color : "#71717a" }} />
                        )}
                      </div>
                      <div className="flex-1 text-left">
                        <p className={`text-sm font-medium ${isActive ? "text-white" : "text-[#a1a1aa]"}`}>
                          Step {step.id}: {step.title}
                        </p>
                        <p className="text-xs text-[#71717a]">{step.subtitle}</p>
                      </div>
                      <ChevronDown
                        className={`h-4 w-4 text-[#71717a] transition ${isActive ? "rotate-180" : ""}`}
                      />
                    </button>

                    {isActive && (
                      <div className="mt-2 ml-14 rounded-xl border border-[#1e1e2e] bg-[#0d0d14] p-5 space-y-3">
                        {/* Step 1: Agent Request */}
                        {step.id === 1 && (
                          <>
                            <p className="text-sm text-[#e4e4e7] font-medium">&quot;{sc.request}&quot;</p>
                            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                              {Object.entries(sc.params).map(([k, v]) => (
                                <div key={k} className="rounded bg-black/30 px-3 py-1.5 font-mono text-xs">
                                  <span className="text-[#71717a]">{k}:</span>{" "}
                                  <span className="text-[#818cf8]">{String(v)}</span>
                                </div>
                              ))}
                            </div>
                          </>
                        )}

                        {/* Step 2: LLM Processing */}
                        {step.id === 2 && (
                          <div className="space-y-2">
                            {sc.candidates.map((c, j) => (
                              <div key={j} className="flex items-center justify-between rounded bg-black/30 px-3 py-2">
                                <span className="text-sm text-[#e4e4e7]">{c.strategy}</span>
                                <span className="text-xs text-[#f59e0b] font-mono">{(c.confidence * 100).toFixed(0)}%</span>
                              </div>
                            ))}
                          </div>
                        )}

                        {/* Step 3: Policy Evaluation */}
                        {step.id === 3 && (
                          <div className="space-y-2">
                            <p className="text-xs text-[#71717a]">Policy: <span className="text-[#818cf8]">GovernanceGuard</span></p>
                            {sc.constraints.map((c) => (
                              <div key={c.name} className="flex items-center justify-between rounded bg-black/30 px-3 py-2">
                                <span className="font-mono text-xs text-[#e4e4e7]">{c.name}</span>
                                <div className="flex items-center gap-2">
                                  <span className="text-[10px] text-[#71717a]">{c.detail}</span>
                                  {c.status === "PASS" ? (
                                    <CheckCircle2 className="h-4 w-4 text-[#22c55e]" />
                                  ) : c.status === "SKIP" ? (
                                    <span className="text-[10px] text-[#71717a]">N/A</span>
                                  ) : (
                                    <XCircle className="h-4 w-4 text-[#ef4444]" />
                                  )}
                                </div>
                              </div>
                            ))}
                          </div>
                        )}

                        {/* Step 4: Decision */}
                        {step.id === 4 && (
                          <div className="space-y-3">
                            <div className="flex items-center gap-2">
                              <span className={`inline-flex items-center rounded border px-2.5 py-1 text-xs font-medium ${
                                sc.result === "ALLOWED"
                                  ? "bg-[#22c55e]/10 border-[#22c55e]/30 text-[#22c55e]"
                                  : "bg-[#ef4444]/10 border-[#ef4444]/30 text-[#ef4444]"
                              }`}>
                                {sc.result}
                              </span>
                              <span className="text-xs text-[#71717a]">{sc.violations} violation{sc.violations !== 1 ? "s" : ""}</span>
                            </div>
                            <p className={`text-sm ${sc.result === "BLOCKED" ? "text-[#ef4444]/80" : "text-[#22c55e]/80"}`}>
                              {sc.reason}
                            </p>
                          </div>
                        )}

                        {/* Step 5: Audit Record */}
                        {step.id === 5 && (
                          <div className="space-y-1.5">
                            {[
                              { k: "decision_id", v: `dec_${Math.random().toString(36).slice(2, 10)}` },
                              { k: "result", v: sc.result },
                              { k: "timestamp", v: new Date().toISOString().slice(0, 19) + "Z" },
                              { k: "policy_hash", v: "sha256:9f86d081..." },
                              { k: "violations", v: String(sc.violations) },
                              { k: "eu_ai_act", v: "6/6 articles compliant" },
                            ].map(({ k, v }) => (
                              <div key={k} className="flex justify-between rounded bg-black/30 px-3 py-1.5 font-mono text-xs">
                                <span className="text-[#71717a]">{k}</span>
                                <span className={sc.result === "ALLOWED" ? "text-[#22c55e]" : "text-[#ef4444]"}>{v}</span>
                              </div>
                            ))}
                          </div>
                        )}

                        {i < pipelineSteps.length - 1 && (
                          <button
                            onClick={() => setActiveStep(i + 1)}
                            className="mt-2 flex items-center gap-1 text-sm text-[#6366f1] hover:text-[#818cf8] transition"
                          >
                            Next step <ArrowRight className="h-3.5 w-3.5" />
                          </button>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </>
        )}

        {/* ══════════════ Free Dashboard Tab ══════════════ */}
        {activeTab === "free" && (
          <div className="space-y-6">
            <div className="flex items-center gap-2 mb-2">
              <span className="inline-flex items-center rounded bg-[#22c55e]/10 border border-[#22c55e]/30 px-2 py-0.5 text-[10px] font-medium text-[#22c55e]">
                FREE
              </span>
              <span className="text-sm text-[#71717a]">Everything you get with the free tier</span>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {[
                { label: "Total Decisions", value: freeDemo.stats.total_decisions, color: "#818cf8" },
                { label: "Allowed", value: freeDemo.stats.allowed, color: "#22c55e" },
                { label: "Blocked", value: freeDemo.stats.blocked, color: "#ef4444" },
                { label: "Block Rate", value: freeDemo.stats.block_rate, color: "#f59e0b" },
              ].map((stat) => (
                <div key={stat.label} className="rounded-xl border border-[#1e1e2e] bg-[#111119] p-4">
                  <p className="text-xs text-[#71717a]">{stat.label}</p>
                  <p className="mt-1 text-2xl font-bold" style={{ color: stat.color }}>{stat.value}</p>
                </div>
              ))}
            </div>

            {/* Decision Log */}
            <div className="rounded-xl border border-[#1e1e2e] bg-[#111119] p-5">
              <h3 className="text-sm font-medium text-white mb-3 flex items-center gap-2">
                <Activity className="h-4 w-4 text-[#6366f1]" />
                Recent Decisions
              </h3>
              <div className="space-y-1.5">
                {freeDemo.recentDecisions.map((d) => (
                  <div key={d.id} className="flex items-center justify-between rounded bg-[#0a0a0f] px-3 py-2">
                    <div className="flex items-center gap-3">
                      <span className={`inline-flex items-center rounded border px-1.5 py-0.5 text-[10px] font-medium ${
                        d.result === "ALLOWED"
                          ? "bg-[#22c55e]/10 border-[#22c55e]/30 text-[#22c55e]"
                          : "bg-[#ef4444]/10 border-[#ef4444]/30 text-[#ef4444]"
                      }`}>
                        {d.result}
                      </span>
                      <span className="font-mono text-xs text-[#e4e4e7]">{d.action}</span>
                      <span className="text-[10px] text-[#6366f1]">{d.agent}</span>
                    </div>
                    <div className="flex items-center gap-3 text-[10px] text-[#71717a]">
                      <span>{d.duration}ms</span>
                      <span>{d.time}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Compliance Status + Policy Viewer */}
            <div className="grid gap-4 md:grid-cols-2">
              {/* Compliance */}
              <div className="rounded-xl border border-[#1e1e2e] bg-[#111119] p-5">
                <h3 className="text-sm font-medium text-white mb-3 flex items-center gap-2">
                  <Shield className="h-4 w-4 text-[#22c55e]" />
                  EU AI Act Compliance
                </h3>
                <div className="space-y-2">
                  {[
                    { art: "Art. 12", name: "Record Keeping", ok: true },
                    { art: "Art. 13", name: "Transparency", ok: true },
                    { art: "Art. 14", name: "Human Oversight", ok: true },
                    { art: "Art. 15", name: "Accuracy & Resilience", ok: true },
                    { art: "Art. 19", name: "Automatic Logs", ok: true },
                    { art: "Art. 86", name: "Right to Explanation", ok: true },
                  ].map((a) => (
                    <div key={a.art} className="flex items-center justify-between rounded bg-[#0a0a0f] px-3 py-1.5">
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-mono text-[#71717a] w-12">{a.art}</span>
                        <span className="text-xs text-[#e4e4e7]">{a.name}</span>
                      </div>
                      <CheckCircle2 className="h-3.5 w-3.5 text-[#22c55e]" />
                    </div>
                  ))}
                </div>
                <div className="mt-3 flex items-center justify-between rounded-lg border border-[#22c55e]/20 bg-[#22c55e]/5 px-3 py-2">
                  <span className="text-xs text-[#22c55e]">Compliance Score</span>
                  <span className="text-sm font-bold text-[#22c55e]">6/6</span>
                </div>
              </div>

              {/* Policy Viewer */}
              <div className="rounded-xl border border-[#1e1e2e] bg-[#111119] p-5">
                <h3 className="text-sm font-medium text-white mb-3 flex items-center gap-2">
                  <FileText className="h-4 w-4 text-[#6366f1]" />
                  Policy: GovernanceGuard
                </h3>
                <div className="space-y-1.5">
                  {["analyst_no_spend", "manager_approval_limit", "director_approval_limit", "vp_approval_limit", "single_channel_cap", "weekend_freeze", "absolute_ceiling"].map((name) => (
                    <div key={name} className="flex items-center justify-between rounded bg-[#0a0a0f] px-3 py-1.5">
                      <span className="font-mono text-[10px] text-[#e4e4e7]">{name}</span>
                      <Lock className="h-3 w-3 text-[#71717a]" />
                    </div>
                  ))}
                </div>
                <div className="mt-3 rounded bg-[#0a0a0f] px-3 py-2">
                  <p className="text-[10px] text-[#71717a]">Backend: <span className="text-[#818cf8]">CSL+Z3</span> &middot; 7 constraints &middot; 6 variables</p>
                </div>
              </div>
            </div>

            <div className="flex items-start gap-2 rounded-lg border border-[#818cf8]/20 bg-[#818cf8]/5 px-4 py-3">
              <Info className="h-4 w-4 text-[#818cf8] mt-0.5 shrink-0" />
              <p className="text-xs text-[#818cf8]/80 leading-relaxed">
                Free tier includes decision log (last 7 days, 100 records), compliance flags, single policy viewer, and full unlimited local CLI usage. Upgrade to Pro for analytics, reasoning traces, simulation, and multi-agent management.
              </p>
            </div>
          </div>
        )}

        {/* ══════════════ Pro Dashboard Tab ══════════════ */}
        {activeTab === "pro" && (
          <div className="space-y-6">
            <div className="flex items-center gap-2 mb-2">
              <span className="inline-flex items-center rounded bg-[#6366f1]/10 border border-[#6366f1]/30 px-2 py-0.5 text-[10px] font-medium text-[#818cf8]">
                PRO
              </span>
              <span className="text-sm text-[#71717a]">Advanced analytics, reasoning traces, and agent control</span>
            </div>

            {/* Decision Trend Chart — SVG Area Chart */}
            <div className="rounded-xl border border-[#1e1e2e] bg-[#111119] p-5">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-medium text-white flex items-center gap-2">
                  <TrendingUp className="h-4 w-4 text-[#6366f1]" />
                  Decision Analytics (30 Days)
                </h3>
                <div className="flex items-center gap-3 text-[10px] text-[#71717a]">
                  <span className="flex items-center gap-1"><span className="h-2 w-2 rounded bg-[#6366f1]" /> Total</span>
                  <span className="flex items-center gap-1"><span className="h-2 w-2 rounded bg-[#22c55e]" /> Allowed</span>
                  <span className="flex items-center gap-1"><span className="h-2 w-2 rounded bg-[#ef4444]" /> Blocked</span>
                </div>
              </div>
              {/* SVG Area Chart */}
              <div className="relative h-44">
                <svg viewBox="0 0 600 160" className="w-full h-full" preserveAspectRatio="none">
                  <defs>
                    <linearGradient id="totalGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#6366f1" stopOpacity="0.3" />
                      <stop offset="100%" stopColor="#6366f1" stopOpacity="0" />
                    </linearGradient>
                    <linearGradient id="blockedGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#ef4444" stopOpacity="0.4" />
                      <stop offset="100%" stopColor="#ef4444" stopOpacity="0" />
                    </linearGradient>
                  </defs>
                  {/* Grid lines */}
                  {[0, 40, 80, 120].map((y) => (
                    <line key={y} x1="0" y1={y} x2="600" y2={y} stroke="#1e1e2e" strokeWidth="0.5" />
                  ))}
                  {/* Total area (allowed + blocked) */}
                  <path
                    d={(() => {
                      const max = 360;
                      const points = proDemo.trendData.map((d, i) => {
                        const x = (i / (proDemo.trendData.length - 1)) * 600;
                        const y = 155 - ((d.allowed + d.blocked) / max) * 150;
                        return `${x},${y}`;
                      });
                      return `M0,155 L${points.join(" L")} L600,155 Z`;
                    })()}
                    fill="url(#totalGrad)"
                  />
                  <path
                    d={(() => {
                      const max = 360;
                      const points = proDemo.trendData.map((d, i) => {
                        const x = (i / (proDemo.trendData.length - 1)) * 600;
                        const y = 155 - ((d.allowed + d.blocked) / max) * 150;
                        return `${x},${y}`;
                      });
                      return `M${points.join(" L")}`;
                    })()}
                    fill="none" stroke="#6366f1" strokeWidth="2"
                  />
                  {/* Blocked area */}
                  <path
                    d={(() => {
                      const max = 360;
                      const points = proDemo.trendData.map((d, i) => {
                        const x = (i / (proDemo.trendData.length - 1)) * 600;
                        const y = 155 - (d.blocked / max) * 150;
                        return `${x},${y}`;
                      });
                      return `M0,155 L${points.join(" L")} L600,155 Z`;
                    })()}
                    fill="url(#blockedGrad)"
                  />
                  <path
                    d={(() => {
                      const max = 360;
                      const points = proDemo.trendData.map((d, i) => {
                        const x = (i / (proDemo.trendData.length - 1)) * 600;
                        const y = 155 - (d.blocked / max) * 150;
                        return `${x},${y}`;
                      });
                      return `M${points.join(" L")}`;
                    })()}
                    fill="none" stroke="#ef4444" strokeWidth="1.5" strokeDasharray="4 2"
                  />
                  {/* Data points on total line */}
                  {proDemo.trendData.filter((_, i) => i % 5 === 0).map((d, idx) => {
                    const max = 360;
                    const i = idx * 5;
                    const x = (i / (proDemo.trendData.length - 1)) * 600;
                    const y = 155 - ((d.allowed + d.blocked) / max) * 150;
                    return <circle key={i} cx={x} cy={y} r="3" fill="#6366f1" stroke="#111119" strokeWidth="1.5" />;
                  })}
                </svg>
                {/* Y-axis labels */}
                <div className="absolute left-0 top-0 h-full flex flex-col justify-between text-[9px] text-[#52525b] py-1">
                  <span>360</span>
                  <span>240</span>
                  <span>120</span>
                  <span>0</span>
                </div>
                {/* X-axis labels */}
                <div className="absolute bottom-0 left-0 right-0 flex justify-between text-[9px] text-[#52525b] px-2 translate-y-4">
                  <span>Mar 1</span>
                  <span>Mar 8</span>
                  <span>Mar 15</span>
                  <span>Mar 22</span>
                  <span>Mar 30</span>
                </div>
              </div>
              {/* Summary stats */}
              <div className="mt-8 grid grid-cols-4 gap-3">
                <div className="rounded-lg bg-[#0a0a0f] border border-[#1e1e2e] px-3 py-2 text-center">
                  <p className="text-lg font-bold text-white">4,587</p>
                  <p className="text-[10px] text-[#71717a]">Total Decisions</p>
                </div>
                <div className="rounded-lg bg-[#0a0a0f] border border-[#1e1e2e] px-3 py-2 text-center">
                  <p className="text-lg font-bold text-[#22c55e]">3,648</p>
                  <p className="text-[10px] text-[#71717a]">Allowed</p>
                </div>
                <div className="rounded-lg bg-[#0a0a0f] border border-[#1e1e2e] px-3 py-2 text-center">
                  <p className="text-lg font-bold text-[#ef4444]">939</p>
                  <p className="text-[10px] text-[#71717a]">Blocked</p>
                </div>
                <div className="rounded-lg bg-[#0a0a0f] border border-[#1e1e2e] px-3 py-2 text-center">
                  <p className="text-lg font-bold text-[#f59e0b]">20.5%</p>
                  <p className="text-[10px] text-[#71717a]">Block Rate</p>
                </div>
              </div>
            </div>

            {/* Reasoning Trace */}
            <div className="rounded-xl border border-[#1e1e2e] bg-[#111119] p-5">
              <h3 className="text-sm font-medium text-white mb-4 flex items-center gap-2">
                <Brain className="h-4 w-4 text-[#f59e0b]" />
                Reasoning Trace — Decision Detail
              </h3>
              <div className="space-y-3">
                {/* Header */}
                <div className="flex items-center gap-3">
                  <span className="inline-flex items-center rounded border bg-[#ef4444]/10 border-[#ef4444]/30 px-2 py-0.5 text-[10px] font-medium text-[#ef4444]">
                    BLOCKED
                  </span>
                  <span className="font-mono text-xs text-[#e4e4e7]">{proDemo.reasoningTrace.decision_id}</span>
                  <span className="text-[10px] text-[#6366f1]">{proDemo.reasoningTrace.agent}</span>
                </div>

                {/* Timing */}
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { label: "Total", value: `${proDemo.reasoningTrace.total_duration_ms}ms`, color: "#818cf8" },
                    { label: "LLM", value: `${proDemo.reasoningTrace.llm_duration_ms}ms`, color: "#f59e0b" },
                    { label: "Policy Eval", value: `${proDemo.reasoningTrace.policy_evaluation_ms}ms`, color: "#22c55e" },
                  ].map((t) => (
                    <div key={t.label} className="rounded bg-[#0a0a0f] px-3 py-2 text-center">
                      <p className="text-[10px] text-[#71717a]">{t.label}</p>
                      <p className="text-sm font-mono font-medium" style={{ color: t.color }}>{t.value}</p>
                    </div>
                  ))}
                </div>

                {/* Candidates */}
                <div>
                  <p className="text-xs text-[#71717a] mb-2">LLM Candidates</p>
                  {proDemo.reasoningTrace.candidates.map((c, i) => (
                    <div key={i} className="flex items-center justify-between rounded bg-[#0a0a0f] px-3 py-1.5 mb-1">
                      <div className="flex items-center gap-2">
                        {c.selected && <Play className="h-3 w-3 text-[#6366f1]" />}
                        <span className={`text-xs ${c.selected ? "text-white" : "text-[#71717a]"}`}>{c.strategy}</span>
                      </div>
                      <span className="text-[10px] font-mono text-[#f59e0b]">{(c.confidence * 100).toFixed(0)}%</span>
                    </div>
                  ))}
                </div>

                {/* Violations */}
                <div>
                  <p className="text-xs text-[#71717a] mb-2">Violations</p>
                  {proDemo.reasoningTrace.violations.map((v, i) => (
                    <div key={i} className="rounded border border-[#ef4444]/20 bg-[#ef4444]/5 px-3 py-2">
                      <p className="font-mono text-xs text-[#f59e0b]">{v.constraint}</p>
                      <p className="mt-0.5 text-xs text-[#e4e4e7]">{v.explanation}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Agent Control + Heatmap */}
            <div className="grid gap-4 md:grid-cols-2">
              {/* Agent Control */}
              <div className="rounded-xl border border-[#1e1e2e] bg-[#111119] p-5">
                <h3 className="text-sm font-medium text-white mb-3 flex items-center gap-2">
                  <Shield className="h-4 w-4 text-[#818cf8]" />
                  Agent Control
                  <span className="text-[10px] rounded border border-[#f59e0b]/30 bg-[#f59e0b]/10 text-[#f59e0b] px-1.5 py-0.5">Art. 14</span>
                </h3>
                <div className="space-y-2">
                  {proDemo.agents.map((a) => (
                    <div key={a.name} className="flex items-center justify-between rounded bg-[#0a0a0f] px-3 py-2">
                      <div>
                        <span className="text-xs text-white">{a.name}</span>
                        <span className="ml-2 text-[10px] text-[#71717a]">{a.total} decisions</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={`text-[10px] ${a.blocked > 30 ? "text-[#ef4444]" : "text-[#71717a]"}`}>
                          {a.blocked} blocked
                        </span>
                        {a.halted ? (
                          <span className="flex items-center gap-1 text-[10px] text-[#ef4444]">
                            <PauseCircle className="h-3.5 w-3.5" /> Halted
                          </span>
                        ) : (
                          <span className="flex items-center gap-1 text-[10px] text-[#22c55e]">
                            <PlayCircle className="h-3.5 w-3.5" /> Running
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Block Rate Heatmap */}
              <div className="rounded-xl border border-[#1e1e2e] bg-[#111119] p-5">
                <h3 className="text-sm font-medium text-white mb-3 flex items-center gap-2">
                  <BarChart3 className="h-4 w-4 text-[#ef4444]" />
                  Block Rate Heatmap
                </h3>
                <div className="space-y-1">
                  {["Mon", "Wed", "Fri"].map((day, di) => (
                    <div key={day} className="flex items-center gap-1">
                      <span className="text-[9px] text-[#71717a] w-6">{day}</span>
                      <div className="flex gap-0.5 flex-1">
                        {proDemo.heatmapData[di].map((val, hi) => {
                          const intensity = Math.min(val / 30, 1);
                          return (
                            <div
                              key={hi}
                              className="flex-1 h-4 rounded-sm"
                              style={{
                                backgroundColor: intensity > 0
                                  ? `rgba(239, 68, 68, ${intensity * 0.8})`
                                  : "rgba(30, 30, 46, 0.5)",
                              }}
                              title={`${day} ${hi}:00 — ${val} blocks`}
                            />
                          );
                        })}
                      </div>
                    </div>
                  ))}
                  <div className="flex items-center justify-between mt-2">
                    <span className="text-[9px] text-[#71717a]">0:00</span>
                    <span className="text-[9px] text-[#71717a]">12:00</span>
                    <span className="text-[9px] text-[#71717a]">23:00</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Policy Simulation Preview */}
            <div className="rounded-xl border border-[#1e1e2e] bg-[#111119] p-5">
              <h3 className="text-sm font-medium text-white mb-3 flex items-center gap-2">
                <FlaskConical className="h-4 w-4 text-[#6366f1]" />
                Policy Simulation
              </h3>
              <div className="grid gap-3 sm:grid-cols-3">
                {[
                  { var: "amount", value: "500000", domain: "0..1000000" },
                  { var: "role", value: "MANAGER", domain: '{"ANALYST","MANAGER",...}' },
                  { var: "channel", value: "DIGITAL", domain: '{"DIGITAL","TV",...}' },
                ].map((p) => (
                  <div key={p.var} className="rounded bg-[#0a0a0f] border border-[#1e1e2e] p-2.5">
                    <div className="flex justify-between mb-1">
                      <span className="font-mono text-[10px] text-[#e4e4e7]">{p.var}</span>
                      <span className="font-mono text-[9px] text-[#71717a]">{p.domain}</span>
                    </div>
                    <div className="rounded bg-[#111119] border border-[#1e1e2e] px-2 py-1 text-xs text-[#818cf8] font-mono">
                      {p.value}
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-3 flex items-center justify-between rounded-lg border border-[#ef4444]/20 bg-[#ef4444]/5 px-4 py-2.5">
                <div className="flex items-center gap-2">
                  <XCircle className="h-5 w-5 text-[#ef4444]" />
                  <span className="text-sm font-medium text-[#ef4444]">BLOCKED</span>
                  <span className="text-[10px] text-[#71717a]">0.08ms</span>
                </div>
                <span className="font-mono text-[10px] text-[#f59e0b]">single_channel_cap violated</span>
              </div>
            </div>

            <div className="flex items-start gap-2 rounded-lg border border-[#6366f1]/20 bg-[#6366f1]/5 px-4 py-3">
              <Zap className="h-4 w-4 text-[#818cf8] mt-0.5 shrink-0" />
              <p className="text-xs text-[#818cf8]/80 leading-relaxed">
                Pro tier includes analytics charts, reasoning traces, policy simulation, halt/resume agent control, multi-agent support, API keys, export, and 90-day data retention. <span className="line-through text-[#818cf8]/50">$79/mo</span> <strong className="text-[#22c55e]">$29/month — Launch Special</strong>
              </p>
            </div>
          </div>
        )}

        {/* CTA */}
        <div className="mt-12 text-center space-y-4">
          <div className="flex items-center justify-center gap-4">
            <Link href="/register">
              <button className="bg-[#6366f1] hover:bg-[#5558e6] text-white font-medium px-8 py-3 rounded-lg transition text-sm">
                Start Free <ArrowRight className="inline h-4 w-4 ml-1" />
              </button>
            </Link>
            <Link href="/contact">
              <button className="border border-[#1e1e2e] hover:border-[#2e2e3e] text-[#a1a1aa] hover:text-white font-medium px-8 py-3 rounded-lg transition text-sm">
                Contact Sales
              </button>
            </Link>
          </div>
          <p className="text-[#52525b] text-xs">
            Free tier includes unlimited local usage + 7-day cloud dashboard
          </p>
        </div>
      </div>
    </div>
  );
}
