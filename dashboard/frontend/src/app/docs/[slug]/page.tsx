"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { ArrowLeft, BookOpen, Loader2 } from "lucide-react";
import type { DocDetail } from "@/lib/types";

export default function DocDetailPage() {
  const params = useParams();
  const slug = params.slug as string;
  const [doc, setDoc] = useState<DocDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!slug) return;
    api.getDoc(slug)
      .then((data) => {
        setDoc(data);
        setLoading(false);
      })
      .catch((err) => {
        setError("Document not found");
        setLoading(false);
      });
  }, [slug]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-32">
        <Loader2 className="h-8 w-8 text-[#6366f1] animate-spin" />
      </div>
    );
  }

  if (error || !doc) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-12 text-center">
        <p className="text-[#ef4444] mb-4">{error}</p>
        <Link href="/docs" className="text-[#6366f1] hover:text-[#818cf8] text-sm">
          Back to Docs
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl px-6 py-12">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm mb-8">
        <Link href="/docs" className="text-[#6366f1] hover:text-[#818cf8] flex items-center gap-1.5 transition">
          <ArrowLeft className="h-3.5 w-3.5" />
          Docs
        </Link>
        <span className="text-[#52525b]">/</span>
        <span className="text-[#71717a]">{doc.category}</span>
      </div>

      {/* Article */}
      <article className="prose-chimera">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            h1: ({ children }) => (
              <h1 className="text-3xl font-bold text-white mb-4">{children}</h1>
            ),
            h2: ({ children }) => (
              <h2 className="text-xl font-semibold text-white mt-10 mb-4 pb-2 border-b border-[#1e1e2e]">
                {children}
              </h2>
            ),
            h3: ({ children }) => (
              <h3 className="text-lg font-medium text-white mt-8 mb-3">{children}</h3>
            ),
            h4: ({ children }) => (
              <h4 className="text-base font-medium text-[#e4e4e7] mt-6 mb-2">{children}</h4>
            ),
            p: ({ children }) => (
              <p className="text-sm text-[#a1a1aa] leading-relaxed mb-4">{children}</p>
            ),
            a: ({ href, children }) => (
              <a href={href} className="text-[#6366f1] hover:text-[#818cf8] underline transition" target={href?.startsWith("http") ? "_blank" : undefined}>
                {children}
              </a>
            ),
            code: ({ className, children }) => {
              const isBlock = className?.includes("language-");
              if (isBlock) {
                return (
                  <code className="block bg-[#0d0d14] border border-[#1e1e2e] rounded-lg p-4 font-mono text-xs text-[#e4e4e7] overflow-x-auto my-4">
                    {children}
                  </code>
                );
              }
              return (
                <code className="bg-[#1e1e2e] text-[#818cf8] rounded px-1.5 py-0.5 font-mono text-xs">
                  {children}
                </code>
              );
            },
            pre: ({ children }) => (
              <pre className="bg-[#0d0d14] border border-[#1e1e2e] rounded-lg p-4 overflow-x-auto my-4 text-sm">
                {children}
              </pre>
            ),
            ul: ({ children }) => (
              <ul className="list-disc list-inside text-sm text-[#a1a1aa] space-y-1.5 mb-4 ml-2">
                {children}
              </ul>
            ),
            ol: ({ children }) => (
              <ol className="list-decimal list-inside text-sm text-[#a1a1aa] space-y-1.5 mb-4 ml-2">
                {children}
              </ol>
            ),
            li: ({ children }) => (
              <li className="text-sm text-[#a1a1aa] leading-relaxed">{children}</li>
            ),
            blockquote: ({ children }) => (
              <blockquote className="border-l-2 border-[#6366f1] pl-4 my-4 text-sm text-[#71717a] italic">
                {children}
              </blockquote>
            ),
            table: ({ children }) => (
              <div className="overflow-x-auto my-4">
                <table className="w-full text-sm border-collapse border border-[#1e1e2e]">
                  {children}
                </table>
              </div>
            ),
            thead: ({ children }) => (
              <thead className="bg-[#111119]">{children}</thead>
            ),
            th: ({ children }) => (
              <th className="border border-[#1e1e2e] px-3 py-2 text-left text-xs font-medium text-[#a1a1aa]">
                {children}
              </th>
            ),
            td: ({ children }) => (
              <td className="border border-[#1e1e2e] px-3 py-2 text-xs text-[#e4e4e7]">
                {children}
              </td>
            ),
            hr: () => <hr className="border-[#1e1e2e] my-8" />,
            strong: ({ children }) => (
              <strong className="text-white font-semibold">{children}</strong>
            ),
            em: ({ children }) => (
              <em className="text-[#a1a1aa] italic">{children}</em>
            ),
          }}
        >
          {doc.content}
        </ReactMarkdown>
      </article>

      {/* Back Link */}
      <div className="mt-12 pt-6 border-t border-[#1e1e2e]">
        <Link href="/docs" className="text-[#6366f1] hover:text-[#818cf8] text-sm flex items-center gap-1.5 transition">
          <ArrowLeft className="h-3.5 w-3.5" /> Back to all docs
        </Link>
      </div>
    </div>
  );
}
