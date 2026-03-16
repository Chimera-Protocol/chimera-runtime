"use client";

import Link from "next/link";
import { Shield } from "lucide-react";
import { AuthNav } from "@/components/layout/AuthNav";

export default function DocsLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-[#0a0a0f]">
      {/* Minimal Nav */}
      <nav className="fixed top-0 left-0 right-0 z-50 border-b border-[#1e1e2e] bg-[#0a0a0f]/90 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
          <Link href="/" className="flex items-center gap-2">
            <Shield className="h-6 w-6 text-[#6366f1]" />
            <span className="text-lg font-bold text-white">Chimera.</span>
            <span className="text-[#71717a] text-sm ml-2">/ Docs</span>
          </Link>
          <div className="flex items-center gap-4">
            <Link href="/demo" className="text-sm text-[#71717a] hover:text-white transition">
              Demo
            </Link>
            <AuthNav />
          </div>
        </div>
      </nav>
      <div className="pt-16">{children}</div>
    </div>
  );
}
