"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Shield, Check, X } from "lucide-react";
import type { ComplianceStatus as ComplianceStatusType } from "@/lib/types";

const articleLabels: Record<string, string> = {
  article_12_record_keeping: "Art. 12 — Record Keeping",
  article_13_transparency: "Art. 13 — Transparency",
  article_14_human_oversight: "Art. 14 — Human Oversight",
  article_15_accuracy_resilience: "Art. 15 — Accuracy & Resilience",
  article_19_automatic_logs: "Art. 19 — Automatic Logs",
  article_86_right_to_explanation: "Art. 86 — Right to Explanation",
};

interface ComplianceStatusProps {
  status: ComplianceStatusType | null;
  loading?: boolean;
}

export function ComplianceStatus({ status, loading }: ComplianceStatusProps) {
  if (loading) {
    return (
      <Card className="border-[#1e1e2e] bg-[#111119]">
        <CardHeader>
          <CardTitle className="text-white">EU AI Act Enforcement</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-32 animate-pulse rounded bg-[#1e1e2e]" />
        </CardContent>
      </Card>
    );
  }

  const articles = status?.articles || {};
  const compliantCount = Object.values(articles).filter(Boolean).length;
  const totalArticles = Object.keys(articles).length || 6;

  return (
    <Card className="border-[#1e1e2e] bg-[#111119]">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-white flex items-center gap-2">
          <Shield className="h-5 w-5 text-[#6366f1]" />
          EU AI Act Enforcement
        </CardTitle>
        <Badge
          variant="outline"
          className={
            status?.compliant
              ? "border-[#22c55e]/30 bg-[#22c55e]/10 text-[#22c55e]"
              : "border-[#f59e0b]/30 bg-[#f59e0b]/10 text-[#f59e0b]"
          }
        >
          {status?.score || `0/${totalArticles}`}
        </Badge>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {Object.entries(articles).map(([key, value]) => (
            <div
              key={key}
              className="flex items-center justify-between rounded-lg border border-[#1e1e2e] bg-[#0a0a0f] px-3 py-2"
            >
              <span className="text-sm text-[#e4e4e7]">
                {articleLabels[key] || key}
              </span>
              {value ? (
                <Check className="h-4 w-4 text-[#22c55e]" />
              ) : (
                <X className="h-4 w-4 text-[#ef4444]" />
              )}
            </div>
          ))}
        </div>

        {/* Formal Verification */}
        {status?.formal_verification && (
          <div className="mt-4 flex items-center gap-2 text-sm">
            <span className="text-[#71717a]">Z3 Verification:</span>
            <Badge
              variant="outline"
              className={
                status.formal_verification.policy_verified
                  ? "border-[#22c55e]/30 text-[#22c55e]"
                  : "border-[#71717a]/30 text-[#71717a]"
              }
            >
              {status.formal_verification.verification_engine}{" "}
              {status.formal_verification.verification_result}
            </Badge>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
