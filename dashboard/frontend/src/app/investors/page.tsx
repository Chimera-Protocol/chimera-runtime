"use client";

import Link from "next/link";
import { PublicNav } from "@/components/layout/PublicNav";
import {
  Shield,
  ArrowLeft,
  TrendingUp,
  Globe,
  Target,
  Lightbulb,
  Users,
  Mail,
  ExternalLink,
  Sparkles,
  Scale,
  Brain,
  Layers,
  CheckCircle2,
} from "lucide-react";

const milestones = [
  { label: "Open-source library live", done: true },
  { label: "5 framework integrations", done: true },
  { label: "CSL policy language + Z3 engine", done: true },
  { label: "Cloud dashboard (beta)", done: true },
  { label: "First 100 beta users", done: false },
  { label: "Enterprise pilot customers", done: false },
];

const marketStats = [
  { value: "$2.1T", label: "AI market by 2030", sub: "McKinsey" },
  { value: "Aug 2025", label: "EU AI Act enforcement", sub: "Article 6" },
  { value: "€35M", label: "Max non-enforcement fine", sub: "Per violation" },
  { value: "0", label: "Competitors with formal verification", sub: "We're first" },
];

export default function InvestorsPage() {
  return (
    <div className="min-h-screen bg-[#0a0a0f] relative overflow-hidden">
      {/* Background effects */}
      <div className="absolute top-0 left-1/3 w-[600px] h-[600px] bg-[#6366f1]/5 rounded-full blur-[200px]" />
      <div className="absolute bottom-1/4 right-1/4 w-[500px] h-[500px] bg-[#22c55e]/3 rounded-full blur-[180px]" />

      <PublicNav backLabel="Back to product" />

      <div className="relative z-10 mx-auto max-w-4xl px-6 pt-32 pb-24">
        {/* Header */}
        <div className="text-center mb-20">
          <div className="inline-flex items-center gap-2 rounded-full border border-[#6366f1]/30 bg-[#6366f1]/10 px-4 py-1.5 mb-6">
            <TrendingUp className="h-3.5 w-3.5 text-[#818cf8]" />
            <span className="text-xs font-medium text-[#818cf8]">Actively Raising</span>
          </div>
          <h1 className="text-4xl sm:text-5xl font-bold text-white leading-tight">
            The Deterministic Runtime for
            <br />
            <span className="bg-gradient-to-r from-[#6366f1] to-[#22c55e] bg-clip-text text-transparent">
              the AI Economy
            </span>
          </h1>
          <p className="mt-6 text-lg text-[#a1a1aa] max-w-2xl mx-auto leading-relaxed">
            Every AI agent will need a deterministic runtime. We&apos;re building the infrastructure
            that makes AI decisions provably safe, auditable, and regulation-ready.
          </p>
        </div>

        {/* The Opportunity */}
        <section className="mb-20">
          <div className="flex items-center gap-3 mb-8">
            <div className="h-10 w-10 rounded-xl bg-[#f59e0b]/10 flex items-center justify-center">
              <Globe className="h-5 w-5 text-[#f59e0b]" />
            </div>
            <h2 className="text-2xl font-bold text-white">The Opportunity</h2>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
            {marketStats.map((stat) => (
              <div
                key={stat.label}
                className="rounded-xl border border-[#1e1e2e] bg-[#111119] p-5 text-center"
              >
                <div className="text-2xl font-bold text-white">{stat.value}</div>
                <div className="text-xs text-[#a1a1aa] mt-1">{stat.label}</div>
                <div className="text-[10px] text-[#6366f1] mt-1 font-medium">{stat.sub}</div>
              </div>
            ))}
          </div>

          <div className="rounded-xl border border-[#1e1e2e] bg-[#111119] p-6">
            <p className="text-sm text-[#a1a1aa] leading-relaxed">
              The EU AI Act becomes enforceable in August 2025, making compliance
              mandatory for high-risk AI systems. Companies face fines up to
              <span className="text-white font-medium"> 7% of global revenue</span> for
              non-compliance. Yet no existing tool offers{" "}
              <span className="text-white font-medium">formal mathematical verification</span>{" "}
              of AI decisions — they rely on heuristic guardrails that can be bypassed.
              Chimera Runtime is the first system to make every AI decision{" "}
              <span className="text-[#6366f1] font-medium">provably enforced</span>.
            </p>
          </div>
        </section>

        {/* Why Us — Unfair Advantages */}
        <section className="mb-20">
          <div className="flex items-center gap-3 mb-8">
            <div className="h-10 w-10 rounded-xl bg-[#6366f1]/10 flex items-center justify-center">
              <Lightbulb className="h-5 w-5 text-[#6366f1]" />
            </div>
            <h2 className="text-2xl font-bold text-white">Why Chimera</h2>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            {[
              {
                icon: Brain,
                title: "Neuro-Symbolic Architecture",
                desc: "Not just guardrails — a formal verification engine (Z3 SAT solver) that mathematically proves every AI decision is policy-enforced. Published research backing.",
                color: "#6366f1",
              },
              {
                icon: Scale,
                title: "Regulation-Native Design",
                desc: "Built from the ground up for EU AI Act. Maps directly to Articles 9, 12, 13, 14, 19, and 86. One-click Annex IV technical documentation generation.",
                color: "#f59e0b",
              },
              {
                icon: Layers,
                title: "Framework-Agnostic Runtime",
                desc: "Drop-in integration with LangChain, LangGraph, CrewAI, LlamaIndex, AutoGen. One line of code wraps any AI agent with deterministic enforcement.",
                color: "#22c55e",
              },
              {
                icon: Target,
                title: "Open Core → SaaS Flywheel",
                desc: "Free open-source library drives adoption. Cloud dashboard (analytics, audit, Annex IV) monetizes power users. Enterprise tier for regulated industries.",
                color: "#ef4444",
              },
            ].map((item) => (
              <div
                key={item.title}
                className="rounded-xl border border-[#1e1e2e] bg-[#111119] p-6 hover:border-[#2e2e3e] transition"
              >
                <div
                  className="h-9 w-9 rounded-lg flex items-center justify-center mb-4"
                  style={{ backgroundColor: `${item.color}15` }}
                >
                  <item.icon className="h-5 w-5" style={{ color: item.color }} />
                </div>
                <h3 className="text-sm font-semibold text-white mb-2">{item.title}</h3>
                <p className="text-xs text-[#71717a] leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Traction & Roadmap */}
        <section className="mb-20">
          <div className="flex items-center gap-3 mb-8">
            <div className="h-10 w-10 rounded-xl bg-[#22c55e]/10 flex items-center justify-center">
              <TrendingUp className="h-5 w-5 text-[#22c55e]" />
            </div>
            <h2 className="text-2xl font-bold text-white">Traction & Roadmap</h2>
          </div>

          <div className="rounded-xl border border-[#1e1e2e] bg-[#111119] p-6">
            <div className="space-y-4">
              {milestones.map((m, i) => (
                <div key={i} className="flex items-center gap-4">
                  <div className="relative flex flex-col items-center">
                    <div
                      className={`h-8 w-8 rounded-full flex items-center justify-center border ${
                        m.done
                          ? "border-[#22c55e]/30 bg-[#22c55e]/10"
                          : "border-[#1e1e2e] bg-[#0a0a0f]"
                      }`}
                    >
                      {m.done ? (
                        <CheckCircle2 className="h-4 w-4 text-[#22c55e]" />
                      ) : (
                        <Sparkles className="h-4 w-4 text-[#71717a]" />
                      )}
                    </div>
                    {i < milestones.length - 1 && (
                      <div
                        className={`w-px h-6 mt-1 ${
                          m.done ? "bg-[#22c55e]/20" : "bg-[#1e1e2e]"
                        }`}
                      />
                    )}
                  </div>
                  <span
                    className={`text-sm ${
                      m.done ? "text-white" : "text-[#71717a]"
                    }`}
                  >
                    {m.label}
                    {!m.done && (
                      <span className="ml-2 text-[10px] rounded-full border border-[#6366f1]/30 bg-[#6366f1]/10 text-[#818cf8] px-2 py-0.5">
                        Next
                      </span>
                    )}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Business Model */}
        <section className="mb-20">
          <div className="flex items-center gap-3 mb-8">
            <div className="h-10 w-10 rounded-xl bg-[#ef4444]/10 flex items-center justify-center">
              <Target className="h-5 w-5 text-[#ef4444]" />
            </div>
            <h2 className="text-2xl font-bold text-white">Business Model</h2>
          </div>

          <div className="grid gap-4 sm:grid-cols-3">
            {[
              {
                tier: "Free",
                target: "Developers & startups",
                revenue: "Open source",
                purpose: "Adoption engine — unlimited local use drives ecosystem growth",
                color: "#71717a",
              },
              {
                tier: "Pro — $29/mo",
                target: "AI teams & agencies",
                revenue: "SaaS MRR",
                purpose: "Analytics, reasoning traces, multi-agent control. First 100 users free (beta)",
                color: "#6366f1",
              },
              {
                tier: "Enterprise — $10k+/yr",
                target: "Banks, pharma, gov",
                revenue: "Annual contracts",
                purpose: "Annex IV generation, SSO/RBAC, SIEM integration. Single deal = $10k+ ARR",
                color: "#f59e0b",
              },
            ].map((item) => (
              <div
                key={item.tier}
                className="rounded-xl border border-[#1e1e2e] bg-[#111119] p-5"
              >
                <div
                  className="text-xs font-semibold rounded-full px-2.5 py-1 inline-block mb-3 border"
                  style={{
                    color: item.color,
                    borderColor: `${item.color}40`,
                    backgroundColor: `${item.color}10`,
                  }}
                >
                  {item.tier}
                </div>
                <p className="text-xs text-white font-medium mb-1">{item.target}</p>
                <p className="text-[11px] text-[#71717a] leading-relaxed">{item.purpose}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Team */}
        <section className="mb-20">
          <div className="flex items-center gap-3 mb-8">
            <div className="h-10 w-10 rounded-xl bg-[#818cf8]/10 flex items-center justify-center">
              <Users className="h-5 w-5 text-[#818cf8]" />
            </div>
            <h2 className="text-2xl font-bold text-white">Team</h2>
          </div>

          <div className="rounded-xl border border-[#1e1e2e] bg-[#111119] p-6">
            <div className="flex items-start gap-5">
              <div className="h-16 w-16 rounded-2xl bg-gradient-to-br from-[#6366f1] to-[#818cf8] flex items-center justify-center shrink-0">
                <span className="text-2xl font-bold text-white">AA</span>
              </div>
              <div>
                <h3 className="text-lg font-semibold text-white">Aytug Akarlar</h3>
                <p className="text-sm text-[#6366f1] font-medium mb-3">Founder & CEO</p>
                <p className="text-xs text-[#f59e0b] font-medium mb-2">Ex Ernst &amp; Young — Technology Risk Auditor</p>
                <p className="text-sm text-[#a1a1aa] leading-relaxed">
                  Former EY technology risk auditor turned AI safety researcher. Published work on
                  neuro-symbolic compliance systems. Designed the Chimera architecture — the first
                  formal verification layer for autonomous AI agents operating under EU AI Act requirements.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* CTA — Contact */}
        <section>
          <div className="rounded-2xl border border-[#6366f1]/20 bg-gradient-to-b from-[#6366f1]/5 to-transparent p-10 text-center">
            <div className="h-14 w-14 rounded-2xl bg-[#6366f1]/10 flex items-center justify-center mx-auto mb-5">
              <Mail className="h-7 w-7 text-[#6366f1]" />
            </div>
            <h2 className="text-2xl font-bold text-white mb-2">
              Let&apos;s Talk
            </h2>
            <p className="text-sm text-[#a1a1aa] mb-8 max-w-md mx-auto">
              We&apos;re raising our pre-seed round to accelerate product development,
              onboard enterprise pilots, and expand the team. Interested in the
              future of AI runtime infrastructure?
            </p>
            <a
              href="mailto:akarlaraytu@gmail.com?subject=Chimera%20Runtime%20—%20Investor%20Inquiry"
              className="inline-flex items-center gap-2 rounded-xl bg-[#6366f1] hover:bg-[#5558e6] text-white font-medium px-8 py-3.5 transition shadow-lg shadow-[#6366f1]/20"
            >
              <Mail className="h-4 w-4" />
              akarlaraytu@gmail.com
            </a>
            <p className="text-xs text-[#52525b] mt-4">
              Or schedule a call — we&apos;ll send our deck and product walkthrough.
            </p>
          </div>
        </section>

        {/* Footer */}
        <div className="mt-16 pt-8 border-t border-[#1e1e2e] flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Shield className="h-4 w-4 text-[#6366f1]" />
            <span className="text-xs text-[#71717a]">Chimera Runtime v3.0.0</span>
          </div>
          <div className="flex items-center gap-4">
            <Link href="/demo" className="text-xs text-[#71717a] hover:text-white transition flex items-center gap-1">
              Product Demo <ExternalLink className="h-3 w-3" />
            </Link>
            <Link href="/docs" className="text-xs text-[#71717a] hover:text-white transition flex items-center gap-1">
              Documentation <ExternalLink className="h-3 w-3" />
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
