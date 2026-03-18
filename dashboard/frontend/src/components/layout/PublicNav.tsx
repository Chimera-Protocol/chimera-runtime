"use client";

import Link from "next/link";
import { Shield, ArrowLeft } from "lucide-react";
import { AuthNav } from "./AuthNav";

interface PublicNavProps {
  backLabel?: string;
  backHref?: string;
  showFull?: boolean;
}

export function PublicNav({ backLabel, backHref = "/", showFull = false }: PublicNavProps) {
  return (
    <nav className="fixed top-0 z-50 w-full border-b border-zinc-800/50 bg-[#06060b]/80 backdrop-blur-xl">
      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-6">
        <Link href="/" className="flex items-center gap-3 group">
          <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-indigo-500/20 to-cyan-500/10 border border-indigo-500/30 flex items-center justify-center group-hover:border-indigo-400/50 group-hover:from-indigo-500/30 transition-all duration-300 shadow-lg shadow-indigo-500/5">
            <Shield className="h-4 w-4 text-indigo-400 group-hover:text-indigo-300 transition-colors" />
          </div>
          <div className="flex items-baseline gap-0">
            <span className="text-sm font-black tracking-tight text-white">Chimera</span>
            <span className="text-sm font-black tracking-tight bg-gradient-to-r from-indigo-400 to-cyan-400 bg-clip-text text-transparent">Runtime</span>
          </div>
        </Link>

        {showFull ? (
          <>
            <div className="hidden items-center gap-6 lg:flex">
              {[
                { href: "#problem", label: "Problem" },
                { href: "#how", label: "How" },
                { href: "/demo", label: "Demo", external: true },
                { href: "#code", label: "Code" },
                { href: "#pricing", label: "Pricing" },
                { href: "/docs", label: "Docs", external: true },
                { href: "/investors", label: "Investors", external: true },
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
              <a href="https://chimera-protocol.com" target="_blank" rel="noopener noreferrer" className="text-xs font-mono text-green-400/70 hover:text-green-400 transition uppercase tracking-wider">
                Fellowship
              </a>
            </div>
            <AuthNav />
          </>
        ) : (
          <div className="flex items-center gap-4">
            {backLabel && (
              <Link
                href={backHref}
                className="flex items-center gap-2 text-xs font-mono text-zinc-600 hover:text-white transition"
              >
                <ArrowLeft className="h-3.5 w-3.5" /> {backLabel}
              </Link>
            )}
            <AuthNav />
          </div>
        )}
      </div>
    </nav>
  );
}
