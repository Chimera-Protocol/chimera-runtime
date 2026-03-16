"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import {
  Shield,
  Activity,
  FileText,
  Zap,
  Lock,
  BarChart3,
  Eye,
  Check,
  ArrowRight,
  Brain,
  GitBranch,
  X,
  Sparkles,
  Users,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { AuthNav } from "@/components/layout/AuthNav";
import { analytics } from "@/lib/analytics";

const features = [
  {
    icon: Shield,
    title: "Neuro-Symbolic Policy Guards",
    description:
      "CSL + Z3 formal verification ensures every AI decision is mathematically provable. No hallucinated compliance.",
  },
  {
    icon: Activity,
    title: "Real-Time Decision Monitoring",
    description:
      "Track ALLOWED, BLOCKED, and OVERRIDE decisions as they happen. Full reasoning traces for every action.",
  },
  {
    icon: FileText,
    title: "Annex IV Auto-Generation",
    description:
      "One-click EU AI Act technical documentation. 14/19 sections filled automatically from live system data.",
  },
  {
    icon: BarChart3,
    title: "Advanced Analytics",
    description:
      "Decision trends, block rate heatmaps, violation patterns, and latency distributions. Data-driven compliance.",
  },
  {
    icon: Eye,
    title: "Human Oversight (Art. 14)",
    description:
      "Confirm, override, or halt any AI agent. Full audit trail of human interventions. Single-click controls.",
  },
  {
    icon: Brain,
    title: "Causal Analysis",
    description:
      "Neuro-Symbolic-Causal pipeline traces root causes of policy violations. Beyond guardrails — true explainability.",
  },
];

const tiers = [
  {
    name: "Free",
    badge: "Open Source",
    price: "$0",
    period: "forever",
    description: "Runtime policy enforcement for any AI agent — no limits locally",
    features: [
      "Runtime guard on every AI decision",
      "Policy enforcement with formal verification",
      "Unlimited local audit logging",
      "Full CLI & Python SDK",
      "Cloud dashboard (7-day, 100 records)",
      "EU AI Act compliance status checks",
    ],
    cta: "Get Started Free",
    href: "/register",
    highlight: false,
  },
  {
    name: "Pro",
    badge: "Most Popular",
    price: "$29",
    originalPrice: "$79",
    period: "/month",
    launchDeal: true,
    betaFree: true,
    description: "Deep analytics, reasoning traces & multi-agent control",
    features: [
      "Everything in Free",
      "Decision analytics — 5 interactive charts",
      "Full reasoning trace for every blocked action",
      "Halt/Resume any agent in real time (Art. 14)",
      "Multi-policy hot-reload & comparison",
      "90-day cloud data retention",
      "Exportable compliance reports (Art. 86)",
      "Programmatic API key access",
      "Email & webhook alerts on violations",
    ],
    cta: "Join Beta — Free Access",
    href: "/contact?plan=pro",
    highlight: true,
  },
  {
    name: "Enterprise",
    badge: "$10k+/year",
    price: "Custom",
    period: "pricing",
    description: "End-to-end compliance infrastructure for regulated industries",
    features: [
      "Everything in Pro",
      "One-click Annex IV document generation",
      "Real-time decision stream (WebSocket)",
      "SSO/SAML & role-based access control",
      "SIEM integration (Splunk, Datadog, QRadar)",
      "Unlimited data retention & multi-env",
      "Causal root-cause analysis dashboard",
      "White-label & custom branding",
      "Dedicated support & SLA guarantee",
    ],
    cta: "Contact Sales",
    href: "/contact",
    highlight: false,
  },
];

const integrations = [
  "LangChain",
  "LangGraph",
  "LlamaIndex",
  "CrewAI",
  "AutoGen",
];

export default function LandingPage() {
  const [showBetaPopup, setShowBetaPopup] = useState(false);

  useEffect(() => {
    const dismissed = sessionStorage.getItem("beta-popup-dismissed");
    if (!dismissed) {
      const timer = setTimeout(() => setShowBetaPopup(true), 2500);
      return () => clearTimeout(timer);
    }
  }, []);

  const dismissPopup = () => {
    setShowBetaPopup(false);
    sessionStorage.setItem("beta-popup-dismissed", "1");
  };

  return (
    <div className="min-h-screen bg-[#0a0a0f]">
      {/* Beta Popup */}
      {showBetaPopup && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="relative mx-4 w-full max-w-md rounded-2xl border border-[#6366f1]/30 bg-[#111119] p-8 shadow-2xl shadow-[#6366f1]/10">
            <button
              onClick={dismissPopup}
              className="absolute right-4 top-4 text-[#71717a] hover:text-white transition"
            >
              <X className="h-5 w-5" />
            </button>
            <div className="flex items-center gap-3 mb-4">
              <div className="h-12 w-12 rounded-xl bg-[#6366f1]/10 flex items-center justify-center">
                <Sparkles className="h-6 w-6 text-[#6366f1]" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-white">Early Access Program</h3>
                <p className="text-xs text-[#22c55e] font-medium">First 100 beta testers get Pro free</p>
              </div>
            </div>
            <p className="text-sm text-[#a1a1aa] mb-2">
              We&apos;re opening <span className="text-white font-medium">Pro tier features for free</span> to
              our first 100 users. Get full analytics, reasoning traces, and multi-agent
              control at no cost.
            </p>
            <div className="flex items-center gap-2 mb-6 mt-4 rounded-lg border border-[#22c55e]/20 bg-[#22c55e]/5 px-3 py-2">
              <Users className="h-4 w-4 text-[#22c55e] shrink-0" />
              <span className="text-xs text-[#22c55e]">Limited spots — join as a beta tester and shape the product</span>
            </div>
            <div className="flex gap-3">
              <Link href="/contact?plan=pro" className="flex-1" onClick={() => { analytics.ctaClick("beta-claim-pro"); dismissPopup(); }}>
                <Button className="w-full bg-[#6366f1] hover:bg-[#5558e6] text-white font-medium">
                  Claim Free Pro Access
                </Button>
              </Link>
              <Button
                variant="outline"
                className="border-[#1e1e2e] text-[#71717a] hover:text-white"
                onClick={dismissPopup}
              >
                Later
              </Button>
            </div>
          </div>
        </div>
      )}
      {/* Navigation */}
      <nav className="fixed top-0 z-50 w-full border-b border-[#1e1e2e] bg-[#0a0a0f]/80 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
          <div className="flex items-center gap-2">
            <Shield className="h-6 w-6 text-[#6366f1]" />
            <span className="text-lg font-bold text-white">
              Chimera<span className="text-[#6366f1]">Compliance</span>
            </span>
          </div>
          <div className="hidden items-center gap-8 md:flex">
            <a href="#features" className="text-sm text-[#71717a] hover:text-white transition-colors">
              Features
            </a>
            <a href="#pricing" className="text-sm text-[#71717a] hover:text-white transition-colors">
              Pricing
            </a>
            <a href="#integrations" className="text-sm text-[#71717a] hover:text-white transition-colors">
              Integrations
            </a>
            <Link href="/investors" className="text-sm text-[#71717a] hover:text-white transition-colors">
              For Investors
            </Link>
            <Link href="/docs" className="text-sm text-[#71717a] hover:text-white transition-colors">
              Docs
            </Link>
          </div>
          <AuthNav />
        </div>
      </nav>

      {/* Hero */}
      <section className="relative flex min-h-screen items-center justify-center overflow-hidden pt-16">
        {/* Gradient orbs */}
        <div className="absolute left-1/4 top-1/4 h-96 w-96 rounded-full bg-[#6366f1]/10 blur-[128px]" />
        <div className="absolute right-1/4 bottom-1/4 h-96 w-96 rounded-full bg-[#22c55e]/5 blur-[128px]" />

        <div className="relative z-10 mx-auto max-w-5xl px-6 text-center">
          <Badge
            variant="outline"
            className="mb-6 border-[#6366f1]/30 bg-[#6366f1]/10 text-[#818cf8]"
          >
            <Zap className="mr-1 h-3 w-3" /> EU AI Act Ready
          </Badge>

          <h1 className="text-5xl font-bold tracking-tight text-white sm:text-7xl">
            AI Compliance
            <br />
            <span className="bg-gradient-to-r from-[#6366f1] to-[#818cf8] bg-clip-text text-transparent">
              Made Provable
            </span>
          </h1>

          <p className="mx-auto mt-6 max-w-2xl text-lg text-[#71717a]">
            The neuro-symbolic compliance layer for AI agents. Formal verification
            with Z3, immutable audit trails, and one-click Annex IV documentation.
            Every decision mathematically guaranteed.
          </p>

          <div className="mt-10 flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
            <Link href="/dashboard" onClick={() => analytics.ctaClick("hero-open-dashboard")}>
              <Button
                size="lg"
                className="bg-[#6366f1] hover:bg-[#5558e6] text-white px-8 py-6 text-base"
              >
                Open Dashboard
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
            <div className="rounded-lg border border-[#1e1e2e] bg-[#111119] px-6 py-3 font-mono text-sm text-[#71717a]">
              pip install chimera-compliance
            </div>
          </div>

          {/* Stats */}
          <div className="mt-16 grid grid-cols-2 gap-8 sm:grid-cols-4">
            {[
              { label: "Decisions Audited", value: "∞" },
              { label: "Z3 Verified", value: "100%" },
              { label: "Framework Integrations", value: "5+" },
              { label: "EU AI Act Articles", value: "6/6" },
            ].map((stat) => (
              <div key={stat.label} className="text-center">
                <div className="text-3xl font-bold text-white">{stat.value}</div>
                <div className="mt-1 text-sm text-[#71717a]">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="border-t border-[#1e1e2e] py-24">
        <div className="mx-auto max-w-7xl px-6">
          <div className="text-center">
            <Badge
              variant="outline"
              className="mb-4 border-[#22c55e]/30 bg-[#22c55e]/10 text-[#22c55e]"
            >
              Features
            </Badge>
            <h2 className="text-3xl font-bold text-white sm:text-4xl">
              Enterprise-Grade Compliance Infrastructure
            </h2>
            <p className="mx-auto mt-4 max-w-2xl text-[#71717a]">
              From formal policy verification to automated documentation — every tool
              you need for EU AI Act compliance.
            </p>
          </div>

          <div className="mt-16 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {features.map((feature) => (
              <Card
                key={feature.title}
                className="border-[#1e1e2e] bg-[#111119] hover:border-[#6366f1]/30 transition-colors"
              >
                <CardHeader>
                  <feature.icon className="h-10 w-10 text-[#6366f1] mb-2" />
                  <CardTitle className="text-white">{feature.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription className="text-[#71717a] text-sm leading-relaxed">
                    {feature.description}
                  </CardDescription>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Integrations */}
      <section
        id="integrations"
        className="border-t border-[#1e1e2e] py-24 bg-[#0d0d14]"
      >
        <div className="mx-auto max-w-7xl px-6 text-center">
          <Badge
            variant="outline"
            className="mb-4 border-[#f59e0b]/30 bg-[#f59e0b]/10 text-[#f59e0b]"
          >
            <GitBranch className="mr-1 h-3 w-3" /> Integrations
          </Badge>
          <h2 className="text-3xl font-bold text-white">
            Works With Your Agent Framework
          </h2>
          <p className="mx-auto mt-4 max-w-xl text-[#71717a]">
            Drop-in compliance guards for every major AI agent framework.
            One line of code to protect your agents.
          </p>

          <div className="mt-12 flex flex-wrap items-center justify-center gap-4">
            {integrations.map((name) => (
              <div
                key={name}
                className="rounded-xl border border-[#1e1e2e] bg-[#111119] px-8 py-4 text-white font-medium hover:border-[#6366f1]/30 transition-colors"
              >
                {name}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="border-t border-[#1e1e2e] py-24">
        <div className="mx-auto max-w-7xl px-6">
          <div className="text-center">
            <Badge
              variant="outline"
              className="mb-4 border-[#6366f1]/30 bg-[#6366f1]/10 text-[#818cf8]"
            >
              Pricing
            </Badge>
            <h2 className="text-3xl font-bold text-white sm:text-4xl">
              Start Free, Scale With Confidence
            </h2>
            <p className="mx-auto mt-4 max-w-xl text-[#71717a]">
              The Python library is always free and unlimited.
              Cloud dashboard features scale with your needs.
            </p>
          </div>

          <div className="mt-16 grid gap-8 lg:grid-cols-3 items-stretch">
            {tiers.map((tier) => (
              <Card
                key={tier.name}
                className={`relative flex flex-col overflow-visible border-[#1e1e2e] bg-[#111119] ${
                  tier.highlight
                    ? "border-[#6366f1] ring-1 ring-[#6366f1]/20"
                    : ""
                }`}
              >
                {tier.highlight && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 z-10">
                    <Badge className="bg-[#6366f1] text-white px-4 py-1 shadow-lg shadow-[#6366f1]/25">
                      {tier.badge}
                    </Badge>
                  </div>
                )}
                <CardHeader className="pb-4">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-white text-xl">
                      {tier.name}
                    </CardTitle>
                    {!tier.highlight && (
                      <Badge
                        variant="outline"
                        className="border-[#1e1e2e] text-[#71717a]"
                      >
                        {tier.badge}
                      </Badge>
                    )}
                  </div>
                  <div className="mt-4">
                    {tier.originalPrice && (
                      <span className="text-lg text-[#71717a] line-through mr-2">
                        {tier.originalPrice}
                      </span>
                    )}
                    <span className="text-4xl font-bold text-white">
                      {tier.price}
                    </span>
                    <span className="text-[#71717a] ml-1">{tier.period}</span>
                    {tier.launchDeal && (
                      <span className="ml-2 inline-block rounded-full bg-[#22c55e]/10 border border-[#22c55e]/30 px-2.5 py-0.5 text-[10px] font-semibold text-[#22c55e] uppercase">
                        Launch Special
                      </span>
                    )}
                    {tier.betaFree && (
                      <div className="mt-2 flex items-center gap-2 rounded-lg border border-[#f59e0b]/20 bg-[#f59e0b]/5 px-3 py-1.5">
                        <Sparkles className="h-3.5 w-3.5 text-[#f59e0b] shrink-0" />
                        <span className="text-[11px] text-[#f59e0b] font-medium">
                          Free for first 100 beta testers
                        </span>
                      </div>
                    )}
                  </div>
                  <CardDescription className="text-[#71717a] mt-2">
                    {tier.description}
                  </CardDescription>
                </CardHeader>
                <CardContent className="flex flex-col flex-1">
                  <ul className="space-y-3 flex-1">
                    {tier.features.map((feature) => (
                      <li
                        key={feature}
                        className="flex items-start gap-2 text-sm text-[#e4e4e7]"
                      >
                        <Check className="h-4 w-4 text-[#22c55e] mt-0.5 shrink-0" />
                        {feature}
                      </li>
                    ))}
                  </ul>
                  <div className="mt-8 space-y-3">
                    <Link href={tier.href} className="block" onClick={() => analytics.pricingClick(tier.name.toLowerCase())}>
                      <Button
                        className={`w-full ${
                          tier.highlight
                            ? "bg-[#6366f1] hover:bg-[#5558e6] text-white"
                            : "bg-[#1e1e2e] hover:bg-[#2e2e3e] text-white"
                        }`}
                      >
                        {tier.cta}
                      </Button>
                    </Link>
                    <Link href="/demo" className="block" onClick={() => analytics.ctaClick("try-demo")}>
                      <Button
                        variant="outline"
                        className="w-full border-[#6366f1]/30 bg-[#6366f1]/5 text-[#818cf8] hover:bg-[#6366f1]/10 hover:text-white"
                      >
                        <Zap className="mr-2 h-3.5 w-3.5" />
                        Try Interactive Demo
                      </Button>
                    </Link>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="border-t border-[#1e1e2e] py-24 bg-[#0d0d14]">
        <div className="mx-auto max-w-3xl px-6 text-center">
          <h2 className="text-3xl font-bold text-white">
            Ready to Make Your AI Compliant?
          </h2>
          <p className="mt-4 text-[#71717a]">
            Install in 60 seconds. No credit card required.
            Your first audit record in under 5 minutes.
          </p>
          <div className="mt-8 flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
            <div className="rounded-lg border border-[#1e1e2e] bg-[#111119] px-6 py-3 font-mono text-sm text-[#e4e4e7]">
              pip install chimera-compliance
            </div>
            <Link href="/dashboard" onClick={() => analytics.ctaClick("bottom-cta-dashboard")}>
              <Button className="bg-[#6366f1] hover:bg-[#5558e6] text-white">
                Open Dashboard <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-[#1e1e2e] py-12">
        <div className="mx-auto max-w-7xl px-6">
          <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
            <div className="flex items-center gap-2">
              <Shield className="h-5 w-5 text-[#6366f1]" />
              <span className="text-sm font-medium text-white">
                Chimera Compliance
              </span>
              <span className="text-sm text-[#71717a]">v3.0.0</span>
            </div>
            <div className="text-sm text-[#71717a]">
              EU AI Act compliant. Open source core.
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
