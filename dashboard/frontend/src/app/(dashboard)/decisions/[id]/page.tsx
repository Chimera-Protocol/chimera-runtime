"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { ProGate } from "@/components/pro-gate";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  ArrowLeft,
  Shield,
  Clock,
  Bot,
  FileText,
  AlertTriangle,
  ChevronDown,
  Star,
  Brain,
  Download,
} from "lucide-react";
import type {
  DecisionSummary,
  DecisionAuditRecord,
  Candidate,
} from "@/lib/types";

const resultColors: Record<string, string> = {
  ALLOWED: "bg-[#22c55e]/10 text-[#22c55e] border-[#22c55e]/30",
  BLOCKED: "bg-[#ef4444]/10 text-[#ef4444] border-[#ef4444]/30",
  HUMAN_OVERRIDE: "bg-[#f59e0b]/10 text-[#f59e0b] border-[#f59e0b]/30",
  INTERRUPTED: "bg-[#6b7280]/10 text-[#6b7280] border-[#6b7280]/30",
};

function isFullRecord(d: unknown): d is DecisionAuditRecord {
  return (
    typeof d === "object" &&
    d !== null &&
    "reasoning" in d &&
    "agent" in d &&
    "performance" in d
  );
}

export default function DecisionDetailPage() {
  const params = useParams();
  const id = params?.id as string;
  const { user } = useAuth();
  const tier = user?.tier || "free";

  const [decision, setDecision] = useState<
    DecisionAuditRecord | DecisionSummary | null
  >(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedAttempts, setExpandedAttempts] = useState<Set<number>>(
    new Set([0])
  );

  useEffect(() => {
    if (!id) return;
    async function fetchDecision() {
      try {
        const data = await api.getDecision(id, tier);
        setDecision(data);
      } catch {
        setError("Decision not found");
      } finally {
        setLoading(false);
      }
    }
    fetchDecision();
  }, [id, tier]);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-48 animate-pulse rounded bg-[#1e1e2e]" />
        <div className="h-96 animate-pulse rounded bg-[#1e1e2e]" />
      </div>
    );
  }

  if (error || !decision) {
    return (
      <div className="space-y-6">
        <Link href="/decisions">
          <Button variant="ghost" className="text-[#71717a] hover:text-white">
            <ArrowLeft className="mr-2 h-4 w-4" /> Back to Decisions
          </Button>
        </Link>
        <Card className="border-[#1e1e2e] bg-[#111119]">
          <CardContent className="py-16 text-center text-[#ef4444]">
            {error || "Decision not found"}
          </CardContent>
        </Card>
      </div>
    );
  }

  const summary: DecisionSummary = isFullRecord(decision)
    ? {
        decision_id: decision.decision_id,
        timestamp: decision.timestamp,
        result: decision.decision.result,
        action: decision.decision.action_taken,
        policy_file: decision.decision.policy_file,
        duration_ms: decision.performance.total_duration_ms,
        total_candidates: decision.reasoning.total_candidates,
        total_attempts: decision.reasoning.total_attempts,
        agent_name: decision.agent.name,
        model: decision.agent.model,
        violations: [],
      }
    : (decision as DecisionSummary);

  const full = isFullRecord(decision) ? decision : null;

  async function handleExplanation() {
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"}/audit/decisions/${id}/explanation`,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("chimera_token") || ""}`,
          },
        }
      );
      if (!res.ok) throw new Error("Failed");
      const html = await res.text();
      const w = window.open("", "_blank");
      if (w) {
        w.document.write(html);
        w.document.close();
      }
    } catch (err) {
      console.error("Explanation error:", err);
    }
  }

  function toggleAttempt(n: number) {
    setExpandedAttempts((prev) => {
      const next = new Set(prev);
      if (next.has(n)) next.delete(n);
      else next.add(n);
      return next;
    });
  }

  return (
    <div className="space-y-6">
      <Link href="/decisions">
        <Button variant="ghost" className="text-[#71717a] hover:text-white">
          <ArrowLeft className="mr-2 h-4 w-4" /> Back to Decisions
        </Button>
      </Link>

      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-white">Decision Detail</h1>
            <Badge
              variant="outline"
              className={resultColors[summary.result] || resultColors.INTERRUPTED}
            >
              {summary.result}
            </Badge>
          </div>
          <p className="mt-1 font-mono text-sm text-[#71717a]">
            {summary.decision_id}
          </p>
        </div>
        <ProGate feature="Art. 86 Explanation">
          <Button
            onClick={handleExplanation}
            variant="outline"
            className="border-[#6366f1]/30 text-[#818cf8] hover:bg-[#6366f1]/10"
          >
            <Download className="mr-2 h-4 w-4" />
            Art. 86 Report
          </Button>
        </ProGate>
      </div>

      {/* Info Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <InfoCard icon={<FileText className="h-5 w-5 text-[#6366f1]" />} label="Action" value={summary.action} />
        <InfoCard icon={<Clock className="h-5 w-5 text-[#f59e0b]" />} label="Latency" value={`${summary.duration_ms.toFixed(1)}ms`} />
        <InfoCard icon={<Bot className="h-5 w-5 text-[#818cf8]" />} label="Agent" value={summary.agent_name || "N/A"} />
        <InfoCard icon={<Shield className="h-5 w-5 text-[#22c55e]" />} label="Candidates" value={`${summary.total_candidates} (${summary.total_attempts} att.)`} />
      </div>

      {/* Details */}
      <Card className="border-[#1e1e2e] bg-[#111119]">
        <CardHeader><CardTitle className="text-white">Details</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <DetailRow label="Timestamp" value={formatDate(summary.timestamp)} />
          <DetailRow label="Policy File" value={summary.policy_file} mono />
          <DetailRow label="Model" value={summary.model || "N/A"} />
          {full && (
            <>
              <DetailRow label="Agent Version" value={full.agent.version} />
              <DetailRow label="CSL-Core" value={full.agent.csl_core_version} />
              <DetailRow label="Temperature" value={String(full.agent.temperature)} />
            </>
          )}
        </CardContent>
      </Card>

      {/* Violations */}
      {summary.violations && summary.violations.length > 0 && (
        <Card className="border-[#ef4444]/20 bg-[#111119]">
          <CardHeader>
            <CardTitle className="text-[#ef4444] flex items-center gap-2">
              <AlertTriangle className="h-5 w-5" />
              Violations ({summary.violations.length})
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {summary.violations.map((v, i) => (
              <div key={i} className="rounded-lg border border-[#ef4444]/20 bg-[#ef4444]/5 p-4">
                <Badge variant="outline" className="border-[#ef4444]/30 text-[#ef4444] font-mono text-xs">
                  {v.constraint}
                </Badge>
                <p className="mt-2 text-sm text-[#e4e4e7]">{v.explanation}</p>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* ── Reasoning Trace (Pro) ───────────────────────────────── */}
      <ProGate feature="Full Reasoning Trace">
        {full ? (
          <Card className="border-[#1e1e2e] bg-[#111119]">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Brain className="h-5 w-5 text-[#6366f1]" />
                Reasoning Trace
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {full.reasoning.selected_candidate && (
                <div className="rounded-lg border border-[#6366f1]/20 bg-[#6366f1]/5 p-4">
                  <div className="flex items-center gap-2 mb-1">
                    <Star className="h-4 w-4 text-[#f59e0b]" />
                    <span className="text-sm font-medium text-white">
                      Selected: {full.reasoning.selected_candidate}
                    </span>
                  </div>
                  {full.reasoning.selection_reasoning && (
                    <p className="text-xs text-[#a1a1aa] mt-1">{full.reasoning.selection_reasoning}</p>
                  )}
                </div>
              )}

              {full.reasoning.attempts.map((attempt) => (
                <div key={attempt.attempt_number} className="rounded-lg border border-[#1e1e2e]">
                  <button
                    onClick={() => toggleAttempt(attempt.attempt_number)}
                    className="flex w-full items-center justify-between p-4 text-left hover:bg-[#1e1e2e]/50 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <Badge variant="outline" className="border-[#6366f1]/30 text-[#818cf8]">
                        Attempt {attempt.attempt_number}
                      </Badge>
                      <span className="text-sm text-[#a1a1aa]">
                        {attempt.candidates.length} candidates &middot; {attempt.outcome}
                      </span>
                    </div>
                    <ChevronDown className={`h-4 w-4 text-[#71717a] transition ${expandedAttempts.has(attempt.attempt_number) ? "rotate-180" : ""}`} />
                  </button>

                  {expandedAttempts.has(attempt.attempt_number) && (
                    <div className="border-t border-[#1e1e2e] p-4 space-y-3">
                      {attempt.candidates.map((c: Candidate) => (
                        <CandidateCard key={c.candidate_id} candidate={c} isSelected={c.candidate_id === full.reasoning.selected_candidate} />
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </CardContent>
          </Card>
        ) : (
          <Card className="border-[#1e1e2e] bg-[#111119]">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Brain className="h-5 w-5 text-[#6366f1]" />Reasoning Trace
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="h-16 rounded bg-[#1e1e2e]" />
                <div className="h-24 rounded bg-[#1e1e2e]" />
                <div className="h-24 rounded bg-[#1e1e2e]" />
              </div>
            </CardContent>
          </Card>
        )}
      </ProGate>

      {/* Performance Breakdown (Pro) */}
      {full && (
        <Card className="border-[#1e1e2e] bg-[#111119]">
          <CardHeader><CardTitle className="text-white">Performance Breakdown</CardTitle></CardHeader>
          <CardContent>
            <div className="grid gap-4 sm:grid-cols-4">
              <PerfStat label="Total" value={full.performance.total_duration_ms} color="#6366f1" />
              <PerfStat label="LLM" value={full.performance.llm_duration_ms} color="#f59e0b" />
              <PerfStat label="Policy" value={full.performance.policy_evaluation_ms} color="#22c55e" />
              <PerfStat label="Audit" value={full.performance.audit_generation_ms} color="#818cf8" />
            </div>
          </CardContent>
        </Card>
      )}

      {/* EU AI Act Compliance */}
      {full?.compliance && (
        <Card className="border-[#1e1e2e] bg-[#111119]">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Shield className="h-5 w-5 text-[#22c55e]" />EU AI Act Compliance
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-2 sm:grid-cols-3">
              {Object.entries(full.compliance.eu_ai_act).map(([key, val]) => (
                <div key={key} className="flex items-center gap-2 rounded bg-[#0a0a0f] px-3 py-2">
                  <div className={`h-2 w-2 rounded-full ${val ? "bg-[#22c55e]" : "bg-[#ef4444]"}`} />
                  <span className="text-xs text-[#a1a1aa]">{key.replace(/_/g, " ")}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function CandidateCard({ candidate, isSelected }: { candidate: Candidate; isSelected: boolean }) {
  return (
    <div className={`rounded-lg border p-4 ${isSelected ? "border-[#f59e0b]/30 bg-[#f59e0b]/5" : "border-[#1e1e2e] bg-[#0a0a0f]"}`}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          {isSelected && <Star className="h-3.5 w-3.5 text-[#f59e0b]" />}
          <span className="text-sm font-medium text-white">{candidate.strategy}</span>
        </div>
        <ConfidenceBar value={candidate.llm_confidence} />
      </div>
      {candidate.llm_reasoning && <p className="text-xs text-[#a1a1aa] mb-2 leading-relaxed">{candidate.llm_reasoning}</p>}
      {candidate.parameters && Object.keys(candidate.parameters).length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-2">
          {Object.entries(candidate.parameters).map(([k, v]) => (
            <span key={k} className="rounded bg-[#1e1e2e] px-2 py-0.5 font-mono text-[10px] text-[#a1a1aa]">
              {k}={String(v)}
            </span>
          ))}
        </div>
      )}
      {candidate.policy_evaluation && (
        <div className="mt-2 rounded border border-[#1e1e2e] bg-[#111119] p-2">
          <div className="flex items-center gap-2 mb-1">
            <Badge variant="outline" className={resultColors[candidate.policy_evaluation.result] || resultColors.INTERRUPTED}>
              {candidate.policy_evaluation.result}
            </Badge>
            <span className="text-[10px] text-[#71717a] font-mono">{candidate.policy_evaluation.duration_ms.toFixed(1)}ms</span>
          </div>
          {candidate.policy_evaluation.violations.length > 0 && (
            <div className="mt-1 space-y-1">
              {candidate.policy_evaluation.violations.map((v, i) => (
                <p key={i} className="text-[10px] text-[#ef4444]">{v.constraint}: {v.explanation}</p>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function ConfidenceBar({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const color = pct >= 70 ? "#22c55e" : pct >= 40 ? "#f59e0b" : "#ef4444";
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-16 rounded-full bg-[#1e1e2e] overflow-hidden">
        <div className="h-full rounded-full" style={{ width: `${pct}%`, backgroundColor: color }} />
      </div>
      <span className="text-xs font-mono" style={{ color }}>{pct}%</span>
    </div>
  );
}

function PerfStat({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="text-center">
      <p className="text-xs text-[#71717a]">{label}</p>
      <p className="text-lg font-bold font-mono" style={{ color }}>{value.toFixed(1)}ms</p>
    </div>
  );
}

function InfoCard({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <Card className="border-[#1e1e2e] bg-[#111119]">
      <CardContent className="flex items-center gap-3 p-4">
        {icon}
        <div>
          <p className="text-xs text-[#71717a]">{label}</p>
          <p className="text-sm font-medium text-white truncate">{value}</p>
        </div>
      </CardContent>
    </Card>
  );
}

function DetailRow({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="flex items-center justify-between border-b border-[#1e1e2e] pb-3 last:border-0 last:pb-0">
      <span className="text-sm text-[#71717a]">{label}</span>
      <span className={`text-sm text-white ${mono ? "font-mono text-xs" : ""}`}>{value}</span>
    </div>
  );
}

function formatDate(ts: string): string {
  try {
    return new Date(ts).toLocaleString("en-US", {
      year: "numeric", month: "short", day: "numeric",
      hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false,
    });
  } catch { return ts; }
}
