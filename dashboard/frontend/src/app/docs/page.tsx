"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import {
  BookOpen,
  Layers,
  Terminal,
  Code2,
  Puzzle,
  Scale,
  Rocket,
  FileText,
} from "lucide-react";
import type { DocSummary } from "@/lib/types";

const categoryIcons: Record<string, React.ElementType> = {
  Overview: BookOpen,
  "Getting Started": Rocket,
  Architecture: Layers,
  Policy: FileText,
  CLI: Terminal,
  API: Code2,
  Integrations: Puzzle,
  "EU AI Act": Scale,
};

// Docs that cover Pro or Enterprise features
const docTierBadge: Record<string, "pro" | "enterprise"> = {
  "api-reference": "pro",
  "annex_iv_technical_documentation": "enterprise",
};

const categoryColors: Record<string, string> = {
  Overview: "#6366f1",
  "Getting Started": "#22c55e",
  Architecture: "#818cf8",
  Policy: "#f59e0b",
  CLI: "#ef4444",
  API: "#06b6d4",
  Integrations: "#a855f7",
  "EU AI Act": "#f43f5e",
};

export default function DocsPage() {
  const [docs, setDocs] = useState<DocSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState<string>("all");

  useEffect(() => {
    api.getDocs().then((res) => {
      setDocs(res.docs);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  const categories = ["all", ...Array.from(new Set(docs.map((d) => d.category)))];
  const filtered = selectedCategory === "all" ? docs : docs.filter((d) => d.category === selectedCategory);

  return (
    <div className="mx-auto max-w-6xl px-6 py-12">
      {/* Header */}
      <div className="mb-10">
        <h1 className="text-3xl font-bold text-white mb-2">Documentation</h1>
        <p className="text-[#71717a] max-w-2xl">
          Everything you need to integrate chimera-compliance into your AI agents.
          From quickstart guides to full API reference.
        </p>
      </div>

      {/* Category Filters */}
      <div className="flex flex-wrap gap-2 mb-8">
        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() => setSelectedCategory(cat)}
            className={`rounded-lg px-3 py-1.5 text-sm transition ${
              selectedCategory === cat
                ? "bg-[#6366f1]/10 text-[#818cf8] border border-[#6366f1]/30"
                : "text-[#71717a] border border-[#1e1e2e] hover:border-[#2e2e3e]"
            }`}
          >
            {cat === "all" ? "All" : cat}
          </button>
        ))}
      </div>

      {/* Docs Grid */}
      {loading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-40 animate-pulse rounded-xl bg-[#1e1e2e]" />
          ))}
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filtered.map((doc) => {
            const Icon = categoryIcons[doc.category] || FileText;
            const color = categoryColors[doc.category] || "#6366f1";
            const tierBadge = docTierBadge[doc.slug];

            return (
              <Link key={doc.slug} href={`/docs/${doc.slug}`}>
                <div className="group rounded-xl border border-[#1e1e2e] bg-[#111119] p-6 transition hover:border-[#2e2e3e] hover:bg-[#111119]/80 h-full">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <div
                        className="h-9 w-9 rounded-lg flex items-center justify-center"
                        style={{ backgroundColor: `${color}15` }}
                      >
                        <Icon className="h-5 w-5" style={{ color }} />
                      </div>
                      {tierBadge && (
                        <span
                          className={`text-[9px] font-semibold rounded px-1.5 py-0.5 border ${
                            tierBadge === "enterprise"
                              ? "border-[#f59e0b]/30 text-[#f59e0b] bg-[#f59e0b]/10"
                              : "border-[#6366f1]/30 text-[#818cf8] bg-[#6366f1]/10"
                          }`}
                        >
                          {tierBadge === "enterprise" ? "ENT" : "PRO"}
                        </span>
                      )}
                    </div>
                    <span
                      className="text-[10px] rounded-full px-2 py-0.5 border"
                      style={{
                        color,
                        borderColor: `${color}30`,
                        backgroundColor: `${color}08`,
                      }}
                    >
                      {doc.category}
                    </span>
                  </div>
                  <h3 className="text-sm font-medium text-white mb-2 group-hover:text-[#818cf8] transition">
                    {doc.title}
                  </h3>
                  <p className="text-xs text-[#71717a] line-clamp-3 leading-relaxed">
                    {doc.excerpt}
                  </p>
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
