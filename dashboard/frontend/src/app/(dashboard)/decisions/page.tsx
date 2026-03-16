"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { ProGate } from "@/components/pro-gate";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ChevronLeft, ChevronRight, ExternalLink, AlertTriangle, Download } from "lucide-react";
import type { DecisionSummary, PaginatedResponse } from "@/lib/types";

const resultColors: Record<string, string> = {
  ALLOWED: "bg-[#22c55e]/10 text-[#22c55e] border-[#22c55e]/30",
  BLOCKED: "bg-[#ef4444]/10 text-[#ef4444] border-[#ef4444]/30",
  HUMAN_OVERRIDE: "bg-[#f59e0b]/10 text-[#f59e0b] border-[#f59e0b]/30",
  INTERRUPTED: "bg-[#6b7280]/10 text-[#6b7280] border-[#6b7280]/30",
};

export default function DecisionsPage() {
  const { user } = useAuth();
  const tier = user?.tier || "free";
  const [data, setData] = useState<PaginatedResponse<DecisionSummary> | null>(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [filter, setFilter] = useState<string>("all");
  const [agentFilter, setAgentFilter] = useState<string>("all");
  const [agents, setAgents] = useState<string[]>([]);
  const [exporting, setExporting] = useState(false);

  // Fetch agent list on mount
  useEffect(() => {
    api.getAgents().then((res) => {
      setAgents(res.agents.map((a) => a.name));
    }).catch(() => {});
  }, []);

  useEffect(() => {
    async function fetchDecisions() {
      setLoading(true);
      try {
        const result = await api.getDecisions({
          page,
          limit: 20,
          result: filter === "all" ? undefined : filter,
          agent: agentFilter === "all" ? undefined : agentFilter,
          tier,
        });
        setData(result);
      } catch (err) {
        console.error("Failed to fetch decisions:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchDecisions();
  }, [page, filter, agentFilter]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Decisions</h1>
          <p className="mt-1 text-sm text-[#71717a]">
            Audit log of all AI agent decisions
          </p>
        </div>
        <div className="flex items-center gap-3">
          <ProGate feature="Export">
            <Button
              variant="outline"
              size="sm"
              disabled={exporting}
              onClick={async () => {
                setExporting(true);
                try { await api.exportDecisions("json", tier); } finally { setExporting(false); }
              }}
              className="border-[#6366f1]/30 text-[#818cf8] hover:bg-[#6366f1]/10"
            >
              <Download className="mr-2 h-3.5 w-3.5" />
              {exporting ? "Exporting..." : "Export JSON"}
            </Button>
          </ProGate>
          {agents.length > 1 && (
            <Select value={agentFilter} onValueChange={(v: string | null) => { if (v) { setAgentFilter(v); setPage(1); } }}>
              <SelectTrigger className="w-52 border-[#1e1e2e] bg-[#111119] text-white">
                <SelectValue placeholder="Agent" />
              </SelectTrigger>
              <SelectContent className="border-[#1e1e2e] bg-[#111119]">
                <SelectItem value="all">All Agents</SelectItem>
                {agents.map((name) => (
                  <SelectItem key={name} value={name}>{name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
          <Select value={filter} onValueChange={(v: string | null) => { if (v) { setFilter(v); setPage(1); } }}>
            <SelectTrigger className="w-40 border-[#1e1e2e] bg-[#111119] text-white">
              <SelectValue placeholder="Filter" />
            </SelectTrigger>
            <SelectContent className="border-[#1e1e2e] bg-[#111119]">
              <SelectItem value="all">All Results</SelectItem>
              <SelectItem value="ALLOWED">Allowed</SelectItem>
              <SelectItem value="BLOCKED">Blocked</SelectItem>
              <SelectItem value="HUMAN_OVERRIDE">Override</SelectItem>
              <SelectItem value="INTERRUPTED">Interrupted</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      <Card className="border-[#1e1e2e] bg-[#111119]">
        <CardContent className="p-0">
          {loading ? (
            <div className="space-y-2 p-6">
              {Array.from({ length: 8 }).map((_, i) => (
                <div key={i} className="h-12 animate-pulse rounded bg-[#1e1e2e]" />
              ))}
            </div>
          ) : data && data.items.length > 0 ? (
            <>
              <Table>
                <TableHeader>
                  <TableRow className="border-[#1e1e2e] hover:bg-transparent">
                    <TableHead className="text-[#71717a]">Result</TableHead>
                    <TableHead className="text-[#71717a]">Decision ID</TableHead>
                    <TableHead className="text-[#71717a]">Action</TableHead>
                    <TableHead className="text-[#71717a]">Agent</TableHead>
                    <TableHead className="text-[#71717a]">Violations</TableHead>
                    <TableHead className="text-[#71717a]">Latency</TableHead>
                    <TableHead className="text-[#71717a]">Timestamp</TableHead>
                    <TableHead className="text-[#71717a]"></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data.items.map((d) => (
                    <TableRow
                      key={d.decision_id}
                      className="border-[#1e1e2e] hover:bg-[#1e1e2e]/50"
                    >
                      <TableCell>
                        <Badge
                          variant="outline"
                          className={resultColors[d.result] || resultColors.INTERRUPTED}
                        >
                          {d.result}
                        </Badge>
                      </TableCell>
                      <TableCell className="font-mono text-xs text-[#e4e4e7]">
                        {d.decision_id.substring(0, 16)}...
                      </TableCell>
                      <TableCell className="text-sm text-white">
                        {d.action}
                      </TableCell>
                      <TableCell className="text-xs text-[#818cf8] font-mono">
                        {d.agent_name}
                      </TableCell>
                      <TableCell>
                        {d.violations.length > 0 ? (
                          <span className="flex items-center gap-1 text-xs text-[#ef4444]">
                            <AlertTriangle className="h-3 w-3" />
                            {d.violations.length}
                          </span>
                        ) : (
                          <span className="text-xs text-[#71717a]">—</span>
                        )}
                      </TableCell>
                      <TableCell className="font-mono text-xs text-[#71717a]">
                        {d.duration_ms.toFixed(1)}ms
                      </TableCell>
                      <TableCell className="text-xs text-[#71717a]">
                        {formatDate(d.timestamp)}
                      </TableCell>
                      <TableCell>
                        <Link href={`/decisions/${d.decision_id}`}>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-[#6366f1] hover:text-[#818cf8]"
                          >
                            <ExternalLink className="h-4 w-4" />
                          </Button>
                        </Link>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              {/* Pagination */}
              <div className="flex items-center justify-between border-t border-[#1e1e2e] px-6 py-4">
                <span className="text-sm text-[#71717a]">
                  Page {data.page} of {data.total_pages} ({data.total} total)
                </span>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={page <= 1}
                    onClick={() => setPage(page - 1)}
                    className="border-[#1e1e2e] text-[#71717a] hover:text-white"
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={page >= (data?.total_pages ?? 1)}
                    onClick={() => setPage(page + 1)}
                    className="border-[#1e1e2e] text-[#71717a] hover:text-white"
                  >
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </>
          ) : (
            <div className="py-16 text-center text-[#71717a]">
              No decisions found. Run your first agent to see data here.
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function formatDate(ts: string): string {
  try {
    const d = new Date(ts);
    return d.toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false,
    });
  } catch {
    return ts;
  }
}
