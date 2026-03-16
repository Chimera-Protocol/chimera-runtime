"use client";

import { useAuth } from "@/lib/auth";
import Link from "next/link";
import { Shield, User, LogOut } from "lucide-react";

/**
 * Auth-aware navigation for public pages (landing, docs, demo, contact).
 * Shows user email + Dashboard link when logged in, Sign In/Get Started when not.
 */
export function AuthNav({
  variant = "full",
}: {
  variant?: "full" | "minimal";
}) {
  const { user, logout, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex items-center gap-3">
        <div className="h-8 w-20 animate-pulse rounded bg-[#1e1e2e]" />
      </div>
    );
  }

  if (user) {
    return (
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 rounded-lg border border-[#1e1e2e] bg-[#111119] px-3 py-1.5">
          <User className="h-3.5 w-3.5 text-[#6366f1]" />
          <span className="text-xs text-[#a1a1aa]">{user.email}</span>
          <span className="rounded bg-[#6366f1]/10 px-1.5 py-0.5 text-[9px] font-medium text-[#818cf8] uppercase">
            {user.tier}
          </span>
        </div>
        <Link href="/dashboard">
          <button className="bg-[#6366f1] hover:bg-[#5558e6] text-white text-sm font-medium px-4 py-2 rounded-lg transition">
            Dashboard
          </button>
        </Link>
        <button
          onClick={logout}
          className="text-[#71717a] hover:text-white transition p-2"
          title="Sign Out"
        >
          <LogOut className="h-4 w-4" />
        </button>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-3">
      <Link href="/login">
        <button className="text-[#71717a] hover:text-white text-sm font-medium px-3 py-2 transition">
          Sign In
        </button>
      </Link>
      <Link href="/register">
        <button className="bg-[#6366f1] hover:bg-[#5558e6] text-white text-sm font-medium px-4 py-2 rounded-lg transition">
          Get Started
        </button>
      </Link>
    </div>
  );
}
