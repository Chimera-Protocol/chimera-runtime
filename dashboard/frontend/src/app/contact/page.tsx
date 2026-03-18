"use client";

import { useState, useEffect, Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { analytics } from "@/lib/analytics";
import {
  Shield,
  Mail,
  ArrowLeft,
  Building2,
  Send,
  Loader2,
  CheckCircle2,
  AlertTriangle,
  Wrench,
} from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

const planInfo: Record<string, { title: string; badge: string; color: string }> = {
  pro: {
    title: "Pro Plan",
    badge: "PRO",
    color: "#6366f1",
  },
  enterprise: {
    title: "Enterprise Plan",
    badge: "ENTERPRISE",
    color: "#f59e0b",
  },
};

export default function ContactPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-[#6366f1]" />
      </div>
    }>
      <ContactPageInner />
    </Suspense>
  );
}

function ContactPageInner() {
  const { user } = useAuth();
  const searchParams = useSearchParams();
  const plan = searchParams.get("plan") || "";

  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [company, setCompany] = useState("");
  const [message, setMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState("");

  // Pre-fill email if logged in
  useEffect(() => {
    if (user?.email) {
      setEmail(user.email);
    }
  }, [user]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) return;

    setSubmitting(true);
    setError("");

    try {
      const res = await fetch(`${API_BASE}/leads`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: email.trim(),
          name: name.trim(),
          company: company.trim(),
          plan,
          message: message.trim(),
          user_email: user?.email || "",
        }),
      });

      if (!res.ok) throw new Error("Failed to submit");
      setSubmitted(true);
      analytics.contactSubmit();
    } catch {
      setError("Failed to submit. Please try again or email us directly.");
    } finally {
      setSubmitting(false);
    }
  };

  const info = planInfo[plan];

  return (
    <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center relative overflow-hidden">
      <div className="absolute top-1/3 left-1/4 w-96 h-96 bg-[#f59e0b]/5 rounded-full blur-[128px]" />
      <div className="absolute bottom-1/4 right-1/3 w-96 h-96 bg-[#6366f1]/5 rounded-full blur-[128px]" />

      <div className="w-full max-w-lg mx-4 relative z-10">
        <Link href="/" className="inline-flex items-center gap-2 text-[#71717a] hover:text-white transition mb-8">
          <ArrowLeft className="h-4 w-4" /> Back to home
        </Link>

        {/* Under Development Banner */}
        <div className="mb-4 flex items-start gap-3 rounded-xl border border-[#f59e0b]/20 bg-[#f59e0b]/5 p-4">
          <Wrench className="h-5 w-5 text-[#f59e0b] mt-0.5 shrink-0" />
          <div>
            <p className="text-sm font-medium text-[#f59e0b]">Under Active Development</p>
            <p className="text-xs text-[#f59e0b]/70 mt-1">
              Chimera Runtime is currently in active development. Leave your details and our team will reach out when your plan is ready.
            </p>
          </div>
        </div>

        <div className="bg-[#111119] border border-[#1e1e2e] rounded-2xl p-8">
          {submitted ? (
            /* Success State */
            <div className="text-center py-8">
              <CheckCircle2 className="h-12 w-12 text-[#22c55e] mx-auto mb-4" />
              <h2 className="text-xl font-bold text-white mb-2">Thank you!</h2>
              <p className="text-sm text-[#71717a] mb-6">
                Our team will reach out to <span className="text-white">{email}</span> shortly.
              </p>
              <Link href="/">
                <button className="bg-[#6366f1] hover:bg-[#5558e6] text-white text-sm font-medium px-6 py-2.5 rounded-lg transition">
                  Back to Home
                </button>
              </Link>
            </div>
          ) : (
            <>
              {/* Header */}
              <div className="flex items-center gap-3 mb-6">
                <div className="h-12 w-12 rounded-xl bg-[#6366f1]/10 flex items-center justify-center">
                  <Building2 className="h-6 w-6 text-[#6366f1]" />
                </div>
                <div>
                  <h1 className="text-xl font-bold text-white">
                    {info ? `Get ${info.title}` : "Contact Sales"}
                  </h1>
                  <p className="text-sm text-[#71717a]">
                    Leave your details and we&apos;ll be in touch
                  </p>
                </div>
                {info && (
                  <span
                    className="ml-auto text-[10px] font-medium rounded px-2 py-1 border"
                    style={{
                      color: info.color,
                      borderColor: `${info.color}40`,
                      backgroundColor: `${info.color}10`,
                    }}
                  >
                    {info.badge}
                  </span>
                )}
              </div>

              {/* Logged-in user info */}
              {user && (
                <div className="mb-5 flex items-center gap-2 rounded-lg border border-[#1e1e2e] bg-[#0a0a0f] px-3 py-2">
                  <Shield className="h-3.5 w-3.5 text-[#6366f1]" />
                  <span className="text-xs text-[#71717a]">Logged in as</span>
                  <span className="text-xs text-white">{user.email}</span>
                  <span className="ml-auto rounded bg-[#6366f1]/10 px-1.5 py-0.5 text-[9px] font-medium text-[#818cf8] uppercase">
                    {user.tier}
                  </span>
                </div>
              )}

              {/* Form */}
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm text-[#a1a1aa] mb-1.5">Email *</label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    placeholder="you@company.com"
                    className="w-full bg-[#0a0a0f] border border-[#1e1e2e] rounded-lg px-4 py-2.5 text-white placeholder:text-[#52525b] focus:border-[#6366f1] focus:ring-1 focus:ring-[#6366f1] outline-none text-sm"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-sm text-[#a1a1aa] mb-1.5">Name</label>
                    <input
                      type="text"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      placeholder="John Doe"
                      className="w-full bg-[#0a0a0f] border border-[#1e1e2e] rounded-lg px-4 py-2.5 text-white placeholder:text-[#52525b] focus:border-[#6366f1] focus:ring-1 focus:ring-[#6366f1] outline-none text-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-[#a1a1aa] mb-1.5">Company</label>
                    <input
                      type="text"
                      value={company}
                      onChange={(e) => setCompany(e.target.value)}
                      placeholder="Acme Corp"
                      className="w-full bg-[#0a0a0f] border border-[#1e1e2e] rounded-lg px-4 py-2.5 text-white placeholder:text-[#52525b] focus:border-[#6366f1] focus:ring-1 focus:ring-[#6366f1] outline-none text-sm"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm text-[#a1a1aa] mb-1.5">Message</label>
                  <textarea
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    placeholder="Tell us about your use case..."
                    rows={3}
                    className="w-full bg-[#0a0a0f] border border-[#1e1e2e] rounded-lg px-4 py-2.5 text-white placeholder:text-[#52525b] focus:border-[#6366f1] focus:ring-1 focus:ring-[#6366f1] outline-none text-sm resize-y"
                  />
                </div>

                {error && (
                  <div className="flex items-center gap-2 rounded-lg border border-[#ef4444]/20 bg-[#ef4444]/5 px-3 py-2">
                    <AlertTriangle className="h-3.5 w-3.5 text-[#ef4444]" />
                    <span className="text-xs text-[#ef4444]">{error}</span>
                  </div>
                )}

                <button
                  type="submit"
                  disabled={submitting || !email.trim()}
                  className="w-full bg-[#6366f1] hover:bg-[#5558e6] text-white font-medium py-3 rounded-lg transition flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  {submitting ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <>
                      <Send className="h-4 w-4" />
                      Submit Inquiry
                    </>
                  )}
                </button>
              </form>

              {/* Direct Contact */}
              <div className="mt-6 pt-6 border-t border-[#1e1e2e]">
                <p className="text-xs text-[#71717a] text-center mb-3">Or reach us directly</p>
                <a
                  href="mailto:research@chimera-protocol.com"
                  className="flex items-center justify-center gap-2 rounded-lg border border-[#1e1e2e] bg-[#0a0a0f] px-4 py-3 hover:border-[#6366f1]/30 transition"
                >
                  <Mail className="h-4 w-4 text-[#6366f1]" />
                  <span className="text-sm text-white">research@chimera-protocol.com</span>
                </a>
              </div>
            </>
          )}
        </div>

        {/* Footer note */}
        <p className="text-center text-[10px] text-[#52525b] mt-6">
          chimera-runtime v3.0.0 — Under active development
        </p>
      </div>
    </div>
  );
}
