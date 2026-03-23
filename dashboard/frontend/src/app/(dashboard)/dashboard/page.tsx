"use client";

import { useCallback, useEffect, useState } from "react";
import { StatsCards } from "@/components/dashboard/StatsCards";
import { RecentDecisions } from "@/components/dashboard/RecentDecisions";
import { ComplianceStatus } from "@/components/dashboard/ComplianceStatus";
import { ViolationsChart } from "@/components/dashboard/ViolationsChart";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { Sparkles, RefreshCw, ArrowRight, Loader2, Database } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import type {
  AuditStats,
  DecisionSummary,
  ComplianceStatus as ComplianceStatusType,
  ViolationCount,
} from "@/lib/types";

function DemoBanner({
  hasData,
  onDataChanged,
}: {
  hasData: boolean;
  onDataChanged: () => void;
}) {
  const [loadingAction, setLoadingAction] = useState<"load" | "reset" | null>(null);

  const handleLoadDemo = async () => {
    setLoadingAction("load");
    try {
      await api.loadDemoData();
      onDataChanged();
    } catch (err) {
      console.error("Failed to load demo data:", err);
    } finally {
      setLoadingAction(null);
    }
  };

  const handleResetDemo = async () => {
    setLoadingAction("reset");
    try {
      await api.resetDemoData();
      onDataChanged();
    } catch (err) {
      console.error("Failed to reset demo data:", err);
    } finally {
      setLoadingAction(null);
    }
  };

  return (
    <AnimatePresence mode="wait">
      {!hasData ? (
        <motion.div
          key="welcome"
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          transition={{ duration: 0.3 }}
          className="relative rounded-xl border border-[#1e1e2e] bg-[#111119] px-5 py-5 flex items-start gap-4"
        >
          <div className="mt-0.5 h-10 w-10 rounded-lg bg-indigo-500/10 flex items-center justify-center shrink-0">
            <Database className="h-5 w-5 text-indigo-400" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-white">
              Welcome! Load sample data to explore the dashboard
            </p>
            <p className="text-xs text-[#71717a] mt-1 leading-relaxed">
              Get started by loading demo audit records and policies to see the dashboard in action.
            </p>
            <div className="flex items-center gap-3 mt-4">
              <button
                onClick={handleLoadDemo}
                disabled={loadingAction !== null}
                className="inline-flex items-center gap-2 rounded-lg bg-[#6366f1] px-4 py-2 text-xs font-semibold text-white hover:bg-[#5558e6] transition disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loadingAction === "load" ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <Sparkles className="h-3.5 w-3.5" />
                )}
                {loadingAction === "load" ? "Loading..." : "Load Demo Data"}
              </button>
            </div>
          </div>
        </motion.div>
      ) : (
        <motion.div
          key="loaded"
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          transition={{ duration: 0.3 }}
          className="relative rounded-xl border border-[#1e1e2e] bg-[#111119] px-5 py-4 flex items-start gap-4"
        >
          <div className="mt-0.5 h-8 w-8 rounded-lg bg-[#22c55e]/10 flex items-center justify-center shrink-0">
            <Database className="h-4 w-4 text-[#22c55e]" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-white">
              You&apos;re viewing demo data
            </p>
            <p className="text-xs text-[#71717a] mt-1 leading-relaxed">
              Connect your agent for real data, or reset demo data.
            </p>
            <div className="flex items-center gap-3 mt-3">
              <a
                href="/connect"
                className="inline-flex items-center gap-1.5 text-xs font-medium text-indigo-400 hover:text-indigo-300 transition"
              >
                Connect Agent
                <ArrowRight className="h-3 w-3" />
              </a>
              <button
                onClick={handleResetDemo}
                disabled={loadingAction !== null}
                className="inline-flex items-center gap-1.5 text-xs text-[#71717a] hover:text-white transition disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loadingAction === "reset" ? (
                  <Loader2 className="h-3 w-3 animate-spin" />
                ) : (
                  <RefreshCw className="h-3 w-3" />
                )}
                {loadingAction === "reset" ? "Resetting..." : "Reset Demo Data"}
              </button>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
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
  const [hasData, setHasData] = useState(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
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
      setHasData((statsData?.total_decisions ?? 0) > 0);
    } catch (err) {
      console.error("Failed to fetch dashboard data:", err);
    } finally {
      setLoading(false);
    }
  }, [tier]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return (
    <div className="space-y-6">
      {/* Demo Banner */}
      <DemoBanner hasData={hasData} onDataChanged={fetchData} />

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
