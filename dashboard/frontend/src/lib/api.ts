// API client for the Chimera Compliance Dashboard backend

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

function getAuthHeader(): Record<string, string> {
  if (typeof window === "undefined") return {};
  const token = localStorage.getItem("chimera_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function fetchApi<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeader(),
      ...options?.headers,
    },
    ...options,
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "Unknown error");
    throw new ApiError(text, res.status);
  }

  return res.json();
}

// ========================================================================
// TYPES
// ========================================================================

import type {
  AuditStats,
  DecisionSummary,
  DecisionAuditRecord,
  PaginatedResponse,
  ViolationCount,
  PolicySummary,
  PolicyDetail,
  VerificationResult,
  ComplianceStatus,
  TrendDataPoint,
  HeatmapCell,
  AgentStat,
  DocSummary,
  DocDetail,
  AdminStats,
} from "./types";

// ========================================================================
// API
// ========================================================================

export const api = {
  // Health
  health: () => fetchApi<{ status: string }>("/health"),

  // ── Auth ──────────────────────────────────────────────────────────
  auth: {
    login: (email: string, password: string) =>
      fetchApi<{ access_token: string; user: unknown }>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      }),
    register: (email: string, password: string) =>
      fetchApi<{ access_token: string; user: unknown }>("/auth/register", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      }),
    me: () => fetchApi<{ user: unknown }>("/auth/me"),
  },

  // ── Audit ─────────────────────────────────────────────────────────
  getDecisions: (params?: {
    page?: number;
    limit?: number;
    result?: string;
    agent?: string;
    tier?: string;
  }) => {
    const searchParams = new URLSearchParams();
    if (params?.page) searchParams.set("page", String(params.page));
    if (params?.limit) searchParams.set("limit", String(params.limit));
    if (params?.result) searchParams.set("result", params.result);
    if (params?.agent) searchParams.set("agent", params.agent);
    if (params?.tier) searchParams.set("tier", params.tier);
    const qs = searchParams.toString();
    return fetchApi<PaginatedResponse<DecisionSummary>>(
      `/audit/decisions${qs ? `?${qs}` : ""}`
    );
  },

  getDecision: (id: string, tier: string = "free") =>
    fetchApi<DecisionAuditRecord | DecisionSummary>(
      `/audit/decisions/${id}?tier=${tier}`
    ),

  getStats: (tier: string = "free", lastDays?: number) => {
    const params = new URLSearchParams({ tier });
    if (lastDays) params.set("last_days", String(lastDays));
    return fetchApi<AuditStats>(`/audit/stats?${params}`);
  },

  getViolations: (n: number = 10, tier: string = "free") =>
    fetchApi<ViolationCount[]>(`/audit/violations?n=${n}&tier=${tier}`),

  getAgents: (tier: string = "free") =>
    fetchApi<{ agents: AgentStat[] }>(`/audit/agents?tier=${tier}`),

  // ── Policies ──────────────────────────────────────────────────────
  getPolicies: () =>
    fetchApi<{ policies: PolicySummary[] }>("/policies"),

  getPolicy: (filename: string) =>
    fetchApi<PolicyDetail>(`/policies/${filename}`),

  verifyPolicy: (filename: string) =>
    fetchApi<VerificationResult>(
      `/policies/${filename}/verify`,
      { method: "POST" }
    ),

  simulatePolicy: (filename: string, parameters: Record<string, unknown>) =>
    fetchApi<{
      result: string;
      duration_ms: number;
      violations: Array<{ constraint: string; explanation: string }>;
    }>(`/policies/${filename}/simulate`, {
      method: "POST",
      body: JSON.stringify(parameters),
    }),

  createPolicy: (filename: string, content: string) =>
    fetchApi<{ filename: string; status: string; message: string }>(
      "/policies",
      {
        method: "POST",
        body: JSON.stringify({ filename, content }),
      }
    ),

  getPolicyContent: (filename: string) =>
    fetchApi<{ filename: string; content: string }>(
      `/policies/${filename}/content`
    ),

  // ── Compliance ────────────────────────────────────────────────────
  getComplianceStatus: () =>
    fetchApi<ComplianceStatus>("/compliance/status"),

  // ── Analytics ─────────────────────────────────────────────────────
  getTrend: (granularity: string = "daily", lastDays: number = 30) =>
    fetchApi<{ data: TrendDataPoint[] }>(
      `/analytics/trend?granularity=${granularity}&last_days=${lastDays}`
    ),

  getHeatmap: (lastDays: number = 30) =>
    fetchApi<{ data: HeatmapCell[] }>(
      `/analytics/heatmap?last_days=${lastDays}`
    ),

  getPerformance: (lastDays: number = 30) =>
    fetchApi<{
      total_duration_ms: { min: number; max: number; mean: number; median: number; p95: number; count: number };
      llm_duration_ms: { min: number; max: number; mean: number; median: number; p95: number; count: number };
      policy_evaluation_ms: { min: number; max: number; mean: number; median: number; p95: number; count: number };
    }>(`/analytics/performance?last_days=${lastDays}`),

  getViolationTrend: (lastDays: number = 30) =>
    fetchApi<{ data: Array<{ date: string; violations: Record<string, number> }> }>(
      `/analytics/violations?last_days=${lastDays}`
    ),

  getCostEstimate: (lastDays: number = 30) =>
    fetchApi<{
      total_estimated_cost_usd: number;
      average_cost_per_decision: number;
      cost_by_model: Record<string, number>;
      cost_by_day: Array<{ date: string; cost: number; decisions: number }>;
      total_decisions: number;
    }>(`/analytics/cost-estimate?last_days=${lastDays}`),

  // ── Export ──────────────────────────────────────────────────────────
  exportDecisions: async (format: string = "json", tier: string = "free") => {
    const url = `${API_BASE}/audit/export?format=${format}&tier=${tier}`;
    const res = await fetch(url, {
      headers: { ...getAuthHeader() },
    });
    if (!res.ok) throw new Error("Export failed");
    const blob = await res.blob();
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `chimera-audit-${format}.json`;
    a.click();
    URL.revokeObjectURL(a.href);
  },

  // ── Docs ──────────────────────────────────────────────────────────
  getDocs: () =>
    fetchApi<{ docs: DocSummary[] }>("/docs"),

  getDoc: (slug: string) =>
    fetchApi<DocDetail>(`/docs/${slug}`),

  // ── Agents (Halt/Resume) ─────────────────────────────────────────
  getAgentsFull: (tier: string = "free") =>
    fetchApi<{ agents: Array<AgentStat & { halted: boolean; halted_at: string | null; halt_reason: string | null }> }>(
      `/agents?tier=${tier}`
    ),

  haltAgent: (agentName: string, reason: string = "Manual halt via dashboard") =>
    fetchApi<{ status: string; agent: string; reason: string; halted_at: string }>(
      `/agents/${encodeURIComponent(agentName)}/halt`,
      { method: "POST", body: JSON.stringify({ reason }) }
    ),

  resumeAgent: (agentName: string) =>
    fetchApi<{ status: string; agent: string }>(
      `/agents/${encodeURIComponent(agentName)}/resume`,
      { method: "POST" }
    ),

  // ── Settings / API Keys ─────────────────────────────────────────
  getApiKeys: () =>
    fetchApi<{ keys: Array<{ id: number; key_prefix: string; name: string; created_at: string; last_used: string | null; revoked: boolean }> }>(
      "/settings/api-keys"
    ),

  createApiKey: (name: string = "Default") =>
    fetchApi<{ key: string; key_prefix: string; name: string; id: number; created_at: string; message: string }>(
      "/settings/api-keys",
      { method: "POST", body: JSON.stringify({ name }) }
    ),

  revokeApiKey: (keyId: number) =>
    fetchApi<{ status: string; id: number }>(
      `/settings/api-keys/${keyId}`,
      { method: "DELETE" }
    ),

  // ── Admin ─────────────────────────────────────────────────────────
  getAdminStats: () =>
    fetchApi<AdminStats>("/leads/admin/stats"),

  getLeads: () =>
    fetchApi<{ leads: Array<{ id: number; email: string; name: string; company: string; plan: string; message: string; created_at: string }>; total: number }>(
      "/leads"
    ),
};

export default api;
