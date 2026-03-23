// TypeScript types mirroring Python chimera_runtime.models

export type DecisionResult = "ALLOWED" | "BLOCKED" | "HUMAN_OVERRIDE" | "INTERRUPTED";

export interface Violation {
  constraint: string;
  rule?: string;
  trigger_values?: Record<string, unknown>;
  explanation: string;
}

export interface PolicyEvaluation {
  policy_file: string;
  policy_hash: string;
  result: DecisionResult;
  duration_ms: number;
  violations: Violation[];
}

export interface Candidate {
  candidate_id: string;
  strategy: string;
  llm_reasoning: string;
  llm_confidence: number;
  parameters: Record<string, unknown>;
  policy_evaluation?: PolicyEvaluation;
}

export interface Attempt {
  attempt_number: number;
  candidates: Candidate[];
  outcome: string;
  note?: string;
}

export interface ReasoningTrace {
  total_candidates: number;
  total_attempts: number;
  attempts: Attempt[];
  selected_candidate?: string;
  selection_reasoning?: string;
}

export interface AgentInfo {
  name: string;
  version: string;
  csl_core_version: string;
  model: string;
  model_provider: string;
  temperature: number;
}

export interface InputInfo {
  raw_request: string;
  structured_params: Record<string, unknown>;
  context: Record<string, unknown>;
}

export interface DecisionInfo {
  action_taken: string;
  result: DecisionResult;
  final_parameters: Record<string, unknown>;
  policy_file: string;
  policy_hash: string;
}

export interface ComplianceInfo {
  eu_ai_act: Record<string, boolean>;
  formal_verification: {
    policy_verified: boolean;
    verification_engine: string;
    verification_result: string;
  };
  human_oversight: {
    override_available: boolean;
    stop_mechanism: boolean;
    policy_human_editable: boolean;
  };
}

export interface PerformanceInfo {
  total_duration_ms: number;
  llm_duration_ms: number;
  policy_evaluation_ms: number;
  audit_generation_ms: number;
}

export interface HumanOversightRecord {
  action: string;
  reason: string;
  override_decision?: string;
  timestamp: string;
}

export interface DecisionAuditRecord {
  schema_version: string;
  decision_id: string;
  timestamp: string;
  agent: AgentInfo;
  input: InputInfo;
  reasoning: ReasoningTrace;
  decision: DecisionInfo;
  compliance: ComplianceInfo;
  performance: PerformanceInfo;
  human_oversight_record?: HumanOversightRecord;
}

// Summary version for list views
export interface DecisionSummary {
  decision_id: string;
  timestamp: string;
  result: DecisionResult;
  action: string;
  policy_file: string;
  duration_ms: number;
  total_candidates: number;
  total_attempts: number;
  agent_name: string;
  model: string;
  violations: Violation[];
}

export interface AuditStats {
  total_decisions: number;
  allowed_count: number;
  blocked_count: number;
  human_override_count: number;
  interrupted_count: number;
  block_rate: number;
  allow_rate: number;
  avg_duration_ms: number;
  avg_latency_ms: number;
  avg_candidates_per_decision: number;
  avg_attempts_per_decision: number;
  total_violations: number;
  period_start: string;
  period_end: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

export interface PolicySummary {
  filename: string;
  domain_name: string;
  constraint_count: number;
  backend: string;
  hash: string;
  loaded: boolean;
  error?: boolean;
}

export interface PolicyDetail {
  filename: string;
  domain_name: string;
  constraint_count: number;
  constraint_names: string[];
  variable_names: string[];
  variable_domains: Record<string, string>;
  backend: string;
  hash: string;
  csl_core_available: boolean;
}

export interface ViolationCount {
  constraint: string;
  count: number;
}

export interface ComplianceStatus {
  compliant: boolean;
  score: string;
  articles: Record<string, boolean>;
  formal_verification: {
    policy_verified: boolean;
    verification_engine: string;
    verification_result: string;
  };
  human_oversight: {
    override_available: boolean;
    stop_mechanism: boolean;
    policy_human_editable: boolean;
  };
  total_decisions: number;
}

export interface TrendDataPoint {
  date: string;
  ALLOWED: number;
  BLOCKED: number;
  HUMAN_OVERRIDE: number;
  INTERRUPTED: number;
  total: number;
}

export interface HeatmapCell {
  day: string;
  day_index: number;
  hour: number;
  block_rate: number;
  total: number;
  blocked: number;
}

// ── Verification (Feature 1) ──────────────────────────────────────

export interface ConstraintResult {
  name: string;
  reachable: boolean;
  status: string;
}

export interface VerificationResult {
  filename: string;
  verified: boolean;
  messages: string[];
  backend: string;
  verification_engine: string;
  verification_time_ms: number;
  constraint_results: ConstraintResult[];
  csl_core_available: boolean;
}

// ── Multi-Agent (Feature 3) ───────────────────────────────────────

export interface AgentStat {
  name: string;
  total: number;
  allowed: number;
  blocked: number;
  avg_latency_ms: number;
}

// ── Admin Stats ─────────────────────────────────────────────────

export interface AdminStats {
  total_users: number;
  tier_distribution: Record<string, number>;
  total_leads: number;
  recent_users: Array<{
    id: number;
    email: string;
    tier: string;
    created_at: string;
    last_login: string | null;
  }>;
}

// ── Docs/Blog (Feature 6) ────────────────────────────────────────

export interface DocSummary {
  title: string;
  slug: string;
  category: string;
  excerpt: string;
  filename: string;
}

export interface DocDetail {
  title: string;
  slug: string;
  category: string;
  content: string;
}
