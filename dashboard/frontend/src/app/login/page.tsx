"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth";
import { analytics } from "@/lib/analytics";
import { Shield, Mail, Lock, ArrowRight, Loader2 } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      await login(email, password);
      analytics.loginComplete();
      router.push("/dashboard");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center relative overflow-hidden">
      {/* Background gradient orbs */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-[#6366f1]/10 rounded-full blur-[128px]" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-[#818cf8]/5 rounded-full blur-[128px]" />

      <div className="w-full max-w-md mx-4 relative z-10">
        {/* Logo */}
        <div className="text-center mb-8">
          <Link href="/" className="inline-flex items-center gap-2">
            <Shield className="w-8 h-8 text-[#6366f1]" />
            <span className="text-2xl font-bold text-white">Chimera.</span>
          </Link>
          <p className="text-[#71717a] mt-2">Sign in to your dashboard</p>
        </div>

        {/* Login Card */}
        <div className="bg-[#111119] border border-[#1e1e2e] rounded-2xl p-8">
          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <div className="bg-[#ef4444]/10 border border-[#ef4444]/20 rounded-lg p-3 text-[#ef4444] text-sm">
                {error}
              </div>
            )}

            <div>
              <label className="block text-sm text-[#a1a1aa] mb-2">Email</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#71717a]" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@company.com"
                  required
                  className="w-full bg-[#0a0a0f] border border-[#1e1e2e] rounded-lg pl-10 pr-4 py-3 text-white placeholder:text-[#52525b] focus:border-[#6366f1] focus:ring-1 focus:ring-[#6366f1] outline-none transition"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm text-[#a1a1aa] mb-2">Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#71717a]" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  minLength={6}
                  className="w-full bg-[#0a0a0f] border border-[#1e1e2e] rounded-lg pl-10 pr-4 py-3 text-white placeholder:text-[#52525b] focus:border-[#6366f1] focus:ring-1 focus:ring-[#6366f1] outline-none transition"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-[#6366f1] hover:bg-[#5558e6] text-white font-medium py-3 rounded-lg transition flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {loading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <>
                  Sign In <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-[#71717a] text-sm">
              Don&apos;t have an account?{" "}
              <Link href="/register" className="text-[#6366f1] hover:text-[#818cf8] transition">
                Create one
              </Link>
            </p>
          </div>
        </div>

        {/* Footer */}
        <p className="text-center text-[#52525b] text-xs mt-6">
          chimera-runtime v3.0.0 — Deterministic Runtime for AI Agents
        </p>
      </div>
    </div>
  );
}
