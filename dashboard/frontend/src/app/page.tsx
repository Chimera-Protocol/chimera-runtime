"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import {
  Shield,
  Activity,
  FileText,
  Zap,
  Lock,
  Eye,
  Check,
  ArrowRight,
  Brain,
  X,
  Sparkles,
  Users,
  AlertTriangle,
  Cpu,
  Terminal,
  ChevronRight,
  Play,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { AuthNav } from "@/components/layout/AuthNav";
import { analytics } from "@/lib/analytics";
import { motion, useInView, useScroll, useTransform, AnimatePresence } from "framer-motion";

/* ─────────────────────────────────────────── DATA ─── */

const tiers = [
  {
    name: "Open Runtime",
    badge: "Free Forever",
    price: "$0",
    period: "",
    description: "Full local enforcement. No limits.",
    features: [
      "Deterministic runtime guard",
      "Unlimited policy enforcement",
      "Open-source CSL engine",
      "Z3 formal verification",
      "Full CLI & Python SDK",
    ],
    cta: "Get Started",
    href: "/register",
    highlight: false,
  },
  {
    name: "Pro Control",
    badge: "Popular",
    price: "$49",
    period: "/mo",
    description: "Analytics, traces, multi-agent control.",
    features: [
      "Everything in Open Runtime",
      "Decision analytics dashboard",
      "Full reasoning traces",
      "Real-time halt / resume",
      "Multi-agent monitoring",
      "Webhook & email alerts",
    ],
    cta: "Start Pro Trial",
    href: "/contact?plan=pro",
    highlight: true,
  },
  {
    name: "Enterprise",
    badge: "Contact Us",
    price: "Custom",
    period: "",
    description: "Governance at scale.",
    features: [
      "Everything in Pro",
      "Annex IV auto-generation",
      "SIEM integrations",
      "SSO / SAML / RBAC",
      "Causal root-cause analysis",
      "Dedicated support & SLA",
    ],
    cta: "Contact Sales",
    href: "/contact",
    highlight: false,
  },
];

/* ─────────────────────────────────── ANIMATED COMPONENTS ─── */

function GlitchText({ children, className = "" }: { children: string; className?: string }) {
  return (
    <span className={`relative inline-block ${className}`}>
      <span className="relative z-10">{children}</span>
      <span
        aria-hidden
        className="absolute inset-0 text-cyan-400 animate-glitch-1 z-0 opacity-70"
        style={{ clipPath: "inset(40% 0 20% 0)" }}
      >
        {children}
      </span>
      <span
        aria-hidden
        className="absolute inset-0 text-red-400 animate-glitch-2 z-0 opacity-70"
        style={{ clipPath: "inset(60% 0 0 0)" }}
      >
        {children}
      </span>
    </span>
  );
}

function TypewriterCode() {
  const lines = [
    { text: "from chimera_runtime import load_guard", delay: 0 },
    { text: "", delay: 800 },
    { text: 'guard = load_guard("policy.csl")', delay: 1200 },
    { text: "agent = guard.wrap(agent)", delay: 2000 },
    { text: "", delay: 2800 },
    { text: "# Your AI is now constrained.", delay: 3200 },
    { text: "# No exceptions. No bypass.", delay: 4000 },
  ];

  const [visibleLines, setVisibleLines] = useState(0);
  const [currentChar, setCurrentChar] = useState(0);

  useEffect(() => {
    if (visibleLines >= lines.length) return;

    const line = lines[visibleLines];
    if (currentChar < line.text.length) {
      const t = setTimeout(() => setCurrentChar((c) => c + 1), 25 + Math.random() * 35);
      return () => clearTimeout(t);
    } else {
      const t = setTimeout(() => {
        setVisibleLines((v) => v + 1);
        setCurrentChar(0);
      }, 300);
      return () => clearTimeout(t);
    }
  }, [visibleLines, currentChar]);

  const colorize = (text: string) => {
    if (text.startsWith("#")) return <span className="text-zinc-600">{text}</span>;
    return text.split(/(\b(?:from|import|def|class|return|if|else|True|False|None)\b)/g).map((part, i) => {
      if (["from", "import", "def", "class", "return", "if", "else"].includes(part))
        return <span key={i} className="text-[#c678dd]">{part}</span>;
      if (["True", "False", "None"].includes(part))
        return <span key={i} className="text-[#d19a66]">{part}</span>;
      // strings
      const strMatch = part.match(/(".*?")/g);
      if (strMatch) {
        return <span key={i}>{
          part.split(/(".*?")/g).map((s, j) =>
            s.startsWith('"') ? <span key={j} className="text-[#98c379]">{s}</span> : <span key={j} className="text-[#abb2bf]">{s}</span>
          )
        }</span>;
      }
      return <span key={i} className="text-[#abb2bf]">{part}</span>;
    });
  };

  return (
    <div className="font-mono text-sm leading-7 select-none">
      {lines.slice(0, visibleLines + 1).map((line, i) => (
        <div key={i} className="flex">
          <span className="text-zinc-700 w-8 text-right mr-4 select-none">{i + 1}</span>
          <span>
            {i < visibleLines ? colorize(line.text) : colorize(line.text.slice(0, currentChar))}
            {i === visibleLines && <span className="animate-blink text-[#528bff]">|</span>}
          </span>
        </div>
      ))}
    </div>
  );
}

function RuntimeSimulation() {
  const decisions = [
    { action: "transfer_funds($450K)", result: "BLOCKED", rule: "manager_limit", time: "0.3ms" },
    { action: "deploy_model(prod)", result: "ALLOWED", rule: "deploy_policy", time: "0.2ms" },
    { action: "delete_records(all)", result: "BLOCKED", rule: "data_retention", time: "0.1ms" },
    { action: "approve_budget($80K)", result: "ALLOWED", rule: "budget_policy", time: "0.2ms" },
    { action: "modify_acl(root)", result: "ASK_HUMAN", rule: "privilege_escalation", time: "0.4ms" },
    { action: "send_email(bulk)", result: "BLOCKED", rule: "comm_policy", time: "0.1ms" },
  ];

  const [active, setActive] = useState(0);
  const [flash, setFlash] = useState(false);

  useEffect(() => {
    const t = setInterval(() => {
      setFlash(true);
      setTimeout(() => setFlash(false), 150);
      setActive((a) => (a + 1) % decisions.length);
    }, 2000);
    return () => clearInterval(t);
  }, []);

  return (
    <div className="relative rounded-xl border border-zinc-800/50 bg-[#0c0c14] overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-zinc-900/30 border-b border-zinc-800/50">
        <div className="flex items-center gap-2">
          <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
          <span className="text-[10px] font-mono text-zinc-500 uppercase tracking-wider">Runtime Active</span>
        </div>
        <span className="text-[10px] font-mono text-zinc-600">chimera v1.0.0</span>
      </div>

      {/* Feed */}
      <div className="p-3 space-y-1">
        {decisions.map((d, i) => {
          const isActive = i === active;
          const isPast = i < active || (i > active && i < decisions.length);
          return (
            <motion.div
              key={i}
              initial={false}
              animate={{
                opacity: isActive ? 1 : 0.3,
                scale: isActive ? 1 : 0.98,
                x: isActive && flash ? [-2, 2, -1, 0] : 0,
              }}
              transition={{ duration: 0.2 }}
              className={`flex items-center justify-between px-3 py-1.5 rounded font-mono text-[11px] ${
                isActive ? "bg-zinc-800/40" : ""
              }`}
            >
              <div className="flex items-center gap-2 flex-1 min-w-0">
                <ChevronRight className={`h-3 w-3 shrink-0 ${isActive ? "text-cyan-400" : "text-zinc-700"}`} />
                <span className="text-zinc-400 truncate">{d.action}</span>
              </div>
              <div className="flex items-center gap-3 shrink-0">
                <span className="text-zinc-600 text-[10px]">{d.time}</span>
                <span
                  className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                    d.result === "BLOCKED"
                      ? "bg-red-500/10 text-red-400"
                      : d.result === "ALLOWED"
                      ? "bg-green-500/10 text-green-400"
                      : "bg-amber-500/10 text-amber-400"
                  }`}
                >
                  {d.result}
                </span>
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}

function FadeInSection({ children, className = "", delay = 0 }: { children: React.ReactNode; className?: string; delay?: number }) {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: "-80px" });
  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 40 }}
      animate={inView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.7, delay, ease: [0.22, 1, 0.36, 1] }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

function ScrollingMarquee() {
  const items = [
    "DETERMINISTIC", "VERIFIABLE", "CONTROLLABLE", "Z3 PROVEN",
    "FORMALLY VERIFIED", "ZERO BYPASS", "CONSTRAINT ENFORCED",
    "AUDIT COMPLETE", "POLICY GUARD", "RUNTIME ACTIVE",
  ];
  return (
    <div className="relative overflow-hidden border-y border-zinc-800/50 bg-[#08080d] py-3">
      <div className="animate-marquee flex whitespace-nowrap">
        {[...items, ...items].map((item, i) => (
          <span key={i} className="mx-6 text-[11px] font-mono tracking-[0.2em] text-zinc-700 uppercase">
            {item} <span className="text-indigo-500/40 mx-2">/</span>
          </span>
        ))}
      </div>
    </div>
  );
}

function GridBackground() {
  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      <div
        className="absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage: `linear-gradient(rgba(99,102,241,0.3) 1px, transparent 1px), linear-gradient(90deg, rgba(99,102,241,0.3) 1px, transparent 1px)`,
          backgroundSize: "60px 60px",
        }}
      />
      <div className="absolute top-1/4 left-1/3 w-[600px] h-[600px] bg-indigo-500/[0.03] rounded-full blur-[150px]" />
      <div className="absolute bottom-1/4 right-1/4 w-[500px] h-[500px] bg-cyan-400/[0.02] rounded-full blur-[150px]" />
    </div>
  );
}

/* ─────────────────────────────────── MAIN PAGE ─── */

export default function LandingPage() {
  const [showBetaPopup, setShowBetaPopup] = useState(false);
  const { scrollYProgress } = useScroll();
  const progressWidth = useTransform(scrollYProgress, [0, 1], ["0%", "100%"]);

  useEffect(() => {
    const dismissed = sessionStorage.getItem("beta-popup-dismissed");
    if (!dismissed) {
      const timer = setTimeout(() => setShowBetaPopup(true), 4000);
      return () => clearTimeout(timer);
    }
  }, []);

  const dismissPopup = () => {
    setShowBetaPopup(false);
    sessionStorage.setItem("beta-popup-dismissed", "1");
  };

  return (
    <div className="min-h-screen bg-[#06060b] text-white selection:bg-indigo-500/30 selection:text-white">
      {/* ── SCROLL PROGRESS ── */}
      <motion.div
        className="fixed top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-indigo-500 via-cyan-400 to-indigo-500 z-[60] origin-left"
        style={{ width: progressWidth }}
      />

      {/* ── BETA POPUP ── */}
      <AnimatePresence>
        {showBetaPopup && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[100] flex items-center justify-center bg-black/70 backdrop-blur-md"
          >
            <motion.div
              initial={{ scale: 0.9, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.9, y: 20 }}
              className="relative mx-4 w-full max-w-md rounded-2xl border border-indigo-500/20 bg-[#0c0c14] p-8 shadow-2xl shadow-indigo-500/5"
            >
              <button onClick={dismissPopup} className="absolute right-4 top-4 text-zinc-600 hover:text-white transition">
                <X className="h-5 w-5" />
              </button>
              <div className="flex items-center gap-3 mb-4">
                <div className="h-12 w-12 rounded-xl bg-indigo-500/10 flex items-center justify-center border border-indigo-500/20">
                  <Sparkles className="h-6 w-6 text-indigo-400" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-white">Early Access</h3>
                  <p className="text-xs text-cyan-400 font-mono">First 100 users get Pro free</p>
                </div>
              </div>
              <p className="text-sm text-zinc-400 mb-6">
                Join the first wave of teams enforcing <span className="text-white font-medium">deterministic AI behavior</span>.
              </p>
              <div className="flex gap-3">
                <Link href="/contact?plan=pro" className="flex-1" onClick={() => { analytics.ctaClick("beta-claim-pro"); dismissPopup(); }}>
                  <Button className="w-full bg-indigo-500 hover:bg-indigo-600 text-white font-medium">
                    Claim Free Pro
                  </Button>
                </Link>
                <Button variant="outline" className="border-zinc-800 text-zinc-500 hover:text-white hover:border-zinc-600" onClick={dismissPopup}>
                  Later
                </Button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── NAV ── */}
      <nav className="fixed top-0 z-50 w-full border-b border-zinc-800/50 bg-[#06060b]/80 backdrop-blur-xl">
        <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-6">
          <Link href="/" className="flex items-center gap-2 group">
            <div className="h-7 w-7 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center group-hover:border-indigo-500/40 transition">
              <Shield className="h-3.5 w-3.5 text-indigo-400" />
            </div>
            <span className="text-sm font-bold tracking-tight">
              CHIMERA<span className="text-indigo-400">_</span>
            </span>
          </Link>
          <div className="hidden items-center gap-8 md:flex">
            {[
              { href: "#problem", label: "Problem" },
              { href: "#how", label: "How" },
              { href: "#code", label: "Code" },
              { href: "#pricing", label: "Pricing" },
              { href: "/docs", label: "Docs", external: true },
            ].map((item) =>
              item.external ? (
                <Link key={item.label} href={item.href} className="text-xs font-mono text-zinc-600 hover:text-white transition uppercase tracking-wider">
                  {item.label}
                </Link>
              ) : (
                <a key={item.label} href={item.href} className="text-xs font-mono text-zinc-600 hover:text-white transition uppercase tracking-wider">
                  {item.label}
                </a>
              )
            )}
          </div>
          <AuthNav />
        </div>
      </nav>

      {/* ═══════════════════════════════════════════════════════════════
          HERO
      ═══════════════════════════════════════════════════════════════ */}
      <section className="relative min-h-screen flex items-center justify-center pt-14 overflow-hidden">
        <GridBackground />

        {/* Scanline overlay */}
        <div className="absolute inset-0 pointer-events-none opacity-[0.015] z-20"
          style={{
            backgroundImage: "repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(255,255,255,0.03) 2px, rgba(255,255,255,0.03) 4px)",
          }}
        />

        <div className="relative z-10 mx-auto max-w-6xl px-6">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            {/* Left: Text */}
            <div>
              <motion.div
                initial={{ opacity: 0, x: -30 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
              >
                <div className="flex items-center gap-2 mb-8">
                  <div className="h-1.5 w-1.5 rounded-full bg-green-400 animate-pulse" />
                  <span className="text-[11px] font-mono text-zinc-500 uppercase tracking-[0.2em]">Runtime Active</span>
                </div>

                <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black tracking-tight leading-[1.1]">
                  <GlitchText className="text-white">Deterministic</GlitchText>
                  <br />
                  <span className="text-white">Runtime for</span>
                  <br />
                  <span className="bg-gradient-to-r from-indigo-400 via-cyan-400 to-indigo-400 bg-clip-text text-transparent bg-[length:200%_auto] animate-gradient">
                    AI Agents
                  </span>
                </h1>

                <p className="mt-6 text-lg text-zinc-500 max-w-md leading-relaxed">
                  Stop trusting LLMs. Start constraining them.
                  <br />
                  <span className="text-zinc-400">Every decision enforced — not suggested.</span>
                </p>

                <div className="mt-10 flex flex-col sm:flex-row items-start gap-4">
                  <div
                    className="group flex items-center gap-3 rounded-lg border border-zinc-800 bg-[#0c0c14] px-5 py-3 font-mono text-sm cursor-pointer hover:border-indigo-500/30 transition-all"
                    onClick={() => navigator.clipboard?.writeText("pip install chimera-runtime")}
                  >
                    <span className="text-zinc-600">$</span>
                    <span className="text-cyan-400 select-all">pip install chimera-runtime</span>
                    <span className="text-[10px] text-zinc-700 group-hover:text-zinc-500 transition">COPY</span>
                  </div>
                  <Link href="/dashboard" onClick={() => analytics.ctaClick("hero-dashboard")}>
                    <Button className="bg-indigo-500 hover:bg-indigo-600 text-white px-6 h-12">
                      Open Dashboard <ArrowRight className="ml-2 h-4 w-4" />
                    </Button>
                  </Link>
                </div>

                <div className="mt-10 flex flex-wrap items-center gap-3">
                  {["LangChain", "OpenAI", "CrewAI", "LlamaIndex", "AutoGen"].map((fw) => (
                    <span key={fw} className="text-[10px] font-mono text-zinc-700 border border-zinc-800/50 rounded px-2 py-1 uppercase tracking-wider">
                      {fw}
                    </span>
                  ))}
                </div>
              </motion.div>
            </div>

            {/* Right: Live Simulation */}
            <motion.div
              initial={{ opacity: 0, x: 30 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.8, delay: 0.3, ease: [0.22, 1, 0.36, 1] }}
            >
              <RuntimeSimulation />
            </motion.div>
          </div>
        </div>
      </section>

      {/* ── MARQUEE ── */}
      <ScrollingMarquee />

      {/* ═══════════════════════════════════════════════════════════════
          PROBLEM
      ═══════════════════════════════════════════════════════════════ */}
      <section id="problem" className="relative py-32 overflow-hidden">
        <GridBackground />
        <div className="relative z-10 mx-auto max-w-5xl px-6">
          <FadeInSection className="text-center mb-20">
            <span className="text-[11px] font-mono text-red-400/70 uppercase tracking-[0.3em] mb-4 block">The Problem</span>
            <h2 className="text-3xl sm:text-5xl font-black text-white leading-tight">
              LLMs don&apos;t follow rules.
              <br />
              <span className="text-zinc-600">They approximate them.</span>
            </h2>
          </FadeInSection>

          <div className="grid sm:grid-cols-3 gap-4">
            {[
              { icon: AlertTriangle, text: "They hallucinate", sub: "Confident lies with citations", color: "red" },
              { icon: Lock, text: "They get injected", sub: "One prompt to bypass everything", color: "red" },
              { icon: X, text: "They break silently", sub: "No error. No log. Just wrong.", color: "red" },
            ].map((item, i) => (
              <FadeInSection key={item.text} delay={i * 0.1}>
                <motion.div
                  whileHover={{ y: -4, borderColor: "rgba(239,68,68,0.3)" }}
                  className="rounded-xl border border-zinc-800/50 bg-[#0c0c14] p-6 transition-colors"
                >
                  <item.icon className="h-6 w-6 text-red-400/60 mb-4" />
                  <p className="text-base font-bold text-white mb-1">{item.text}</p>
                  <p className="text-xs text-zinc-600">{item.sub}</p>
                </motion.div>
              </FadeInSection>
            ))}
          </div>

          <FadeInSection delay={0.3} className="mt-16 text-center">
            <p className="text-lg text-zinc-600">
              And yet, we hand them real-world decisions.{" "}
            </p>
            <p className="text-xl font-bold text-white mt-2">This is the flaw.</p>
          </FadeInSection>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════════
          PARADIGM SHIFT
      ═══════════════════════════════════════════════════════════════ */}
      <section className="relative py-32 border-t border-zinc-800/30">
        <div className="mx-auto max-w-4xl px-6 text-center">
          <FadeInSection>
            <span className="text-[11px] font-mono text-cyan-400/70 uppercase tracking-[0.3em] mb-4 block">Paradigm Shift</span>
            <h2 className="text-3xl sm:text-5xl font-black text-white leading-tight">
              AI doesn&apos;t need
              <br />better prompts.
            </h2>
            <p className="text-3xl sm:text-5xl font-black mt-2 bg-gradient-to-r from-indigo-400 to-cyan-400 bg-clip-text text-transparent">
              It needs laws.
            </p>
          </FadeInSection>

          <FadeInSection delay={0.2}>
            <div className="mt-14 relative">
              <motion.div
                whileHover={{ scale: 1.02 }}
                className="inline-block rounded-xl border border-indigo-500/20 bg-indigo-500/[0.03] px-10 py-6 backdrop-blur-sm"
              >
                <p className="text-xs font-mono text-indigo-400/60 uppercase tracking-[0.3em] mb-2">Execution Model</p>
                <span className="text-2xl sm:text-3xl font-black bg-gradient-to-r from-indigo-300 via-cyan-300 to-indigo-300 bg-clip-text text-transparent">
                  Lawful State Evolution
                </span>
              </motion.div>
            </div>

            <p className="mt-10 text-lg text-zinc-500 max-w-2xl mx-auto">
              AI systems no longer <em className="text-zinc-400 not-italic">try</em> to follow rules.{" "}
              <span className="text-white font-bold">They are structurally incapable of violating them.</span>
            </p>
          </FadeInSection>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════════
          SOLUTION
      ═══════════════════════════════════════════════════════════════ */}
      <section className="relative py-32 border-t border-zinc-800/30">
        <GridBackground />
        <div className="relative z-10 mx-auto max-w-5xl px-6">
          <FadeInSection className="text-center mb-16">
            <span className="text-[11px] font-mono text-indigo-400/70 uppercase tracking-[0.3em] mb-4 block">The Solution</span>
            <h2 className="text-3xl sm:text-5xl font-black text-white">
              Not a wrapper. Not a filter.
            </h2>
            <p className="text-xl text-zinc-500 mt-4">A runtime.</p>
          </FadeInSection>

          <div className="grid sm:grid-cols-3 gap-4">
            {[
              { icon: Lock, title: "Enforce", desc: "Constraints live outside the model. The model's opinion is irrelevant.", accent: "indigo" },
              { icon: Cpu, title: "Verify", desc: "Z3 theorem prover validates every policy. Mathematically. Before deployment.", accent: "cyan" },
              { icon: Shield, title: "Block", desc: "Invalid actions die before execution. No recovery needed. No damage done.", accent: "indigo" },
            ].map((item, i) => (
              <FadeInSection key={item.title} delay={i * 0.1}>
                <motion.div
                  whileHover={{ y: -6 }}
                  className="group rounded-xl border border-zinc-800/50 bg-[#0c0c14] p-8 transition-all hover:border-indigo-500/20"
                >
                  <item.icon className={`h-8 w-8 mb-4 ${item.accent === "cyan" ? "text-cyan-400/60" : "text-indigo-400/60"} group-hover:${item.accent === "cyan" ? "text-cyan-400" : "text-indigo-400"} transition`} />
                  <h3 className="text-xl font-black text-white mb-2">{item.title}</h3>
                  <p className="text-sm text-zinc-500 leading-relaxed">{item.desc}</p>
                </motion.div>
              </FadeInSection>
            ))}
          </div>

          {/* Enforcement pipeline */}
          <FadeInSection delay={0.3} className="mt-16">
            <div className="flex items-center justify-center gap-2 sm:gap-4 font-mono text-sm">
              {["Checked", "Proven", "Enforced"].map((step, i) => (
                <motion.div
                  key={step}
                  className="flex items-center gap-2 sm:gap-4"
                  initial={{ opacity: 0 }}
                  whileInView={{ opacity: 1 }}
                  transition={{ delay: 0.5 + i * 0.2 }}
                  viewport={{ once: true }}
                >
                  {i > 0 && <span className="text-zinc-700">{">"}</span>}
                  <span className={`px-4 py-2 rounded-lg border ${
                    i === 2
                      ? "border-cyan-400/30 bg-cyan-400/5 text-cyan-400"
                      : "border-zinc-800 bg-zinc-900/30 text-zinc-400"
                  }`}>
                    {step}
                  </span>
                </motion.div>
              ))}
            </div>
          </FadeInSection>
        </div>
      </section>

      {/* ── MARQUEE 2 ── */}
      <ScrollingMarquee />

      {/* ═══════════════════════════════════════════════════════════════
          HOW IT WORKS
      ═══════════════════════════════════════════════════════════════ */}
      <section id="how" className="relative py-32">
        <div className="mx-auto max-w-5xl px-6">
          <FadeInSection className="text-center mb-20">
            <span className="text-[11px] font-mono text-cyan-400/70 uppercase tracking-[0.3em] mb-4 block">How It Works</span>
            <h2 className="text-3xl sm:text-4xl font-black text-white">
              Three steps. Zero trust in the model.
            </h2>
          </FadeInSection>

          <div className="space-y-4">
            {[
              {
                num: "01",
                title: "Define Constraints",
                desc: "Write policies in CSL — Constraint Specification Language. Human-readable. Machine-enforceable. Not a prompt. A specification.",
                code: 'STATE_CONSTRAINT limit {\n  WHEN role == "MANAGER"\n  THEN amount <= 250000\n}',
              },
              {
                num: "02",
                title: "Verify Correctness",
                desc: "Z3 theorem prover checks reachability, consistency, and conflict-freedom. Your policy is mathematically proven correct before a single agent runs.",
                code: "$ chimera-runtime verify policy.csl\n  Syntax     ✓\n  Z3 SAT     ✓ Consistent\n  Conflicts  ✓ None found",
              },
              {
                num: "03",
                title: "Enforce at Runtime",
                desc: "Every agent action passes through the constraint guard. The guard is deterministic. Not probabilistic. Not negotiable.",
                code: "Agent: transfer($500K)\nGuard: BLOCKED [manager_limit]\n→ amount 500000 > limit 250000\n→ Audit record: dec_8f3a2b...",
              },
            ].map((step, i) => (
              <FadeInSection key={step.num} delay={i * 0.1}>
                <motion.div
                  whileHover={{ x: 4 }}
                  className="grid lg:grid-cols-2 gap-6 rounded-xl border border-zinc-800/50 bg-[#0c0c14] p-6 lg:p-8 hover:border-indigo-500/20 transition-colors"
                >
                  <div>
                    <span className="text-4xl font-black text-indigo-500/20">{step.num}</span>
                    <h3 className="text-xl font-black text-white mt-2 mb-3">{step.title}</h3>
                    <p className="text-sm text-zinc-500 leading-relaxed">{step.desc}</p>
                  </div>
                  <div className="rounded-lg bg-[#08080d] border border-zinc-800/30 p-4 font-mono text-xs text-zinc-400 overflow-x-auto">
                    <pre className="whitespace-pre">{step.code}</pre>
                  </div>
                </motion.div>
              </FadeInSection>
            ))}
          </div>

          <FadeInSection delay={0.3} className="mt-12 text-center">
            <p className="text-sm font-mono text-zinc-600">
              No exceptions. <span className="text-white">No bypass.</span>
            </p>
          </FadeInSection>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════════
          BEFORE / AFTER
      ═══════════════════════════════════════════════════════════════ */}
      <section className="py-24 border-t border-zinc-800/30">
        <div className="mx-auto max-w-4xl px-6">
          <FadeInSection>
            <div className="grid md:grid-cols-2 gap-4">
              <motion.div
                whileHover={{ scale: 1.02 }}
                className="rounded-xl border border-red-500/10 bg-red-500/[0.02] p-8"
              >
                <p className="text-[10px] font-mono text-red-400/60 uppercase tracking-[0.3em] mb-4">Before Chimera</p>
                <p className="text-xl sm:text-2xl font-bold text-zinc-500 italic leading-snug">
                  &ldquo;The model <span className="text-red-400">should</span> follow this rule...&rdquo;
                </p>
              </motion.div>
              <motion.div
                whileHover={{ scale: 1.02 }}
                className="rounded-xl border border-cyan-400/20 bg-cyan-400/[0.02] p-8"
              >
                <p className="text-[10px] font-mono text-cyan-400/60 uppercase tracking-[0.3em] mb-4">After Chimera</p>
                <p className="text-xl sm:text-2xl font-bold text-white leading-snug">
                  &ldquo;The system <span className="text-cyan-400">cannot</span> violate this rule.&rdquo;
                </p>
              </motion.div>
            </div>
          </FadeInSection>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════════
          CODE
      ═══════════════════════════════════════════════════════════════ */}
      <section id="code" className="relative py-32 border-t border-zinc-800/30">
        <GridBackground />
        <div className="relative z-10 mx-auto max-w-4xl px-6">
          <FadeInSection className="text-center mb-12">
            <span className="text-[11px] font-mono text-indigo-400/70 uppercase tracking-[0.3em] mb-4 block">For Developers</span>
            <h2 className="text-3xl sm:text-4xl font-black text-white">
              Three lines. Full constraint.
            </h2>
          </FadeInSection>

          <FadeInSection delay={0.2}>
            <div className="rounded-xl border border-zinc-800/50 bg-[#0c0c14] overflow-hidden shadow-2xl shadow-black/50">
              {/* Terminal chrome */}
              <div className="flex items-center gap-2 px-4 py-3 bg-[#0a0a10] border-b border-zinc-800/50">
                <div className="flex gap-1.5">
                  <div className="h-2.5 w-2.5 rounded-full bg-[#ff5f57]" />
                  <div className="h-2.5 w-2.5 rounded-full bg-[#febc2e]" />
                  <div className="h-2.5 w-2.5 rounded-full bg-[#28c840]" />
                </div>
                <span className="ml-3 text-[10px] font-mono text-zinc-600">main.py — chimera_runtime</span>
              </div>
              {/* Code */}
              <div className="p-6">
                <TypewriterCode />
              </div>
            </div>
          </FadeInSection>

          <FadeInSection delay={0.4} className="mt-10 flex flex-wrap items-center justify-center gap-3">
            {["Deterministic", "Verifiable", "Controllable"].map((tag) => (
              <span key={tag} className="text-[10px] font-mono uppercase tracking-[0.2em] text-cyan-400/70 border border-cyan-400/10 rounded-full px-4 py-1.5 bg-cyan-400/[0.02]">
                {tag}
              </span>
            ))}
          </FadeInSection>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════════
          REAL-TIME CONTROL
      ═══════════════════════════════════════════════════════════════ */}
      <section className="py-32 border-t border-zinc-800/30">
        <div className="mx-auto max-w-5xl px-6">
          <FadeInSection className="text-center mb-16">
            <span className="text-[11px] font-mono text-indigo-400/70 uppercase tracking-[0.3em] mb-4 block">Control Plane</span>
            <h2 className="text-3xl sm:text-4xl font-black text-white">
              Not just enforcement — <span className="text-cyan-400">visibility</span>
            </h2>
          </FadeInSection>

          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {[
              { icon: Activity, label: "Decisions", desc: "ALLOW / BLOCK in real-time", accent: "green" },
              { icon: Brain, label: "Traces", desc: "Full causal reasoning chain", accent: "indigo" },
              { icon: Eye, label: "Intervention", desc: "Halt, override, resume", accent: "cyan" },
              { icon: Users, label: "Fleet", desc: "Multi-agent monitoring", accent: "indigo" },
            ].map((item, i) => (
              <FadeInSection key={item.label} delay={i * 0.08}>
                <motion.div
                  whileHover={{ y: -4 }}
                  className="rounded-xl border border-zinc-800/50 bg-[#0c0c14] p-6 hover:border-indigo-500/20 transition-colors"
                >
                  <item.icon className={`h-5 w-5 mb-3 ${
                    item.accent === "green" ? "text-green-400/60" : item.accent === "cyan" ? "text-cyan-400/60" : "text-indigo-400/60"
                  }`} />
                  <p className="text-sm font-bold text-white mb-1">{item.label}</p>
                  <p className="text-[11px] text-zinc-600">{item.desc}</p>
                </motion.div>
              </FadeInSection>
            ))}
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════════
          CAUSAL INTELLIGENCE
      ═══════════════════════════════════════════════════════════════ */}
      <section className="py-32 border-t border-zinc-800/30">
        <div className="mx-auto max-w-4xl px-6 text-center">
          <FadeInSection>
            <span className="text-[11px] font-mono text-cyan-400/70 uppercase tracking-[0.3em] mb-4 block">Causal Intelligence</span>
            <h2 className="text-3xl sm:text-4xl font-black text-white mb-4">
              Beyond guardrails.
            </h2>
            <p className="text-zinc-600 mb-12">Chimera doesn&apos;t just stop violations. It explains them.</p>
          </FadeInSection>

          <FadeInSection delay={0.2}>
            <div className="space-y-3 max-w-md mx-auto">
              {[
                "Why a violation happened",
                "Which constraint triggered it",
                "What causal chain led there",
              ].map((trace, i) => (
                <motion.div
                  key={trace}
                  initial={{ opacity: 0, x: -20 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.3 + i * 0.15 }}
                  viewport={{ once: true }}
                  className="flex items-center gap-3 rounded-lg border border-zinc-800/50 bg-[#0c0c14] px-5 py-3 text-left"
                >
                  <ArrowRight className="h-3.5 w-3.5 text-cyan-400/60 shrink-0" />
                  <span className="text-sm text-zinc-300">{trace}</span>
                </motion.div>
              ))}
            </div>
          </FadeInSection>

          <FadeInSection delay={0.5} className="mt-12">
            <p className="text-sm text-zinc-600">
              This is not explainability. <span className="text-white font-bold">This is causal accountability.</span>
            </p>
          </FadeInSection>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════════
          COMPLIANCE (secondary)
      ═══════════════════════════════════════════════════════════════ */}
      <section className="py-24 border-t border-zinc-800/30">
        <div className="mx-auto max-w-4xl px-6 text-center">
          <FadeInSection>
            <p className="text-xs font-mono text-zinc-600 uppercase tracking-[0.3em] mb-4">EU AI Act</p>
            <h2 className="text-2xl sm:text-3xl font-black text-white mb-3">
              Compliance is a consequence — <span className="text-zinc-500">not the product.</span>
            </h2>
            <p className="text-sm text-zinc-600 mb-10 max-w-xl mx-auto">
              When you enforce deterministic constraints by design, compliance follows automatically.
            </p>
          </FadeInSection>

          <FadeInSection delay={0.2}>
            <div className="grid sm:grid-cols-3 gap-3">
              {[
                { art: "Annex IV", desc: "Auto-generated documentation" },
                { art: "Art. 14", desc: "Human oversight built-in" },
                { art: "Art. 12 & 86", desc: "Complete auditability" },
              ].map((item) => (
                <div key={item.art} className="rounded-lg border border-zinc-800/50 bg-[#0c0c14] p-5">
                  <p className="text-sm font-bold font-mono text-indigo-400/80">{item.art}</p>
                  <p className="text-[11px] text-zinc-600 mt-1">{item.desc}</p>
                </div>
              ))}
            </div>
          </FadeInSection>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════════
          ECOSYSTEM
      ═══════════════════════════════════════════════════════════════ */}
      <section className="py-24 border-t border-zinc-800/30">
        <div className="mx-auto max-w-5xl px-6 text-center">
          <FadeInSection>
            <span className="text-[11px] font-mono text-indigo-400/70 uppercase tracking-[0.3em] mb-4 block">Ecosystem</span>
            <h2 className="text-3xl font-black text-white mb-10">
              Works everywhere.
            </h2>
          </FadeInSection>

          <FadeInSection delay={0.2}>
            <div className="flex flex-wrap items-center justify-center gap-3">
              {["LangChain", "LangGraph", "OpenAI Agents", "CrewAI", "LlamaIndex", "AutoGen"].map((name) => (
                <motion.div
                  key={name}
                  whileHover={{ y: -3, borderColor: "rgba(99,102,241,0.3)" }}
                  className="rounded-lg border border-zinc-800/50 bg-[#0c0c14] px-6 py-3 text-sm font-mono text-zinc-400 transition-colors"
                >
                  {name}
                </motion.div>
              ))}
            </div>
            <p className="mt-8 text-xs font-mono text-zinc-700">
              One line. <span className="text-cyan-400/60">Full control.</span>
            </p>
          </FadeInSection>
        </div>
      </section>

      {/* ── MARQUEE 3 ── */}
      <ScrollingMarquee />

      {/* ═══════════════════════════════════════════════════════════════
          PRICING
      ═══════════════════════════════════════════════════════════════ */}
      <section id="pricing" className="relative py-32">
        <GridBackground />
        <div className="relative z-10 mx-auto max-w-6xl px-6">
          <FadeInSection className="text-center mb-16">
            <span className="text-[11px] font-mono text-indigo-400/70 uppercase tracking-[0.3em] mb-4 block">Pricing</span>
            <h2 className="text-3xl sm:text-4xl font-black text-white">
              Runtime is free. Forever.
            </h2>
            <p className="text-sm text-zinc-600 mt-3">Cloud control scales with you.</p>
          </FadeInSection>

          <div className="grid lg:grid-cols-3 gap-4 items-stretch">
            {tiers.map((tier, i) => (
              <FadeInSection key={tier.name} delay={i * 0.1}>
                <motion.div
                  whileHover={{ y: -6 }}
                  className={`relative flex flex-col rounded-xl border p-8 h-full transition-colors ${
                    tier.highlight
                      ? "border-indigo-500/30 bg-indigo-500/[0.02]"
                      : "border-zinc-800/50 bg-[#0c0c14]"
                  }`}
                >
                  {tier.highlight && (
                    <div className="absolute -top-3 left-6">
                      <span className="bg-indigo-500 text-white text-[10px] font-mono uppercase tracking-wider px-3 py-1 rounded-full">
                        {tier.badge}
                      </span>
                    </div>
                  )}

                  <div className="mb-6">
                    <h3 className="text-lg font-bold text-white">{tier.name}</h3>
                    <div className="mt-3">
                      <span className="text-3xl font-black text-white">{tier.price}</span>
                      {tier.period && <span className="text-zinc-600 text-sm ml-1">{tier.period}</span>}
                    </div>
                    <p className="text-xs text-zinc-600 mt-2">{tier.description}</p>
                  </div>

                  <ul className="space-y-2.5 flex-1">
                    {tier.features.map((f) => (
                      <li key={f} className="flex items-start gap-2 text-[13px] text-zinc-400">
                        <Check className="h-3.5 w-3.5 text-cyan-400/60 mt-0.5 shrink-0" />
                        {f}
                      </li>
                    ))}
                  </ul>

                  <div className="mt-8">
                    <Link href={tier.href} onClick={() => analytics.pricingClick(tier.name.toLowerCase())}>
                      <Button className={`w-full ${
                        tier.highlight
                          ? "bg-indigo-500 hover:bg-indigo-600 text-white"
                          : "bg-zinc-900 hover:bg-zinc-800 text-zinc-300 border border-zinc-800"
                      }`}>
                        {tier.cta}
                      </Button>
                    </Link>
                  </div>
                </motion.div>
              </FadeInSection>
            ))}
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════════
          VISION (FINALE)
      ═══════════════════════════════════════════════════════════════ */}
      <section className="relative py-40 border-t border-zinc-800/30 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-indigo-500/[0.01] to-transparent" />
        <GridBackground />

        <div className="relative z-10 mx-auto max-w-3xl px-6 text-center">
          <FadeInSection>
            <p className="text-sm text-zinc-600 mb-2 font-mono">We are not building a tool.</p>
            <p className="text-sm text-zinc-500 mb-8 font-mono">We are defining the missing layer in AI systems:</p>

            <motion.h2
              className="text-5xl sm:text-7xl font-black bg-gradient-to-r from-indigo-400 via-cyan-400 to-indigo-400 bg-clip-text text-transparent bg-[length:200%_auto] animate-gradient leading-tight"
              whileInView={{ scale: [0.95, 1] }}
              transition={{ duration: 0.6 }}
              viewport={{ once: true }}
            >
              The Constraint
              <br />
              Layer
            </motion.h2>
          </FadeInSection>

          <FadeInSection delay={0.3}>
            <div className="mt-14 space-y-3 max-w-sm mx-auto text-left">
              {[
                { left: "Operating systems", right: "control hardware" },
                { left: "Blockchains", right: "enforce trust" },
                { left: "Chimera", right: "enforces behavior", highlight: true },
              ].map((item) => (
                <div
                  key={item.left}
                  className={`flex items-center gap-3 text-sm ${
                    item.highlight ? "text-white" : "text-zinc-500"
                  }`}
                >
                  <span className={`text-xs ${item.highlight ? "text-cyan-400" : "text-zinc-700"}`}>{">"}</span>
                  <span className={item.highlight ? "font-bold" : ""}>{item.left}</span>
                  <span className={item.highlight ? "text-cyan-400" : "text-zinc-600"}>{item.right}</span>
                </div>
              ))}
            </div>
          </FadeInSection>

          <FadeInSection delay={0.5}>
            <div className="mt-16 flex flex-col sm:flex-row items-center justify-center gap-4">
              <div
                className="flex items-center gap-3 rounded-lg border border-zinc-800 bg-[#0c0c14] px-5 py-3 font-mono text-sm cursor-pointer hover:border-indigo-500/30 transition"
                onClick={() => navigator.clipboard?.writeText("pip install chimera-runtime")}
              >
                <span className="text-zinc-600">$</span>
                <span className="text-cyan-400">pip install chimera-runtime</span>
              </div>
              <Link href="/dashboard" onClick={() => analytics.ctaClick("bottom-cta")}>
                <Button className="bg-indigo-500 hover:bg-indigo-600 text-white px-6">
                  Open Dashboard <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </Link>
            </div>
          </FadeInSection>
        </div>
      </section>

      {/* ── FOOTER ── */}
      <footer className="border-t border-zinc-800/30 py-8">
        <div className="mx-auto max-w-7xl px-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Shield className="h-4 w-4 text-indigo-400/60" />
            <span className="text-xs font-mono text-zinc-600">CHIMERA_RUNTIME</span>
          </div>
          <p className="text-[11px] font-mono text-zinc-800">
            LLMs generate. Chimera governs.
          </p>
        </div>
      </footer>
    </div>
  );
}
