"use client";

import { useEffect, useState } from "react";
import { StatsCards } from "@/components/dashboard/StatsCards";
import { RecentDecisions } from "@/components/dashboard/RecentDecisions";
import { ComplianceStatus } from "@/components/dashboard/ComplianceStatus";
import { ViolationsChart } from "@/components/dashboard/ViolationsChart";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { Info, X } from "lucide-react";
import type {
  AuditStats,
  DecisionSummary,
  ComplianceStatus as ComplianceStatusType,
  ViolationCount,
} from "@/lib/types";

function DemoBanner() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const dismissed = localStorage.getItem("chimera_demo_banner_dismissed");
    if (!dismissed) setVisible(true);
  }, []);

  const dismiss = (permanent: boolean) => {
    setVisible(false);
    if (permanent) localStorage.setItem("chimera_demo_banner_dismissed", "1");
  };

  if (!visible) return null;

  return (
    <div className="relative rounded-xl border border-indigo-500/20 bg-indigo-500/[0.04] px-5 py-4 flex items-start gap-4">
      <div className="mt-0.5 h-8 w-8 rounded-lg bg-indigo-500/10 flex items-center justify-center shrink-0">
        <Info className="h-4 w-4 text-indigo-400" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-white">Sample Data</p>
        <p className="text-xs text-[#71717a] mt-1 leading-relaxed">
          This dashboard is populated with sample audit records for demonstration purposes.
          Connect your own agent via <span className="text-indigo-400 font-mono">pip install chimera-runtime</span> to see real enforcement data.
        </p>
        <div className="flex items-center gap-3 mt-3">
          <button
            onClick={() => dismiss(false)}
            className="text-xs font-medium text-indigo-400 hover:text-indigo-300 transition"
          >
            Got it
          </button>
          <button
            onClick={() => dismiss(true)}
            className="text-xs text-[#52525b] hover:text-[#71717a] transition"
          >
            Don&apos;t show again
          </button>
        </div>
      </div>
      <button
        onClick={() => dismiss(false)}
        className="text-[#52525b] hover:text-white transition shrink-0"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  );
}

export default function DashboardPage() {
  const { user } = useAuth();
  const tier = user?.tier || "free";
  const [stats, setStats] = useState<AuditStats | null>(null);
  const [decisions, setDecisions] = useState<DecisionSummary[]>([]);
  const [compliance, setCompliance] = useState<ComplianceStatusType | null>(null);
  const [violations, setViolations] = useState<ViolationCount[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const [statsData, decisionsData, complianceData, violationsData] =
          await Promise.all([
            api.getStats(tier),
            api.getDecisions({ limit: 10, tier }),
            api.getComplianceStatus(),
            api.getViolations(5, tier),
          ]);
        setStats(statsData);
        setDecisions(decisionsData.items);
        setCompliance(complianceData);
        setViolations(violationsData);
      } catch (err) {
        console.error("Failed to fetch dashboard data:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  return (
    <div className="space-y-6">
      {/* Demo Banner */}
      <DemoBanner />

      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Dashboard</h1>
        <p className="mt-1 text-sm text-[#71717a]">
          Real-time enforcement monitoring overview
        </p>
      </div>

      {/* Stats Cards */}
      <StatsCards stats={stats} loading={loading} />

      {/* Main Content Grid */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Recent Decisions (2/3 width) */}
        <div className="lg:col-span-2">
          <RecentDecisions decisions={decisions} loading={loading} />
        </div>

        {/* Compliance Status (1/3 width) */}
        <div>
          <ComplianceStatus status={compliance} loading={loading} />
        </div>
      </div>

      {/* Violations Chart */}
      <ViolationsChart violations={violations} loading={loading} />
    </div>
  );
}
