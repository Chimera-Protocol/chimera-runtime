"use client";

import { useEffect, useState } from "react";
import { StatsCards } from "@/components/dashboard/StatsCards";
import { RecentDecisions } from "@/components/dashboard/RecentDecisions";
import { ComplianceStatus } from "@/components/dashboard/ComplianceStatus";
import { ViolationsChart } from "@/components/dashboard/ViolationsChart";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type {
  AuditStats,
  DecisionSummary,
  ComplianceStatus as ComplianceStatusType,
  ViolationCount,
} from "@/lib/types";

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
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Dashboard</h1>
        <p className="mt-1 text-sm text-[#71717a]">
          Real-time compliance monitoring overview
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
