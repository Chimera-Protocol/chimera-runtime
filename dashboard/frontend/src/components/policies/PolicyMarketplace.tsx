"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Shield,
  DollarSign,
  Heart,
  Cpu,
  Server,
  Gamepad2,
  Lock,
  Bot,
  ExternalLink,
  GitPullRequest,
  User,
  Copy,
  Check,
  ChevronDown,
  ChevronUp,
  Globe,
  Landmark,
  ShoppingCart,
  FileCode,
  Sparkles,
} from "lucide-react";

// ── Category Definitions ─────────────────────────────────────

interface Category {
  id: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  borderColor: string;
  bgColor: string;
}

const CATEGORIES: Category[] = [
  { id: "all", label: "All Policies", icon: Globe, color: "text-white", borderColor: "border-white/20", bgColor: "bg-white/5" },
  { id: "finance", label: "Finance", icon: DollarSign, color: "text-[#22c55e]", borderColor: "border-[#22c55e]/30", bgColor: "bg-[#22c55e]/5" },
  { id: "healthcare", label: "Healthcare", icon: Heart, color: "text-[#ef4444]", borderColor: "border-[#ef4444]/30", bgColor: "bg-[#ef4444]/5" },
  { id: "defi", label: "DeFi / Web3", icon: Landmark, color: "text-[#a855f7]", borderColor: "border-[#a855f7]/30", bgColor: "bg-[#a855f7]/5" },
  { id: "devops", label: "DevOps", icon: Server, color: "text-[#3b82f6]", borderColor: "border-[#3b82f6]/30", bgColor: "bg-[#3b82f6]/5" },
  { id: "ai-safety", label: "AI Safety", icon: Shield, color: "text-[#f59e0b]", borderColor: "border-[#f59e0b]/30", bgColor: "bg-[#f59e0b]/5" },
  { id: "ecommerce", label: "E-Commerce", icon: ShoppingCart, color: "text-[#06b6d4]", borderColor: "border-[#06b6d4]/30", bgColor: "bg-[#06b6d4]/5" },
  { id: "gaming", label: "Gaming", icon: Gamepad2, color: "text-[#ec4899]", borderColor: "border-[#ec4899]/30", bgColor: "bg-[#ec4899]/5" },
];

// ── Policy Template Data ─────────────────────────────────────

interface PolicyTemplate {
  name: string;
  domain: string;
  description: string;
  category: string;
  constraints: number;
  author: string;
  authorGithub: string;
  source: "official" | "community";
  content: string;
}

const POLICY_TEMPLATES: PolicyTemplate[] = [
  // ── Official (by akarlaraytu) ──────────────────────────────
  {
    name: "Banking Transfer Guard",
    domain: "BankingGuard",
    description: "Comprehensive banking safety: sanctions screening, VIP/non-VIP transfer limits, risk ceilings, device trust, and KYC requirements.",
    category: "finance",
    constraints: 6,
    author: "Aytug Akarlar",
    authorGithub: "akarlaraytu",
    source: "official",
    content: `CONFIG {
  ENFORCEMENT_MODE: BLOCK
  CHECK_LOGICAL_CONSISTENCY: TRUE
}

DOMAIN BankingGuard {
  VARIABLES {
    action: {"TRANSFER", "WITHDRAW", "DEPOSIT"}
    amount: 0..100000
    country: {"TR", "US", "EU", "NK"}
    is_vip: {"TRUE", "FALSE"}
    kyc_level: 0..5
    risk_score: 0..1
    device_trust: 0..1
  }

  // Hard sanctions: NK must never appear
  STATE_CONSTRAINT no_sanctioned_country {
    WHEN country == country
    THEN country MUST NOT BE "NK"
  }

  // Non-VIP transfer hard limit
  STATE_CONSTRAINT transfer_limit_non_vip {
    WHEN action == "TRANSFER" AND is_vip == "FALSE"
    THEN amount <= 1000
  }

  // VIP transfer soft limit
  STATE_CONSTRAINT transfer_limit_vip {
    WHEN action == "TRANSFER" AND is_vip == "TRUE"
    THEN amount <= 10000
  }

  // Risk ceiling for transfers
  STATE_CONSTRAINT risk_ceiling_for_transfer {
    WHEN action == "TRANSFER"
    THEN risk_score <= 0.8
  }

  // Device trust for medium+ transfers
  STATE_CONSTRAINT device_trust_for_medium_transfer {
    WHEN action == "TRANSFER" AND amount > 300
    THEN device_trust >= 0.7
  }

  // KYC for larger withdrawals
  STATE_CONSTRAINT kyc_for_large_withdraw {
    WHEN action == "WITHDRAW" AND amount > 500
    THEN kyc_level >= 2
  }
}`,
  },
  {
    name: "Agent Tool Guard",
    domain: "AgentToolGuard",
    description: "Deterministic permission and parameter safety for AI agents. Controls tool access by role, enforces transfer limits, and blocks dangerous operations.",
    category: "ai-safety",
    constraints: 6,
    author: "Aytug Akarlar",
    authorGithub: "akarlaraytu",
    source: "official",
    content: `CONFIG {
  ENFORCEMENT_MODE: BLOCK
  CHECK_LOGICAL_CONSISTENCY: TRUE
}

DOMAIN AgentToolGuard {
  VARIABLES {
    user_role: {"ADMIN", "USER", "ANALYST"}
    tool: {"SEND_EMAIL", "TRANSFER_FUNDS", "QUERY_DB", "DELETE_RECORD"}
    amount: 0..100000
    recipient_domain: {"INTERNAL", "EXTERNAL"}
    pii_present: {"YES", "NO"}
    approval_token: {"YES", "NO"}
  }

  // Non-admin users cannot perform money transfers
  STATE_CONSTRAINT non_admin_no_transfer {
    WHEN user_role == "USER" OR user_role == "ANALYST"
    THEN tool MUST NOT BE "TRANSFER_FUNDS"
  }

  // Money transfers require explicit approval token
  STATE_CONSTRAINT transfer_requires_approval {
    WHEN tool == "TRANSFER_FUNDS" AND user_role == "ADMIN"
    THEN approval_token == "YES"
  }

  // Even admins have a hard transfer limit
  STATE_CONSTRAINT admin_transfer_limit {
    WHEN tool == "TRANSFER_FUNDS" AND user_role == "ADMIN"
    THEN amount <= 5000
  }

  // PII present = only internal email recipients
  STATE_CONSTRAINT no_external_email_with_pii {
    WHEN tool == "SEND_EMAIL" AND pii_present == "YES"
    THEN recipient_domain MUST NOT BE "EXTERNAL"
  }

  // SECRETS table is forbidden
  STATE_CONSTRAINT no_secrets_table_queries {
    WHEN tool == "QUERY_DB"
    THEN db_table MUST NOT BE "SECRETS"
  }

  // DELETE_RECORD is always forbidden
  STATE_CONSTRAINT no_delete_record_tool {
    ALWAYS True
    THEN tool MUST NOT BE "DELETE_RECORD"
  }
}`,
  },
  {
    name: "DAO Treasury Guard",
    domain: "DAOTreasury",
    description: "Governance rules for blockchain DAO treasury: reputation-based limits, multi-sig approval thresholds, timelock requirements, and emergency procedures.",
    category: "defi",
    constraints: 9,
    author: "Aytug Akarlar",
    authorGithub: "akarlaraytu",
    source: "official",
    content: `CONFIG {
  ENFORCEMENT_MODE: BLOCK
  CHECK_LOGICAL_CONSISTENCY: TRUE
}

DOMAIN DAOTreasury {
  VARIABLES {
    transfer_amount: 0..10000000
    total_balance: 0..100000000
    approval_count: 0..100
    proposer_reputation: 0..1000
    proposal_age_hours: 0..720
    destination_type: {"INTERNAL", "EXTERNAL", "BRIDGE", "MULTISIG"}
    action: {"TRANSFER", "GRANT", "INVESTMENT", "EMERGENCY"}
  }

  STATE_CONSTRAINT low_reputation_destination {
    WHEN proposer_reputation < 100
    THEN destination_type == "INTERNAL"
  }

  STATE_CONSTRAINT low_reputation_amount_limit {
    WHEN proposer_reputation < 100
    THEN transfer_amount <= 10000
  }

  STATE_CONSTRAINT external_transfer_approval {
    WHEN proposer_reputation >= 100 AND destination_type == "EXTERNAL" AND transfer_amount > 50000
    THEN approval_count >= 5
  }

  STATE_CONSTRAINT bridge_transfer_max_approval {
    WHEN proposer_reputation >= 100 AND destination_type == "BRIDGE" AND transfer_amount > 10000
    THEN approval_count >= 7
  }

  STATE_CONSTRAINT bridge_always_requires_timelock {
    WHEN proposer_reputation >= 100 AND destination_type == "BRIDGE" AND action != "EMERGENCY"
    THEN proposal_age_hours >= 24
  }

  STATE_CONSTRAINT catastrophic_transfer_protection {
    WHEN transfer_amount > (total_balance * 0.1) AND action != "EMERGENCY"
    THEN approval_count >= 3
  }

  STATE_CONSTRAINT large_transfer_timelock {
    WHEN transfer_amount > (total_balance * 0.05) AND action != "EMERGENCY"
    THEN proposal_age_hours >= 24
  }

  STATE_CONSTRAINT emergency_action_unanimous {
    WHEN action == "EMERGENCY"
    THEN approval_count >= 10
  }

  STATE_CONSTRAINT valid_proposal {
    WHEN transfer_amount > 0
    THEN proposal_id > 0
  }
}`,
  },
  {
    name: "OpenClaw Deterministic Gatekeeper",
    domain: "OpenClawGuard",
    description: "Production-grade 40+ constraint policy for OpenClaw AI agent framework. Covers deployment modes, sender trust, filesystem safety, browser security, PII protection, and supply chain defense.",
    category: "ai-safety",
    constraints: 40,
    author: "Aytug Akarlar",
    authorGithub: "akarlaraytu",
    source: "official",
    content: `// OpenClaw Deterministic Gatekeeper v1.0
// RFC #26348 Reference Implementation
// 40+ constraints covering:
// - Deployment mode hard blocks (EMBEDDED, UNATTENDED)
// - Sender trust levels (OWNER, PAIRED, UNPAIRED, UNKNOWN)
// - Meta inbox incident prevention
// - Filesystem path safety
// - Browser & network safety
// - Secrets & credentials
// - Supply chain protection
// - PII data protection
// - Remote node execution

// See full source at:
// github.com/Chimera-Protocol/csl-core/blob/main/examples/openclaw_guard.csl

CONFIG {
  ENFORCEMENT_MODE: BLOCK
  CHECK_LOGICAL_CONSISTENCY: TRUE
}

DOMAIN OpenClawGuard {
  VARIABLES {
    tool: {"bash", "exec", "read", "write", "edit", "glob",
           "apply_patch", "navigate", "screenshot", "click",
           "type", "evaluate", "fetch", "request", "download",
           "sendMessage", "gmail_send", "gmail_delete",
           "secrets_write", "node_exec", "cron",
           "skill_install", "camera_preview"}
    sender_role: {"OWNER", "PAIRED", "UNPAIRED", "UNKNOWN"}
    deployment_mode: {"DESKTOP", "SERVER", "EMBEDDED", "UNATTENDED"}
    target_count: 0..500
    path_in_workspace: {"YES", "NO"}
    domain_allowlisted: {"YES", "NO"}
    skill_verified: {"YES", "NO"}
    approval_granted: {"YES", "NO"}
    sandbox_active: {"YES", "NO"}
    pii_present: {"YES", "NO"}
  }

  // Embedded devices must not run arbitrary code
  STATE_CONSTRAINT embedded_no_bash {
    WHEN deployment_mode == "EMBEDDED"
    THEN tool MUST NOT BE "bash"
  }

  STATE_CONSTRAINT embedded_no_exec {
    WHEN deployment_mode == "EMBEDDED"
    THEN tool MUST NOT BE "exec"
  }

  // Untrusted senders: read-only tools only
  STATE_CONSTRAINT untrusted_no_bash {
    WHEN sender_role == "UNKNOWN" OR sender_role == "UNPAIRED"
    THEN tool MUST NOT BE "bash"
  }

  STATE_CONSTRAINT untrusted_no_write {
    WHEN sender_role == "UNKNOWN" OR sender_role == "UNPAIRED"
    THEN tool MUST NOT BE "write"
  }

  // Only verified skills can be installed
  STATE_CONSTRAINT unverified_skill_blocked {
    WHEN skill_verified == "NO"
    THEN tool MUST NOT BE "skill_install"
  }

  // PII to non-allowlisted destinations: hard block
  STATE_CONSTRAINT pii_fetch_unknown_blocked {
    WHEN pii_present == "YES" AND domain_allowlisted == "NO"
    THEN tool MUST NOT BE "fetch"
  }

  // Remote execution requires sandbox
  STATE_CONSTRAINT node_exec_no_sandbox {
    WHEN sandbox_active == "NO"
    THEN tool MUST NOT BE "node_exec"
  }

  // ... 33 more constraints in full version
}`,
  },

  // ── Community Contributions ────────────────────────────────
  {
    name: "API Budget Manager",
    domain: "ApiBudgetManager",
    description: "Enforce API spending limits by user tier. FREE users capped at $5/day, PRO users at $100/month cumulative.",
    category: "finance",
    constraints: 2,
    author: "Luis Fuentes",
    authorGithub: "luisayan100",
    source: "community",
    content: `CONFIG {
  ENFORCEMENT_MODE: BLOCK
  CHECK_LOGICAL_CONSISTENCY: TRUE
}

DOMAIN ApiBudgetManager {
  VARIABLES {
    user_tier: {"ENTERPRISE", "PRO", "FREE"}
    daily_spend: 0.0..100000.0
    monthly_cumulative: 0.0..1000000.0
  }

  // FREE users cannot exceed daily spend limit
  STATE_CONSTRAINT free_daily_limit {
    WHEN user_tier == "FREE"
    THEN daily_spend <= 5.0
  }

  // PRO users cannot exceed monthly cumulative limit
  STATE_CONSTRAINT pro_monthly_limit {
    WHEN user_tier == "PRO"
    THEN monthly_cumulative <= 100.0
  }
}`,
  },
  {
    name: "DeFi Slippage Guard",
    domain: "DeFiSlippageGuard",
    description: "Protect DeFi trading bots from high slippage, sandwich attacks, and unverified token pools. Hard cap at 5% price impact.",
    category: "defi",
    constraints: 3,
    author: "sohamzope18",
    authorGithub: "sohamzope18",
    source: "community",
    content: `CONFIG {
  ENFORCEMENT_MODE: BLOCK
}

DOMAIN DeFiSlippageGuard {
  VARIABLES {
    price_impact: 0.0..100.0
    slippage_tolerance: 0.0..100.0
    is_verified_pool: BOOLEAN
  }

  // BLOCK if price_impact exceeds user's slippage tolerance
  STATE_CONSTRAINT enforce_user_slippage {
    WHEN price_impact == price_impact
    THEN price_impact <= slippage_tolerance
  }

  // Hard cap at 5% price impact
  STATE_CONSTRAINT enforce_hard_cap {
    WHEN price_impact == price_impact
    THEN price_impact <= 5.0
  }

  // Only verified pools allowed
  STATE_CONSTRAINT require_verified_pool {
    WHEN is_verified_pool == is_verified_pool
    THEN is_verified_pool MUST BE TRUE
  }
}`,
  },
  {
    name: "DeFi Trading Guard",
    domain: "DeFiTradingGuard",
    description: "Full trading bot protection policy with slippage enforcement, hard caps, and pool verification requirements.",
    category: "defi",
    constraints: 3,
    author: "sohamzope18",
    authorGithub: "sohamzope18",
    source: "community",
    content: `CONFIG {
  ENFORCEMENT_MODE: BLOCK
}

DOMAIN DeFiTradingGuard {
  VARIABLES {
    price_impact: 0.0..100.0
    slippage_tolerance: 0.0..100.0
    is_verified_pool: BOOLEAN
  }

  STATE_CONSTRAINT enforce_user_slippage {
    WHEN price_impact == price_impact
    THEN price_impact <= slippage_tolerance
  }

  STATE_CONSTRAINT enforce_hard_cap {
    WHEN price_impact == price_impact
    THEN price_impact <= 5.0
  }

  STATE_CONSTRAINT require_verified_pool {
    WHEN is_verified_pool == is_verified_pool
    THEN is_verified_pool MUST BE TRUE
  }
}`,
  },
  {
    name: "DevOps Deploy Guard",
    domain: "DevOpsGuard",
    description: "Block risky deployments to PROD on Fridays after 4 PM. The classic 'No Deploy Friday' policy, formally verified.",
    category: "devops",
    constraints: 1,
    author: "sohamzope18",
    authorGithub: "sohamzope18",
    source: "community",
    content: `CONFIG {
  ENFORCEMENT_MODE: BLOCK
}

DOMAIN DevOpsGuard {
  VARIABLES {
    target_env: {"STAGING", "PROD", "DEV"}
    day_of_week: {"MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"}
    current_hour: 0..23
  }

  // No deployments to PROD on Fridays at or after 16:00
  STATE_CONSTRAINT prevent_friday_late_deploys {
    WHEN day_of_week == "FRIDAY" AND current_hour >= 16
    THEN target_env MUST NOT BE "PROD"
  }
}`,
  },
  {
    name: "E-Commerce Margin Guard",
    domain: "EcommerceMarginGuard",
    description: "Prevent AI pricing agents from setting prices below cost plus minimum margin. Protects profit margins deterministically.",
    category: "ecommerce",
    constraints: 1,
    author: "Thomas Cornejo",
    authorGithub: "ThomasCornejo",
    source: "community",
    content: `CONFIG {
  ENFORCEMENT_MODE: BLOCK
  CHECK_LOGICAL_CONSISTENCY: TRUE
}

DOMAIN EcommerceMarginGuard {
  VARIABLES {
    unit_cost: 0.0..1000000.0
    suggested_price: 0.0..1000000.0
    min_margin_percent: 0.0..1.0
  }

  // BLOCK if suggested_price is below minimum acceptable price
  // Minimum = unit_cost * (1 + min_margin_percent)
  STATE_CONSTRAINT enforce_minimum_margin {
    ALWAYS True
    THEN suggested_price >= unit_cost * (1 + min_margin_percent)
  }
}`,
  },
  {
    name: "Game NPC Rules of Engagement",
    domain: "GameNpcROE",
    description: "Prevent friendly fire and enforce ceasefire agreements in game NPC AI behavior. No attacking same-faction or peace-treaty targets.",
    category: "gaming",
    constraints: 2,
    author: "Luis Fuentes",
    authorGithub: "luisayan100",
    source: "community",
    content: `CONFIG {
  ENFORCEMENT_MODE: BLOCK
  CHECK_LOGICAL_CONSISTENCY: TRUE
}

DOMAIN GameNpcROE {
  VARIABLES {
    target_faction: String
    my_faction: String
    has_peace_treaty: {"TRUE", "FALSE"}
  }

  // No friendly fire — cannot attack own faction
  STATE_CONSTRAINT no_friendly_fire {
    ALWAYS True
    THEN target_faction != my_faction
  }

  // Honor ceasefire agreements
  STATE_CONSTRAINT honor_ceasefire {
    ALWAYS True
    THEN has_peace_treaty != "TRUE"
  }
}`,
  },
  {
    name: "Pediatric Safety Guard",
    domain: "PediatricSafetyGuard",
    description: "Block unsafe pediatric dosing for antibiotics. Children under 12 cannot receive more than 250mg of Antibiotic A.",
    category: "healthcare",
    constraints: 1,
    author: "Luis Fuentes",
    authorGithub: "luisayan100",
    source: "community",
    content: `CONFIG {
  ENFORCEMENT_MODE: BLOCK
  CHECK_LOGICAL_CONSISTENCY: TRUE
}

DOMAIN PediatricSafetyGuard {
  VARIABLES {
    patient_age: 0..120
    dosage_mg: 0..10000
    drug_type: String
  }

  // Block unsafe pediatric antibiotic dosing
  STATE_CONSTRAINT pediatric_antibiotic_a_max_dose {
    WHEN drug_type == "ANTIBIOTIC_A" AND patient_age < 12
    THEN dosage_mg <= 250
  }
}`,
  },
  {
    name: "PII Output Guard",
    domain: "PiiOutputGuard",
    description: "Block agent responses containing PII or low-confidence outputs. Enforces minimum 70% confidence score and zero PII leakage.",
    category: "ai-safety",
    constraints: 2,
    author: "Luis Fuentes",
    authorGithub: "luisayan100",
    source: "community",
    content: `CONFIG {
  ENFORCEMENT_MODE: BLOCK
  CHECK_LOGICAL_CONSISTENCY: TRUE
}

DOMAIN PiiOutputGuard {
  VARIABLES {
    output_text: String
    pii_detected: BOOLEAN
    confidence_score: 0.0..1.0
  }

  // BLOCK if PII is detected in output
  STATE_CONSTRAINT no_pii_in_output {
    ALWAYS True
    THEN pii_detected == FALSE
  }

  // BLOCK if confidence is below 0.70
  STATE_CONSTRAINT minimum_confidence {
    ALWAYS True
    THEN confidence_score >= 0.70
  }
}`,
  },
];

// ── CSL Syntax Highlighter ───────────────────────────────────

function highlightCSL(code: string): React.ReactNode[] {
  return code.split("\n").map((line, i) => {
    let highlighted = line;

    // Comments
    if (line.trimStart().startsWith("//")) {
      return <span key={i} className="text-[#71717a]">{line}{"\n"}</span>;
    }

    // Simple token replacement
    const parts: React.ReactNode[] = [];
    let remaining = line;
    let keyIdx = 0;

    // Keywords
    const keywords = ["CONFIG", "DOMAIN", "VARIABLES", "STATE_CONSTRAINT", "WHEN", "THEN", "ALWAYS", "MUST BE", "MUST NOT BE", "MAY BE", "AND", "OR", "NOT"];
    const types = ["BLOCK", "WARN", "LOG", "TRUE", "FALSE", "BOOLEAN", "Int", "Nat", "String", "ENFORCEMENT_MODE", "CHECK_LOGICAL_CONSISTENCY"];

    // Build regex
    const kwPattern = keywords.map(k => k.replace(/\s+/g, "\\s+")).join("|");
    const tyPattern = types.join("|");
    const fullPattern = new RegExp(
      `(//.*$)|("(?:[^"\\\\]|\\\\.)*")|(\\b(?:${kwPattern})\\b)|(\\b(?:${tyPattern})\\b)|(\\b\\d+(?:\\.\\d+)?\\b)`,
      "g"
    );

    let lastIndex = 0;
    let match;
    const regex = new RegExp(fullPattern);

    while ((match = regex.exec(remaining)) !== null) {
      // Text before match
      if (match.index > lastIndex) {
        parts.push(<span key={`${i}-${keyIdx++}`} className="text-[#e4e4e7]">{remaining.slice(lastIndex, match.index)}</span>);
      }

      if (match[1]) {
        // Comment
        parts.push(<span key={`${i}-${keyIdx++}`} className="text-[#71717a]">{match[0]}</span>);
      } else if (match[2]) {
        // String
        parts.push(<span key={`${i}-${keyIdx++}`} className="text-[#22c55e]">{match[0]}</span>);
      } else if (match[3]) {
        // Keyword
        parts.push(<span key={`${i}-${keyIdx++}`} className="text-[#c084fc] font-semibold">{match[0]}</span>);
      } else if (match[4]) {
        // Type
        parts.push(<span key={`${i}-${keyIdx++}`} className="text-[#818cf8]">{match[0]}</span>);
      } else if (match[5]) {
        // Number
        parts.push(<span key={`${i}-${keyIdx++}`} className="text-[#f59e0b]">{match[0]}</span>);
      } else {
        parts.push(<span key={`${i}-${keyIdx++}`} className="text-[#e4e4e7]">{match[0]}</span>);
      }

      lastIndex = regex.lastIndex;
    }

    if (lastIndex < remaining.length) {
      parts.push(<span key={`${i}-${keyIdx++}`} className="text-[#e4e4e7]">{remaining.slice(lastIndex)}</span>);
    }

    return <span key={i}>{parts.length > 0 ? parts : <span className="text-[#e4e4e7]">{line}</span>}{"\n"}</span>;
  });
}

// ── Copy Button ──────────────────────────────────────────────

function CopyBtn({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      onClick={() => {
        navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      }}
      className="absolute top-3 right-3 p-1.5 rounded-md bg-white/5 hover:bg-white/10 transition-colors"
    >
      {copied ? <Check className="h-3.5 w-3.5 text-[#22c55e]" /> : <Copy className="h-3.5 w-3.5 text-[#71717a]" />}
    </button>
  );
}

// ── Policy Card ──────────────────────────────────────────────

function PolicyCard({ policy, index }: { policy: PolicyTemplate; index: number }) {
  const [expanded, setExpanded] = useState(false);
  const [copied, setCopied] = useState(false);
  const cat = CATEGORIES.find(c => c.id === policy.category) || CATEGORIES[0];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05, duration: 0.3 }}
    >
      <Card className="border-[#1e1e2e] bg-[#111119] hover:border-[#2e2e3e] transition-all duration-300 group">
        <CardContent className="p-5">
          {/* Header */}
          <div className="flex items-start justify-between gap-3">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <h3 className="text-sm font-semibold text-white truncate">{policy.name}</h3>
                {policy.source === "official" && (
                  <Badge variant="outline" className="border-[#6366f1]/30 text-[#818cf8] text-[9px] px-1.5 shrink-0">
                    OFFICIAL
                  </Badge>
                )}
                {policy.source === "community" && (
                  <Badge variant="outline" className="border-[#22c55e]/30 text-[#22c55e] text-[9px] px-1.5 shrink-0">
                    COMMUNITY
                  </Badge>
                )}
              </div>
              <p className="mt-1 text-xs text-[#71717a] line-clamp-2">{policy.description}</p>
            </div>
            <Badge variant="outline" className={`${cat.borderColor} ${cat.color} text-[9px] px-1.5 shrink-0`}>
              <cat.icon className="h-3 w-3 mr-1" />
              {cat.label}
            </Badge>
          </div>

          {/* Meta */}
          <div className="mt-3 flex items-center gap-4 text-[11px] text-[#71717a]">
            <span className="flex items-center gap-1">
              <Lock className="h-3 w-3" />
              {policy.constraints} constraint{policy.constraints !== 1 ? "s" : ""}
            </span>
            <span className="flex items-center gap-1">
              <FileCode className="h-3 w-3" />
              {policy.domain}
            </span>
            <a
              href={`https://github.com/${policy.authorGithub}`}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 hover:text-[#818cf8] transition-colors ml-auto"
              onClick={e => e.stopPropagation()}
            >
              <User className="h-3 w-3" />
              @{policy.authorGithub}
              <ExternalLink className="h-2.5 w-2.5" />
            </a>
          </div>

          {/* Actions */}
          <div className="mt-3 flex items-center gap-2">
            <button
              onClick={() => setExpanded(!expanded)}
              className="flex items-center gap-1.5 text-[11px] text-[#818cf8] hover:text-[#a5b4fc] transition-colors"
            >
              {expanded ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
              {expanded ? "Hide Code" : "View Code"}
            </button>
            <button
              onClick={() => {
                navigator.clipboard.writeText(policy.content);
                setCopied(true);
                setTimeout(() => setCopied(false), 2000);
              }}
              className="flex items-center gap-1.5 text-[11px] text-[#71717a] hover:text-white transition-colors ml-auto"
            >
              {copied ? <Check className="h-3 w-3 text-[#22c55e]" /> : <Copy className="h-3 w-3" />}
              {copied ? "Copied!" : "Copy CSL"}
            </button>
          </div>

          {/* Expandable Code */}
          <AnimatePresence>
            {expanded && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.3 }}
                className="overflow-hidden"
              >
                <div className="mt-3 relative rounded-lg border border-[#1e1e2e] bg-[#0a0a0f] overflow-hidden">
                  <CopyBtn text={policy.content} />
                  <pre className="p-4 text-xs leading-relaxed overflow-x-auto max-h-[400px] overflow-y-auto scrollbar-thin">
                    <code>{highlightCSL(policy.content)}</code>
                  </pre>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </CardContent>
      </Card>
    </motion.div>
  );
}

// ── Main Marketplace Component ───────────────────────────────

export function PolicyMarketplace() {
  const [activeCategory, setActiveCategory] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");

  const filtered = POLICY_TEMPLATES.filter(p => {
    const matchesCategory = activeCategory === "all" || p.category === activeCategory;
    const matchesSearch = searchQuery === "" ||
      p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.domain.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.author.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  const officialCount = filtered.filter(p => p.source === "official").length;
  const communityCount = filtered.filter(p => p.source === "community").length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-white flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-[#818cf8]" />
            CSL Policy Marketplace
          </h2>
          <p className="mt-1 text-sm text-[#71717a]">
            Browse, copy, and learn from verified CSL policies. Use them as templates for your own.
          </p>
        </div>
        <a
          href="https://github.com/Chimera-Protocol/csl-core/tree/main/examples/community"
          target="_blank"
          rel="noopener noreferrer"
        >
          <motion.div
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[#22c55e]/10 border border-[#22c55e]/30 text-[#22c55e] text-sm font-medium hover:bg-[#22c55e]/20 transition-colors cursor-pointer"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <GitPullRequest className="h-4 w-4" />
            Submit Your Policy
          </motion.div>
        </a>
      </div>

      {/* Submit Info */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="rounded-lg border border-[#22c55e]/20 bg-[#22c55e]/5 px-4 py-3 flex items-start gap-3"
      >
        <GitPullRequest className="h-4 w-4 text-[#22c55e] mt-0.5 shrink-0" />
        <div className="text-xs text-[#22c55e]/80 leading-relaxed">
          <strong className="text-[#22c55e]">Want your policy listed here?</strong>{" "}
          Submit a PR to the{" "}
          <a
            href="https://github.com/Chimera-Protocol/csl-core/tree/main/examples/community"
            target="_blank"
            rel="noopener noreferrer"
            className="underline hover:text-[#22c55e] transition-colors"
          >
            CSL-Core repository
          </a>{" "}
          under <code className="px-1 py-0.5 rounded bg-[#22c55e]/10 text-[#22c55e] font-mono">examples/community/</code>.
          Your GitHub username will be displayed as the author.
        </div>
      </motion.div>

      {/* Search */}
      <div className="relative">
        <input
          type="text"
          value={searchQuery}
          onChange={e => setSearchQuery(e.target.value)}
          placeholder="Search policies by name, domain, description, or author..."
          className="w-full bg-[#0a0a0f] border border-[#1e1e2e] rounded-lg px-4 py-2.5 text-white placeholder:text-[#52525b] focus:border-[#6366f1] focus:ring-1 focus:ring-[#6366f1] outline-none text-sm"
        />
      </div>

      {/* Category Pills */}
      <div className="flex flex-wrap gap-2">
        {CATEGORIES.map(cat => (
          <button
            key={cat.id}
            onClick={() => setActiveCategory(cat.id)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              activeCategory === cat.id
                ? `${cat.bgColor} ${cat.borderColor} ${cat.color} border`
                : "text-[#71717a] border border-transparent hover:border-[#1e1e2e] hover:text-white"
            }`}
          >
            <cat.icon className="h-3.5 w-3.5" />
            {cat.label}
          </button>
        ))}
      </div>

      {/* Stats */}
      <div className="flex items-center gap-4 text-xs text-[#71717a]">
        <span>{filtered.length} polic{filtered.length !== 1 ? "ies" : "y"}</span>
        <span className="text-[#1e1e2e]">|</span>
        <span className="flex items-center gap-1">
          <Shield className="h-3 w-3 text-[#818cf8]" />
          {officialCount} official
        </span>
        <span className="flex items-center gap-1">
          <User className="h-3 w-3 text-[#22c55e]" />
          {communityCount} community
        </span>
      </div>

      {/* Policy Grid */}
      <div className="grid gap-4 md:grid-cols-2">
        {filtered.map((policy, i) => (
          <PolicyCard key={`${policy.domain}-${policy.authorGithub}`} policy={policy} index={i} />
        ))}
      </div>

      {filtered.length === 0 && (
        <div className="text-center py-12 text-[#71717a]">
          <FileCode className="h-8 w-8 mx-auto mb-3 opacity-50" />
          <p className="text-sm">No policies found matching your search.</p>
        </div>
      )}
    </div>
  );
}
