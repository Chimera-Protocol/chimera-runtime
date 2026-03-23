"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import {
  BookOpen,
  Code2,
  Shield,
  Zap,
  Layers,
  CheckCircle2,
  ArrowLeft,
  Lightbulb,
  Rocket,
  Binary,
  Hash,
  ToggleLeft,
  List,
  AlertTriangle,
  Lock,
  Vote,
  UserCheck,
  Bot,
  ChevronRight,
  Terminal,
  Braces,
  FileCode,
  CircleDot,
} from "lucide-react";
import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

// ---------------------------------------------------------------------------
// Sparkle effect for hero
// ---------------------------------------------------------------------------
function SparkleEffect() {
  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {Array.from({ length: 20 }).map((_, i) => (
        <motion.div
          key={i}
          className="absolute w-1 h-1 rounded-full bg-indigo-400/60"
          style={{
            left: `${Math.random() * 100}%`,
            top: `${Math.random() * 100}%`,
          }}
          animate={{
            opacity: [0, 1, 0],
            scale: [0, 1.5, 0],
          }}
          transition={{
            duration: 2 + Math.random() * 2,
            repeat: Infinity,
            delay: Math.random() * 3,
          }}
        />
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// CSL Syntax Highlighter
// ---------------------------------------------------------------------------
function highlightCSL(code: string): React.ReactNode[] {
  const lines = code.split("\n");

  const keywords = [
    "CONFIG",
    "DOMAIN",
    "VARIABLES",
    "STATE_CONSTRAINT",
    "WHEN",
    "THEN",
    "MUST BE",
    "MUST NOT BE",
    "MAY BE",
    "ALWAYS",
    "BEFORE",
    "AFTER",
    "EVENTUALLY",
    "AND",
    "OR",
    "NOT",
    "ENFORCEMENT_MODE",
    "CHECK_LOGICAL_CONSISTENCY",
  ];

  const types = ["BLOCK", "WARN", "LOG", "TRUE", "FALSE", "BOOLEAN", "Int", "Nat"];

  function highlightLine(line: string): React.ReactNode[] {
    // Handle full-line comments
    const commentIdx = line.indexOf("//");
    let mainPart = line;
    let commentPart: string | null = null;
    if (commentIdx !== -1) {
      mainPart = line.slice(0, commentIdx);
      commentPart = line.slice(commentIdx);
    }

    const nodes: React.ReactNode[] = [];
    let remaining = mainPart;
    let key = 0;

    while (remaining.length > 0) {
      let earliestMatch: { idx: number; len: number; type: string; text: string } | null = null;

      // Check keywords
      for (const kw of keywords) {
        const regex = new RegExp(`\\b${kw}\\b`);
        const m = remaining.match(regex);
        if (m && m.index !== undefined) {
          if (!earliestMatch || m.index < earliestMatch.idx) {
            earliestMatch = { idx: m.index, len: kw.length, type: "keyword", text: kw };
          }
        }
      }

      // Check types
      for (const t of types) {
        const regex = new RegExp(`\\b${t}\\b`);
        const m = remaining.match(regex);
        if (m && m.index !== undefined) {
          if (!earliestMatch || m.index < earliestMatch.idx) {
            earliestMatch = { idx: m.index, len: t.length, type: "type", text: t };
          }
        }
      }

      // Check strings
      const strMatch = remaining.match(/"([^"]*)"/);
      if (strMatch && strMatch.index !== undefined) {
        if (!earliestMatch || strMatch.index < earliestMatch.idx) {
          earliestMatch = {
            idx: strMatch.index,
            len: strMatch[0].length,
            type: "string",
            text: strMatch[0],
          };
        }
      }

      // Check numbers
      const numMatch = remaining.match(/\b(\d+\.?\d*)\b/);
      if (numMatch && numMatch.index !== undefined) {
        // Make sure this isn't inside an identifier
        const before = remaining[numMatch.index - 1];
        const isPartOfIdent = before && /[a-zA-Z_]/.test(before);
        if (!isPartOfIdent) {
          if (!earliestMatch || numMatch.index < earliestMatch.idx) {
            earliestMatch = {
              idx: numMatch.index,
              len: numMatch[0].length,
              type: "number",
              text: numMatch[0],
            };
          }
        }
      }

      if (earliestMatch) {
        // Add text before the match
        if (earliestMatch.idx > 0) {
          nodes.push(
            <span key={key++} className="text-[#e4e4e7]">
              {remaining.slice(0, earliestMatch.idx)}
            </span>
          );
        }

        // Add the match
        const colorMap: Record<string, string> = {
          keyword: "text-[#c084fc]",
          string: "text-[#22c55e]",
          number: "text-[#f59e0b]",
          type: "text-[#818cf8]",
        };
        nodes.push(
          <span key={key++} className={colorMap[earliestMatch.type]}>
            {earliestMatch.text}
          </span>
        );

        remaining = remaining.slice(earliestMatch.idx + earliestMatch.len);
      } else {
        nodes.push(
          <span key={key++} className="text-[#e4e4e7]">
            {remaining}
          </span>
        );
        remaining = "";
      }
    }

    if (commentPart) {
      nodes.push(
        <span key={key++} className="text-[#71717a]">
          {commentPart}
        </span>
      );
    }

    return nodes;
  }

  return lines.map((line, i) => (
    <div key={i} className="leading-relaxed">
      {highlightLine(line)}
    </div>
  ));
}

// ---------------------------------------------------------------------------
// Code Block component
// ---------------------------------------------------------------------------
function CodeBlock({
  code,
  title,
  className = "",
}: {
  code: string;
  title?: string;
  className?: string;
}) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div
      className={`rounded-xl border border-white/10 bg-[#0d0d14] overflow-hidden ${className}`}
    >
      {title && (
        <div className="flex items-center justify-between px-4 py-2 border-b border-white/10 bg-white/[0.02]">
          <div className="flex items-center gap-2">
            <Terminal className="w-3.5 h-3.5 text-[#71717a]" />
            <span className="text-xs text-[#71717a] font-mono">{title}</span>
          </div>
          <button
            onClick={handleCopy}
            className="text-xs text-[#71717a] hover:text-white transition-colors px-2 py-0.5 rounded hover:bg-white/5"
          >
            {copied ? "Copied!" : "Copy"}
          </button>
        </div>
      )}
      <pre className="p-4 text-sm font-mono overflow-x-auto">{highlightCSL(code)}</pre>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Section wrapper with scroll animation
// ---------------------------------------------------------------------------
function Section({
  children,
  className = "",
  id,
}: {
  children: React.ReactNode;
  className?: string;
  id?: string;
}) {
  return (
    <motion.section
      id={id}
      initial={{ opacity: 0, y: 40 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-80px" }}
      transition={{ duration: 0.6, ease: "easeOut" }}
      className={`${className}`}
    >
      {children}
    </motion.section>
  );
}

// ---------------------------------------------------------------------------
// Glass card
// ---------------------------------------------------------------------------
function GlassCard({
  children,
  className = "",
  delay = 0,
}: {
  children: React.ReactNode;
  className?: string;
  delay?: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.5, delay, ease: "easeOut" }}
      className={`rounded-2xl border border-white/10 bg-white/[0.03] backdrop-blur-xl p-6 ${className}`}
    >
      {children}
    </motion.div>
  );
}

// ---------------------------------------------------------------------------
// Section heading
// ---------------------------------------------------------------------------
function SectionHeading({
  icon: Icon,
  title,
  subtitle,
  badge,
}: {
  icon: React.ElementType;
  title: string;
  subtitle?: string;
  badge?: string;
}) {
  return (
    <div className="mb-8">
      <div className="flex items-center gap-3 mb-3">
        <div className="p-2 rounded-lg bg-indigo-500/10 border border-indigo-500/20">
          <Icon className="w-5 h-5 text-indigo-400" />
        </div>
        <h2 className="text-2xl md:text-3xl font-bold text-white">{title}</h2>
        {badge && (
          <Badge variant="outline" className="border-indigo-500/30 text-indigo-400 text-xs">
            {badge}
          </Badge>
        )}
      </div>
      {subtitle && <p className="text-[#a1a1aa] text-lg ml-12">{subtitle}</p>}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Operator table row
// ---------------------------------------------------------------------------
function OpRow({
  category,
  operators,
  color,
}: {
  category: string;
  operators: { op: string; desc: string }[];
  color: string;
}) {
  return (
    <div className="border-b border-white/5 last:border-b-0">
      <div className="px-4 py-3 flex items-start gap-4">
        <Badge
          variant="outline"
          className={`${color} border-current/30 text-xs shrink-0 mt-0.5`}
        >
          {category}
        </Badge>
        <div className="flex flex-wrap gap-3">
          {operators.map((o) => (
            <div key={o.op} className="flex items-center gap-1.5">
              <code className="text-sm font-mono text-white bg-white/5 px-1.5 py-0.5 rounded">
                {o.op}
              </code>
              <span className="text-xs text-[#71717a]">{o.desc}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------
export default function LearnCSLPage() {
  return (
    <div className="min-h-screen bg-[#0a0a0f] relative">
      {/* Floating back button */}
      <Link href="/dashboard">
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="fixed top-6 left-6 z-50 flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 backdrop-blur-xl border border-white/10 text-sm text-[#a1a1aa] hover:text-white hover:bg-white/10 transition-all cursor-pointer"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Dashboard
        </motion.div>
      </Link>

      <div className="max-w-5xl mx-auto px-4 sm:px-6 pb-24">
        {/* ================================================================
            HERO SECTION
        ================================================================ */}
        <section className="relative pt-24 pb-16 text-center">
          <SparkleEffect />

          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <Badge
              variant="outline"
              className="border-indigo-500/30 text-indigo-400 mb-6 text-xs"
            >
              <BookOpen className="w-3 h-3 mr-1" />
              Documentation
            </Badge>

            <h1 className="text-5xl md:text-7xl font-extrabold mb-4 bg-gradient-to-r from-indigo-400 via-purple-400 to-cyan-400 bg-clip-text text-transparent leading-tight">
              Learn CSL
            </h1>

            <p className="text-xl md:text-2xl text-[#a1a1aa] max-w-2xl mx-auto mb-2">
              Master the Chimera Specification Language
            </p>
            <p className="text-[#71717a] max-w-xl mx-auto">
              A deterministic, formally-verified DSL for writing AI agent compliance
              policies. Define constraints, verify with Z3, and deploy with confidence.
            </p>
          </motion.div>

          {/* Navigation pills */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="flex flex-wrap justify-center gap-2 mt-10"
          >
            {[
              { label: "Quick Start", href: "#quickstart" },
              { label: "Variables", href: "#variables" },
              { label: "Constraints", href: "#constraints" },
              { label: "Examples", href: "#examples" },
              { label: "Operators", href: "#operators" },
              { label: "Tips", href: "#tips" },
            ].map((item) => (
              <a
                key={item.label}
                href={item.href}
                className="px-4 py-1.5 rounded-full text-sm border border-white/10 text-[#a1a1aa] hover:text-white hover:border-indigo-500/40 hover:bg-indigo-500/5 transition-all"
              >
                {item.label}
              </a>
            ))}
          </motion.div>
        </section>

        <Separator className="bg-white/5 mb-16" />

        {/* ================================================================
            WHAT IS CSL?
        ================================================================ */}
        <Section id="what-is-csl" className="mb-20">
          <SectionHeading
            icon={Shield}
            title="What is CSL?"
            subtitle="The policy language that keeps AI agents in check"
          />

          <GlassCard>
            <div className="flex flex-col md:flex-row gap-6">
              <div className="flex-1">
                <p className="text-[#e4e4e7] leading-relaxed mb-4">
                  <strong className="text-white">CSL (Chimera Specification Language)</strong> is a
                  domain-specific language designed for writing deterministic compliance policies for
                  AI agents. Every policy is compiled to an intermediate representation (IR) and
                  formally verified using the <strong className="text-cyan-400">Z3 theorem prover</strong> to
                  guarantee logical consistency before deployment.
                </p>
                <p className="text-[#a1a1aa] leading-relaxed">
                  CSL policies act as runtime guardrails. When an AI agent attempts an action, the
                  ChimeraRuntime evaluates the action context against your constraints and returns a
                  deterministic <span className="text-green-400">ALLOW</span> or{" "}
                  <span className="text-red-400">BLOCK</span> decision in under 1ms.
                </p>
              </div>
              <div className="flex flex-col gap-3 md:min-w-[220px]">
                {[
                  { icon: Zap, label: "Sub-millisecond evaluation" },
                  { icon: Shield, label: "Z3 formal verification" },
                  { icon: Code2, label: "Compiled to IR" },
                  { icon: Layers, label: "Composable domains" },
                ].map((item, i) => (
                  <motion.div
                    key={item.label}
                    initial={{ opacity: 0, x: 20 }}
                    whileInView={{ opacity: 1, x: 0 }}
                    viewport={{ once: true }}
                    transition={{ delay: i * 0.1 }}
                    className="flex items-center gap-2 text-sm text-[#a1a1aa]"
                  >
                    <item.icon className="w-4 h-4 text-indigo-400 shrink-0" />
                    {item.label}
                  </motion.div>
                ))}
              </div>
            </div>
          </GlassCard>
        </Section>

        {/* ================================================================
            QUICK START
        ================================================================ */}
        <Section id="quickstart" className="mb-20">
          <SectionHeading
            icon={Rocket}
            title="Quick Start"
            subtitle="Three steps to your first policy"
            badge="Beginner"
          />

          <div className="grid md:grid-cols-3 gap-6">
            {[
              {
                step: 1,
                title: "Define Your Domain",
                desc: "Declare the variables your policy will evaluate. Specify ranges, enums, and booleans.",
                icon: Braces,
                color: "from-indigo-500 to-purple-500",
                code: `DOMAIN PaymentGuard {
  VARIABLES {
    amount: 0..1000000
    currency: {"USD", "EUR"}
    is_verified: BOOLEAN
  }
}`,
              },
              {
                step: 2,
                title: "Write Constraints",
                desc: "Define rules using WHEN/THEN patterns. CSL supports temporal and modal operators.",
                icon: FileCode,
                color: "from-purple-500 to-cyan-500",
                code: `STATE_CONSTRAINT limit_unverified {
  WHEN NOT is_verified
  THEN amount MUST BE <= 500
}`,
              },
              {
                step: 3,
                title: "Verify & Deploy",
                desc: "Run Z3 verification to catch logical inconsistencies, then deploy to the runtime.",
                icon: CheckCircle2,
                color: "from-cyan-500 to-green-500",
                code: `CONFIG {
  ENFORCEMENT_MODE: BLOCK
  CHECK_LOGICAL_CONSISTENCY: TRUE
}`,
              },
            ].map((item, i) => (
              <GlassCard key={item.step} delay={i * 0.15}>
                <div className="flex items-center gap-3 mb-4">
                  <div
                    className={`w-8 h-8 rounded-lg bg-gradient-to-br ${item.color} flex items-center justify-center text-white font-bold text-sm`}
                  >
                    {item.step}
                  </div>
                  <h3 className="text-white font-semibold">{item.title}</h3>
                </div>
                <p className="text-[#a1a1aa] text-sm mb-4">{item.desc}</p>
                <CodeBlock code={item.code} />
              </GlassCard>
            ))}
          </div>
        </Section>

        {/* ================================================================
            FILE STRUCTURE
        ================================================================ */}
        <Section id="structure" className="mb-20">
          <SectionHeading
            icon={Layers}
            title="File Structure"
            subtitle="Every .csl file has two blocks: CONFIG and DOMAIN"
          />

          <div className="grid md:grid-cols-2 gap-6">
            <GlassCard delay={0}>
              <div className="flex items-center gap-2 mb-3">
                <CircleDot className="w-4 h-4 text-cyan-400" />
                <h3 className="text-white font-semibold">CONFIG Block</h3>
                <Badge variant="outline" className="border-cyan-500/30 text-cyan-400 text-xs">
                  Optional
                </Badge>
              </div>
              <p className="text-[#a1a1aa] text-sm mb-4">
                Sets runtime behavior. Controls enforcement mode and whether logical consistency
                checks run during compilation.
              </p>
              <CodeBlock
                code={`CONFIG {
  // How the runtime handles violations
  ENFORCEMENT_MODE: BLOCK   // BLOCK | WARN | LOG

  // Enable Z3 formal verification
  CHECK_LOGICAL_CONSISTENCY: TRUE
}`}
                title="config.csl"
              />
            </GlassCard>

            <GlassCard delay={0.1}>
              <div className="flex items-center gap-2 mb-3">
                <Braces className="w-4 h-4 text-purple-400" />
                <h3 className="text-white font-semibold">DOMAIN Block</h3>
                <Badge variant="outline" className="border-purple-500/30 text-purple-400 text-xs">
                  Required
                </Badge>
              </div>
              <p className="text-[#a1a1aa] text-sm mb-4">
                Contains your VARIABLES declaration and one or more STATE_CONSTRAINT rules. The
                domain name scopes your policy.
              </p>
              <CodeBlock
                code={`DOMAIN MyDomain {
  VARIABLES {
    // declare variables here
  }

  STATE_CONSTRAINT rule_name {
    WHEN <condition>
    THEN <obligation>
  }
}`}
                title="domain.csl"
              />
            </GlassCard>
          </div>

          {/* Full example */}
          <GlassCard className="mt-6" delay={0.2}>
            <div className="flex items-center gap-2 mb-3">
              <FileCode className="w-4 h-4 text-green-400" />
              <h3 className="text-white font-semibold">Complete File Example</h3>
            </div>
            <CodeBlock
              code={`CONFIG {
  ENFORCEMENT_MODE: BLOCK
  CHECK_LOGICAL_CONSISTENCY: TRUE
}

DOMAIN TransferGuard {
  VARIABLES {
    amount: 0..1000000
    sender_tier: {"FREE", "PRO", "ENTERPRISE"}
    is_sanctioned: BOOLEAN
    risk_score: 0.0..1.0
  }

  STATE_CONSTRAINT block_sanctioned {
    ALWAYS NOT is_sanctioned
    THEN amount MUST BE >= 0
  }

  STATE_CONSTRAINT tier_limits {
    WHEN sender_tier == "FREE"
    THEN amount MUST BE <= 1000
  }

  STATE_CONSTRAINT high_risk_cap {
    WHEN risk_score >= 0.8
    THEN amount MUST BE <= 200
  }
}`}
              title="transfer_guard.csl"
            />
          </GlassCard>
        </Section>

        {/* ================================================================
            VARIABLES DEEP DIVE
        ================================================================ */}
        <Section id="variables" className="mb-20">
          <SectionHeading
            icon={Binary}
            title="Variables Deep Dive"
            subtitle="Four types to model any input context"
          />

          <div className="grid sm:grid-cols-2 gap-6">
            {[
              {
                icon: Hash,
                title: "Integer Range",
                desc: "Whole numbers within a bound. Use for amounts, counts, ages, limits.",
                code: `amount: 0..100000\nage: 0..150\nretry_count: 0..10`,
                color: "text-amber-400",
                border: "border-amber-500/20",
                bg: "bg-amber-500/5",
              },
              {
                icon: CircleDot,
                title: "Float Range",
                desc: "Decimal numbers for scores, probabilities, and percentages.",
                code: `risk_score: 0.0..1.0\nconfidence: 0.0..100.0\ntemperature: 0.0..2.0`,
                color: "text-cyan-400",
                border: "border-cyan-500/20",
                bg: "bg-cyan-500/5",
              },
              {
                icon: List,
                title: "Set / Enum",
                desc: "A fixed set of allowed string values. Perfect for roles, tiers, categories.",
                code: `currency: {"USD", "EUR", "GBP"}\nrole: {"ADMIN", "USER", "VIEWER"}\naction: {"READ", "WRITE", "DELETE"}`,
                color: "text-green-400",
                border: "border-green-500/20",
                bg: "bg-green-500/5",
              },
              {
                icon: ToggleLeft,
                title: "Boolean",
                desc: "True or false flags for binary conditions and feature gates.",
                code: `is_verified: BOOLEAN\nis_sanctioned: BOOLEAN\nhas_2fa: BOOLEAN`,
                color: "text-purple-400",
                border: "border-purple-500/20",
                bg: "bg-purple-500/5",
              },
            ].map((item, i) => (
              <GlassCard key={item.title} delay={i * 0.1}>
                <div className="flex items-center gap-3 mb-3">
                  <div className={`p-2 rounded-lg ${item.bg} border ${item.border}`}>
                    <item.icon className={`w-4 h-4 ${item.color}`} />
                  </div>
                  <h3 className="text-white font-semibold">{item.title}</h3>
                </div>
                <p className="text-[#a1a1aa] text-sm mb-4">{item.desc}</p>
                <CodeBlock code={item.code} />
              </GlassCard>
            ))}
          </div>

          <GlassCard className="mt-6" delay={0.4}>
            <div className="flex items-center gap-2 mb-3">
              <Lightbulb className="w-4 h-4 text-amber-400" />
              <h3 className="text-white font-semibold">Primitive Types</h3>
            </div>
            <p className="text-[#a1a1aa] text-sm mb-4">
              CSL also supports bare primitive types when you don&apos;t need range bounds:
            </p>
            <CodeBlock
              code={`count: Int       // any integer
age: Nat         // natural number (>= 0)`}
            />
          </GlassCard>
        </Section>

        {/* ================================================================
            CONSTRAINTS
        ================================================================ */}
        <Section id="constraints" className="mb-20">
          <SectionHeading
            icon={Lock}
            title="Constraints"
            subtitle="The core of CSL: WHEN/THEN rules that guard AI actions"
            badge="Core"
          />

          <GlassCard className="mb-6">
            <h3 className="text-white font-semibold mb-2">The WHEN / THEN Pattern</h3>
            <p className="text-[#a1a1aa] text-sm mb-4">
              Every constraint follows the same shape: a <strong className="text-purple-400">trigger condition</strong> and
              an <strong className="text-purple-400">obligation</strong>. If the condition matches the runtime context,
              the obligation is enforced.
            </p>
            <CodeBlock
              code={`STATE_CONSTRAINT rule_name {
  WHEN <condition>       // trigger
  THEN <obligation>      // enforcement
}`}
              title="pattern.csl"
            />
          </GlassCard>

          <Tabs defaultValue="basic" className="mb-6">
            <TabsList className="bg-white/5 border border-white/10">
              <TabsTrigger value="basic">Basic</TabsTrigger>
              <TabsTrigger value="must">MUST BE / MUST NOT BE</TabsTrigger>
              <TabsTrigger value="always">ALWAYS</TabsTrigger>
              <TabsTrigger value="complex">Complex Conditions</TabsTrigger>
            </TabsList>

            <TabsContent value="basic">
              <GlassCard>
                <h3 className="text-white font-semibold mb-2">Basic Constraint</h3>
                <p className="text-[#a1a1aa] text-sm mb-4">
                  A simple rule that checks a single condition and enforces a single obligation.
                </p>
                <CodeBlock
                  code={`STATE_CONSTRAINT limit_free_users {
  WHEN tier == "FREE"
  THEN amount MUST BE <= 1000
}

STATE_CONSTRAINT require_verification {
  WHEN amount > 5000
  THEN is_verified MUST BE TRUE
}`}
                  title="basic_constraint.csl"
                />
              </GlassCard>
            </TabsContent>

            <TabsContent value="must">
              <GlassCard>
                <h3 className="text-white font-semibold mb-2">MUST BE vs MUST NOT BE</h3>
                <p className="text-[#a1a1aa] text-sm mb-4">
                  Use <code className="text-purple-400">MUST BE</code> to require a value and{" "}
                  <code className="text-purple-400">MUST NOT BE</code> to prohibit one.
                </p>
                <CodeBlock
                  code={`// Require admin role for dangerous actions
STATE_CONSTRAINT admin_only_delete {
  WHEN action == "DELETE"
  THEN role MUST BE "ADMIN"
}

// Block sanctioned transfers entirely
STATE_CONSTRAINT block_sanctioned {
  WHEN is_sanctioned
  THEN action MUST NOT BE "TRANSFER"
}

// Cap amount for risky actions
STATE_CONSTRAINT risky_cap {
  WHEN risk_score >= 0.7
  THEN amount MUST BE <= 100
}`}
                  title="must_examples.csl"
                />
              </GlassCard>
            </TabsContent>

            <TabsContent value="always">
              <GlassCard>
                <h3 className="text-white font-semibold mb-2">ALWAYS Keyword</h3>
                <p className="text-[#a1a1aa] text-sm mb-4">
                  <code className="text-purple-400">ALWAYS</code> replaces WHEN to create
                  unconditional constraints that apply to every evaluation.
                </p>
                <CodeBlock
                  code={`// No one can ever transfer more than 500k
STATE_CONSTRAINT absolute_cap {
  ALWAYS TRUE
  THEN amount MUST BE <= 500000
}

// Tool "DESTROY" is never allowed
STATE_CONSTRAINT no_destroy {
  ALWAYS TRUE
  THEN tool MUST NOT BE "DESTROY"
}

// All transactions must have a positive amount
STATE_CONSTRAINT positive_amount {
  ALWAYS TRUE
  THEN amount MUST BE >= 1
}`}
                  title="always_examples.csl"
                />
              </GlassCard>
            </TabsContent>

            <TabsContent value="complex">
              <GlassCard>
                <h3 className="text-white font-semibold mb-2">Complex Conditions</h3>
                <p className="text-[#a1a1aa] text-sm mb-4">
                  Combine conditions with{" "}
                  <code className="text-purple-400">AND</code>,{" "}
                  <code className="text-purple-400">OR</code>, and{" "}
                  <code className="text-purple-400">NOT</code> for expressive rules.
                </p>
                <CodeBlock
                  code={`// Multiple conditions with AND
STATE_CONSTRAINT high_risk_unverified {
  WHEN risk_score > 0.8 AND NOT is_verified
  THEN amount MUST BE <= 50
}

// OR for multiple triggers
STATE_CONSTRAINT restricted_currencies {
  WHEN currency == "RUB" OR currency == "KPW"
  THEN action MUST NOT BE "TRANSFER"
}

// Nested logic
STATE_CONSTRAINT complex_rule {
  WHEN (role == "USER" OR role == "VIEWER")
    AND amount > 10000
    AND NOT is_verified
  THEN action MUST NOT BE "TRANSFER"
}`}
                  title="complex_conditions.csl"
                />
              </GlassCard>
            </TabsContent>
          </Tabs>

          <GlassCard>
            <div className="flex items-center gap-2 mb-3">
              <Lightbulb className="w-4 h-4 text-amber-400" />
              <h3 className="text-white font-semibold">Temporal Operators</h3>
              <Badge variant="outline" className="border-amber-500/30 text-amber-400 text-xs">
                Advanced
              </Badge>
            </div>
            <p className="text-[#a1a1aa] text-sm mb-4">
              CSL supports temporal operators for stateful policies that reason about ordering:
            </p>
            <CodeBlock
              code={`// BEFORE: condition must hold before another event
STATE_CONSTRAINT verify_before_send {
  BEFORE action == "SEND"
  THEN is_verified MUST BE TRUE
}

// AFTER: enforce a constraint after something happens
STATE_CONSTRAINT cooldown_after_failure {
  AFTER status == "FAILED"
  THEN retry_count MUST BE <= 3
}

// EVENTUALLY: something must become true
STATE_CONSTRAINT eventual_verification {
  EVENTUALLY is_verified MUST BE TRUE
}`}
              title="temporal.csl"
            />
          </GlassCard>
        </Section>

        {/* ================================================================
            REAL-WORLD EXAMPLES
        ================================================================ */}
        <Section id="examples" className="mb-20">
          <SectionHeading
            icon={Code2}
            title="Real-World Examples"
            subtitle="Complete policies you can adapt for your use case"
          />

          <div className="space-y-6">
            {/* Example 1: Payment Guard */}
            <GlassCard delay={0}>
              <div className="flex items-center gap-3 mb-2">
                <div className="p-2 rounded-lg bg-green-500/10 border border-green-500/20">
                  <Lock className="w-4 h-4 text-green-400" />
                </div>
                <div>
                  <h3 className="text-white font-semibold">Payment Guard</h3>
                  <p className="text-[#71717a] text-sm">Transfer limits by user tier and verification</p>
                </div>
              </div>
              <CodeBlock
                code={`CONFIG {
  ENFORCEMENT_MODE: BLOCK
  CHECK_LOGICAL_CONSISTENCY: TRUE
}

DOMAIN PaymentGuard {
  VARIABLES {
    amount: 0..1000000
    sender_tier: {"FREE", "PRO", "ENTERPRISE"}
    is_verified: BOOLEAN
    is_sanctioned: BOOLEAN
    risk_score: 0.0..1.0
    currency: {"USD", "EUR", "GBP", "JPY"}
  }

  // No transfers from sanctioned entities
  STATE_CONSTRAINT block_sanctioned {
    WHEN is_sanctioned
    THEN amount MUST BE <= 0
  }

  // Free users: max $1,000
  STATE_CONSTRAINT free_tier_limit {
    WHEN sender_tier == "FREE"
    THEN amount MUST BE <= 1000
  }

  // Pro users: max $50,000
  STATE_CONSTRAINT pro_tier_limit {
    WHEN sender_tier == "PRO"
    THEN amount MUST BE <= 50000
  }

  // Unverified users: max $500
  STATE_CONSTRAINT unverified_limit {
    WHEN NOT is_verified
    THEN amount MUST BE <= 500
  }

  // High risk: cap at $200
  STATE_CONSTRAINT high_risk_cap {
    WHEN risk_score >= 0.8
    THEN amount MUST BE <= 200
  }

  // Global absolute cap
  STATE_CONSTRAINT absolute_cap {
    ALWAYS TRUE
    THEN amount MUST BE <= 500000
  }
}`}
                title="payment_guard.csl"
              />
            </GlassCard>

            {/* Example 2: Agent Tool Guard */}
            <GlassCard delay={0.1}>
              <div className="flex items-center gap-3 mb-2">
                <div className="p-2 rounded-lg bg-purple-500/10 border border-purple-500/20">
                  <Bot className="w-4 h-4 text-purple-400" />
                </div>
                <div>
                  <h3 className="text-white font-semibold">Agent Tool Guard</h3>
                  <p className="text-[#71717a] text-sm">Restrict dangerous tool calls for AI agents</p>
                </div>
              </div>
              <CodeBlock
                code={`CONFIG {
  ENFORCEMENT_MODE: BLOCK
  CHECK_LOGICAL_CONSISTENCY: TRUE
}

DOMAIN AgentToolGuard {
  VARIABLES {
    tool: {"READ", "WRITE", "DELETE", "EXECUTE", "ADMIN"}
    role: {"AGENT", "SUPERVISOR", "ADMIN"}
    confidence: 0.0..1.0
    is_sandbox: BOOLEAN
    target_scope: {"OWN", "TEAM", "GLOBAL"}
  }

  // Agents can never use ADMIN tools
  STATE_CONSTRAINT no_agent_admin {
    WHEN role == "AGENT"
    THEN tool MUST NOT BE "ADMIN"
  }

  // DELETE requires SUPERVISOR or higher
  STATE_CONSTRAINT delete_needs_supervisor {
    WHEN tool == "DELETE"
    THEN role MUST NOT BE "AGENT"
  }

  // Low confidence blocks WRITE and EXECUTE
  STATE_CONSTRAINT low_confidence_readonly {
    WHEN confidence < 0.5
    THEN tool MUST BE "READ"
  }

  // Global scope needs ADMIN role
  STATE_CONSTRAINT global_scope_admin {
    WHEN target_scope == "GLOBAL"
    THEN role MUST BE "ADMIN"
  }

  // Sandbox mode: only READ allowed
  STATE_CONSTRAINT sandbox_readonly {
    WHEN is_sandbox
    THEN tool MUST BE "READ"
  }
}`}
                title="agent_tool_guard.csl"
              />
            </GlassCard>

            {/* Example 3: Age Verification */}
            <GlassCard delay={0.2}>
              <div className="flex items-center gap-3 mb-2">
                <div className="p-2 rounded-lg bg-amber-500/10 border border-amber-500/20">
                  <UserCheck className="w-4 h-4 text-amber-400" />
                </div>
                <div>
                  <h3 className="text-white font-semibold">Age Verification</h3>
                  <p className="text-[#71717a] text-sm">Content access control by age group</p>
                </div>
              </div>
              <CodeBlock
                code={`DOMAIN AgeVerification {
  VARIABLES {
    user_age: 0..150
    content_rating: {"G", "PG", "PG13", "R", "NC17"}
    is_age_verified: BOOLEAN
    region: {"US", "EU", "UK", "JP"}
  }

  // Under 13: only G-rated content
  STATE_CONSTRAINT children_safe {
    WHEN user_age < 13
    THEN content_rating MUST BE "G"
  }

  // Under 17: no R or NC17
  STATE_CONSTRAINT teen_restriction {
    WHEN user_age < 17
    THEN content_rating MUST NOT BE "NC17"
  }

  // NC17 requires age verification
  STATE_CONSTRAINT nc17_verified {
    WHEN content_rating == "NC17"
    THEN is_age_verified MUST BE TRUE
  }

  // R-rated needs at least 17
  STATE_CONSTRAINT r_rated_age {
    WHEN content_rating == "R" AND user_age < 17
    THEN is_age_verified MUST BE TRUE
  }
}`}
                title="age_verification.csl"
              />
            </GlassCard>

            {/* Example 4: DAO Treasury */}
            <GlassCard delay={0.3}>
              <div className="flex items-center gap-3 mb-2">
                <div className="p-2 rounded-lg bg-cyan-500/10 border border-cyan-500/20">
                  <Vote className="w-4 h-4 text-cyan-400" />
                </div>
                <div>
                  <h3 className="text-white font-semibold">DAO Treasury</h3>
                  <p className="text-[#71717a] text-sm">Governance rules for on-chain treasuries</p>
                </div>
              </div>
              <CodeBlock
                code={`CONFIG {
  ENFORCEMENT_MODE: BLOCK
  CHECK_LOGICAL_CONSISTENCY: TRUE
}

DOMAIN DAOTreasury {
  VARIABLES {
    amount: 0..10000000
    vote_count: 0..1000
    quorum_met: BOOLEAN
    proposer_role: {"MEMBER", "COUNCIL", "MULTISIG"}
    action: {"SPEND", "INVEST", "BURN", "MINT"}
    treasury_balance: 0..100000000
  }

  // Spending requires quorum
  STATE_CONSTRAINT spend_needs_quorum {
    WHEN action == "SPEND"
    THEN quorum_met MUST BE TRUE
  }

  // Members can only propose up to $10k
  STATE_CONSTRAINT member_limit {
    WHEN proposer_role == "MEMBER"
    THEN amount MUST BE <= 10000
  }

  // BURN and MINT need council or multisig
  STATE_CONSTRAINT protected_actions {
    WHEN action == "BURN" OR action == "MINT"
    THEN proposer_role MUST NOT BE "MEMBER"
  }

  // Can never spend more than 10% of treasury
  STATE_CONSTRAINT treasury_protection {
    ALWAYS TRUE
    THEN amount MUST BE <= 10000000
  }

  // At least 5 votes needed
  STATE_CONSTRAINT min_votes {
    WHEN amount > 1000
    THEN vote_count MUST BE >= 5
  }
}`}
                title="dao_treasury.csl"
              />
            </GlassCard>
          </div>
        </Section>

        {/* ================================================================
            OPERATORS REFERENCE
        ================================================================ */}
        <Section id="operators" className="mb-20">
          <SectionHeading
            icon={Terminal}
            title="Operators Reference"
            subtitle="Every operator available in CSL"
          />

          <GlassCard>
            <OpRow
              category="Logic"
              color="text-purple-400"
              operators={[
                { op: "AND", desc: "both true" },
                { op: "OR", desc: "either true" },
                { op: "NOT", desc: "negation" },
              ]}
            />
            <OpRow
              category="Comparison"
              color="text-cyan-400"
              operators={[
                { op: "==", desc: "equal" },
                { op: "!=", desc: "not equal" },
                { op: "<", desc: "less than" },
                { op: ">", desc: "greater than" },
                { op: "<=", desc: "less or equal" },
                { op: ">=", desc: "greater or equal" },
              ]}
            />
            <OpRow
              category="Arithmetic"
              color="text-amber-400"
              operators={[
                { op: "+", desc: "add" },
                { op: "-", desc: "subtract" },
                { op: "*", desc: "multiply" },
                { op: "/", desc: "divide" },
                { op: "%", desc: "modulo" },
              ]}
            />
            <OpRow
              category="Temporal"
              color="text-green-400"
              operators={[
                { op: "WHEN", desc: "conditional" },
                { op: "ALWAYS", desc: "unconditional" },
                { op: "BEFORE", desc: "precondition" },
                { op: "AFTER", desc: "postcondition" },
                { op: "EVENTUALLY", desc: "future state" },
              ]}
            />
            <OpRow
              category="Modal"
              color="text-red-400"
              operators={[
                { op: "MUST BE", desc: "required value" },
                { op: "MUST NOT BE", desc: "prohibited value" },
                { op: "MAY BE", desc: "permitted value" },
              ]}
            />
            <OpRow
              category="Built-in"
              color="text-indigo-400"
              operators={[
                { op: "len(x)", desc: "length" },
                { op: "max(a,b)", desc: "maximum" },
                { op: "min(a,b)", desc: "minimum" },
                { op: "abs(x)", desc: "absolute value" },
              ]}
            />
          </GlassCard>

          <GlassCard className="mt-6" delay={0.1}>
            <div className="flex items-center gap-2 mb-3">
              <Lightbulb className="w-4 h-4 text-amber-400" />
              <h3 className="text-white font-semibold">Member Access & Comments</h3>
            </div>
            <CodeBlock
              code={`// Dot notation for nested fields
WHEN user.profile.age < 18
THEN content.rating MUST NOT BE "R"

// Single-line comments use //
// Multi-line comments use /* ... */
/* This is a
   multi-line comment */`}
              title="syntax.csl"
            />
          </GlassCard>
        </Section>

        {/* ================================================================
            TIPS & BEST PRACTICES
        ================================================================ */}
        <Section id="tips" className="mb-20">
          <SectionHeading
            icon={Lightbulb}
            title="Tips & Best Practices"
            subtitle="Write better policies with these guidelines"
          />

          <div className="space-y-4">
            {[
              {
                icon: CheckCircle2,
                title: "Always declare all variables",
                desc: "Every variable used in constraints must be declared in the VARIABLES block. The compiler will reject undeclared references.",
                color: "text-green-400",
              },
              {
                icon: Shield,
                title: "Use ENFORCEMENT_MODE: BLOCK for production",
                desc: "WARN and LOG modes are useful during development but should never be used in production. BLOCK ensures violations are actually prevented.",
                color: "text-indigo-400",
              },
              {
                icon: Zap,
                title: "Run cslcore verify before deploying",
                desc: "The Z3 verifier catches logical contradictions (e.g., two rules that can never both be satisfied). Always verify before deployment.",
                color: "text-amber-400",
              },
              {
                icon: Layers,
                title: "One domain per concern",
                desc: "Split policies into focused domains: PaymentGuard, ToolGuard, ContentGuard. This makes policies easier to test and maintain.",
                color: "text-cyan-400",
              },
              {
                icon: AlertTriangle,
                title: "Watch for contradictions",
                desc: "If one rule says amount MUST BE <= 100 and another says amount MUST BE >= 200, the Z3 verifier will flag this as unsatisfiable.",
                color: "text-red-400",
              },
              {
                icon: Code2,
                title: "Name constraints descriptively",
                desc: "Use names like block_sanctioned_transfers or limit_free_tier instead of rule1 or constraint_a. Names appear in audit logs.",
                color: "text-purple-400",
              },
              {
                icon: Lock,
                title: "Use ALWAYS TRUE for hard invariants",
                desc: "For rules that must never be violated regardless of context (e.g., absolute caps, forbidden actions), use ALWAYS TRUE as the trigger.",
                color: "text-green-400",
              },
              {
                icon: FileCode,
                title: "Comment your constraints",
                desc: "Use // comments to explain the business reason behind each constraint. Future you (and your team) will thank you.",
                color: "text-[#71717a]",
              },
            ].map((tip, i) => (
              <motion.div
                key={tip.title}
                initial={{ opacity: 0, x: -20 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.06, duration: 0.4 }}
                className="flex items-start gap-4 p-4 rounded-xl border border-white/5 bg-white/[0.02] hover:bg-white/[0.04] transition-colors"
              >
                <tip.icon className={`w-5 h-5 ${tip.color} shrink-0 mt-0.5`} />
                <div>
                  <h4 className="text-white font-medium text-sm">{tip.title}</h4>
                  <p className="text-[#a1a1aa] text-sm mt-0.5">{tip.desc}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </Section>

        {/* ================================================================
            NEXT STEPS
        ================================================================ */}
        <Section id="next-steps" className="mb-8">
          <div className="relative rounded-2xl border border-indigo-500/20 bg-gradient-to-br from-indigo-500/5 via-purple-500/5 to-cyan-500/5 backdrop-blur-xl p-8 text-center overflow-hidden">
            <SparkleEffect />
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5 }}
            >
              <Rocket className="w-10 h-10 text-indigo-400 mx-auto mb-4" />
              <h2 className="text-2xl md:text-3xl font-bold text-white mb-2">
                Ready to write your first policy?
              </h2>
              <p className="text-[#a1a1aa] mb-6 max-w-md mx-auto">
                Head to the Policies page to create, verify, and deploy CSL policies
                with the built-in editor and Z3 verification.
              </p>
              <Link href="/dashboard">
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-500 text-white font-semibold hover:from-indigo-400 hover:to-purple-400 transition-all shadow-lg shadow-indigo-500/20"
                >
                  Go to Dashboard
                  <ChevronRight className="w-4 h-4" />
                </motion.button>
              </Link>
            </motion.div>
          </div>
        </Section>
      </div>
    </div>
  );
}
