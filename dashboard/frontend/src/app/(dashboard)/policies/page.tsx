"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  FileText,
  Shield,
  CheckCircle2,
  XCircle,
  Loader2,
  Variable,
  Lock,
  Plus,
  Save,
  Zap,
  Clock,
  Play,
  FlaskConical,
  AlertTriangle,
  Info,
  Sparkles,
} from "lucide-react";
import { ProGate } from "@/components/pro-gate";
import { PolicyMarketplace } from "@/components/policies/PolicyMarketplace";
import type { PolicySummary, PolicyDetail, VerificationResult } from "@/lib/types";

// ── CSL/YAML Templates ────────────────────────────────────────────

const CSL_TEMPLATE = `CONFIG {
  ENFORCEMENT_MODE: BLOCK
  CHECK_LOGICAL_CONSISTENCY: TRUE
}

DOMAIN MyDomain {
  VARIABLES {
    amount: 0..1000000
    role: {"ADMIN", "USER", "MANAGER"}
    action: {"READ", "WRITE", "DELETE", "TRANSFER"}
  }

  STATE_CONSTRAINT example_rule {
    WHEN role == "USER" AND amount > 10000
    THEN action MUST NOT BE "TRANSFER"
  }
}
`;

const YAML_TEMPLATE = `domain: MyDomain

variables:
  amount: "0..1000000"
  role: "{ADMIN, USER, MANAGER}"
  action: "{READ, WRITE, DELETE, TRANSFER}"

rules:
  - name: example_rule
    when: "role == 'USER' and amount > 10000"
    then: BLOCK
    message: "Users cannot transfer amounts over 10,000"
`;

export default function PoliciesPage() {
  const [policies, setPolicies] = useState<PolicySummary[]>([]);
  const [selected, setSelected] = useState<PolicyDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [verifying, setVerifying] = useState<string | null>(null);
  const [verifyResult, setVerifyResult] = useState<VerificationResult | null>(null);

  // Editor state
  const [editorFormat, setEditorFormat] = useState<"csl" | "yaml">("csl");
  const [editorFilename, setEditorFilename] = useState("");
  const [editorContent, setEditorContent] = useState(CSL_TEMPLATE);
  const [saving, setSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  // Simulation state
  const [simPolicy, setSimPolicy] = useState<string>("");
  const [simDetail, setSimDetail] = useState<PolicyDetail | null>(null);
  const [simParams, setSimParams] = useState<Record<string, string>>({});
  const [simulating, setSimulating] = useState(false);
  const [simResult, setSimResult] = useState<{
    result: string;
    duration_ms: number;
    violations: Array<{ constraint: string; explanation: string }>;
  } | null>(null);

  useEffect(() => {
    fetchPolicies();
  }, []);

  const fetchPolicies = async () => {
    try {
      const data = await api.getPolicies();
      setPolicies(data.policies);
      if (data.policies.length > 0 && !selected) {
        const detail = await api.getPolicy(data.policies[0].filename);
        setSelected(detail);
      }
    } catch (err) {
      console.error("Failed to fetch policies:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleSelect = async (filename: string) => {
    try {
      const detail = await api.getPolicy(filename);
      setSelected(detail);
      setVerifyResult(null);
    } catch (err) {
      console.error("Failed to fetch policy:", err);
    }
  };

  const handleVerify = async (filename: string) => {
    setVerifying(filename);
    try {
      const result = await api.verifyPolicy(filename);
      setVerifyResult(result);
    } catch (err) {
      setVerifyResult({
        filename,
        verified: false,
        messages: ["Verification request failed"],
        backend: "unknown",
        verification_engine: "unknown",
        verification_time_ms: 0,
        constraint_results: [],
        csl_core_available: false,
      });
    } finally {
      setVerifying(null);
    }
  };

  const handleFormatChange = (format: "csl" | "yaml") => {
    setEditorFormat(format);
    setEditorContent(format === "csl" ? CSL_TEMPLATE : YAML_TEMPLATE);
    setEditorFilename("");
    setSaveMessage(null);
  };

  const handleSave = async () => {
    const ext = editorFormat === "csl" ? ".csl" : ".yaml";
    const filename = editorFilename.endsWith(ext)
      ? editorFilename
      : editorFilename + ext;

    if (!editorFilename.trim()) {
      setSaveMessage({ type: "error", text: "Please enter a filename" });
      return;
    }

    setSaving(true);
    setSaveMessage(null);
    try {
      const result = await api.createPolicy(filename, editorContent);
      setSaveMessage({ type: "success", text: result.message });
      await fetchPolicies();
      setEditorFilename("");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to save policy";
      setSaveMessage({ type: "error", text: msg });
    } finally {
      setSaving(false);
    }
  };

  const handleSimPolicyChange = async (filename: string) => {
    setSimPolicy(filename);
    setSimResult(null);
    setSimParams({});
    if (!filename) { setSimDetail(null); return; }
    try {
      const detail = await api.getPolicy(filename);
      setSimDetail(detail);
      // Initialize params with defaults
      const defaults: Record<string, string> = {};
      for (const varName of detail.variable_names) {
        const domain = detail.variable_domains[varName] || "";
        if (domain.includes("..")) {
          // Range like 0..1000000 — default to min
          defaults[varName] = domain.split("..")[0];
        } else if (domain.startsWith("{") && domain.endsWith("}")) {
          // Enum like {"ADMIN", "USER"} — default to first
          const vals = domain.slice(1, -1).split(",").map(s => s.trim().replace(/"/g, ""));
          defaults[varName] = vals[0] || "";
        } else {
          defaults[varName] = "";
        }
      }
      setSimParams(defaults);
    } catch {
      setSimDetail(null);
    }
  };

  const handleSimulate = async () => {
    if (!simPolicy) return;
    setSimulating(true);
    setSimResult(null);
    try {
      // Convert string params to appropriate types
      const typedParams: Record<string, unknown> = {};
      for (const [key, val] of Object.entries(simParams)) {
        const domain = simDetail?.variable_domains[key] || "";
        if (domain.includes("..")) {
          typedParams[key] = Number(val) || 0;
        } else {
          typedParams[key] = val;
        }
      }
      const result = await api.simulatePolicy(simPolicy, typedParams);
      setSimResult(result);
    } catch (err) {
      setSimResult({
        result: "ERROR",
        duration_ms: 0,
        violations: [{ constraint: "system", explanation: err instanceof Error ? err.message : "Simulation failed" }],
      });
    } finally {
      setSimulating(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-48 animate-pulse rounded bg-[#1e1e2e]" />
        <div className="grid gap-6 lg:grid-cols-3">
          <div className="h-64 animate-pulse rounded bg-[#1e1e2e]" />
          <div className="lg:col-span-2 h-64 animate-pulse rounded bg-[#1e1e2e]" />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Policies</h1>
          <p className="mt-1 text-sm text-[#71717a]">
            Manage, verify, and create compliance policies
          </p>
        </div>
        <Link href="/learn-csl">
          <motion.div
            className="relative inline-flex items-center gap-2 px-5 py-2.5 rounded-xl
                       bg-gradient-to-r from-indigo-500/10 to-purple-500/10
                       border border-indigo-500/30 text-indigo-300 text-sm font-medium
                       hover:border-indigo-400/50 transition-colors cursor-pointer"
            animate={{
              boxShadow: [
                "0 0 20px rgba(99,102,241,0.15)",
                "0 0 40px rgba(99,102,241,0.3)",
                "0 0 20px rgba(99,102,241,0.15)",
              ],
            }}
            transition={{ duration: 2, repeat: Infinity }}
          >
            <Sparkles className="h-4 w-4 text-indigo-400" />
            How to Write Policies in CSL
            <motion.span
              className="absolute -top-1 -right-1 h-2 w-2 rounded-full bg-indigo-400"
              animate={{ scale: [1, 1.5, 1], opacity: [1, 0.5, 1] }}
              transition={{ duration: 1.5, repeat: Infinity }}
            />
          </motion.div>
        </Link>
      </div>

      <Tabs defaultValue="manage" className="w-full">
        <TabsList className="bg-[#111119] border border-[#1e1e2e]">
          <TabsTrigger value="manage" className="data-[state=active]:bg-[#6366f1]/10 data-[state=active]:text-[#818cf8]">
            <FileText className="mr-2 h-4 w-4" />
            Policies
          </TabsTrigger>
          <TabsTrigger value="create" className="data-[state=active]:bg-[#6366f1]/10 data-[state=active]:text-[#818cf8]">
            <Plus className="mr-2 h-4 w-4" />
            Create Policy
          </TabsTrigger>
          <TabsTrigger value="simulate" className="data-[state=active]:bg-[#6366f1]/10 data-[state=active]:text-[#818cf8]">
            <FlaskConical className="mr-2 h-4 w-4" />
            Simulate
          </TabsTrigger>
          <TabsTrigger value="marketplace" className="data-[state=active]:bg-[#6366f1]/10 data-[state=active]:text-[#818cf8]">
            <Sparkles className="mr-2 h-4 w-4" />
            Marketplace
          </TabsTrigger>
        </TabsList>

        {/* ══════════════ TAB 1: Manage ══════════════ */}
        <TabsContent value="manage" className="mt-6">
          <div className="grid gap-6 lg:grid-cols-3">
            {/* Policy List */}
            <div className="space-y-3">
              {policies.map((p) => (
                <Card
                  key={p.filename}
                  className={`cursor-pointer border-[#1e1e2e] bg-[#111119] transition-colors hover:border-[#2e2e3e] ${
                    selected?.filename === p.filename ? "border-[#6366f1]/50 ring-1 ring-[#6366f1]/20" : ""
                  }`}
                  onClick={() => handleSelect(p.filename)}
                >
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="text-sm font-medium text-white">{p.filename}</p>
                        <p className="mt-0.5 text-xs text-[#71717a]">{p.domain_name}</p>
                      </div>
                      <Badge
                        variant="outline"
                        className={
                          p.backend === "csl-core"
                            ? "border-[#6366f1]/30 text-[#818cf8] text-[10px]"
                            : "border-[#f59e0b]/30 text-[#f59e0b] text-[10px]"
                        }
                      >
                        {p.backend === "csl-core" ? "CSL+Z3" : "YAML"}
                      </Badge>
                    </div>
                    <div className="mt-2 flex items-center gap-3 text-xs text-[#71717a]">
                      <span>{p.constraint_count} constraints</span>
                      {p.loaded ? (
                        <CheckCircle2 className="h-3 w-3 text-[#22c55e]" />
                      ) : (
                        <XCircle className="h-3 w-3 text-[#ef4444]" />
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            {/* Policy Detail */}
            <div className="lg:col-span-2 space-y-4">
              {selected ? (
                <Card className="border-[#1e1e2e] bg-[#111119]">
                  <CardHeader className="flex flex-row items-center justify-between">
                    <div>
                      <CardTitle className="text-white flex items-center gap-2">
                        <FileText className="h-5 w-5 text-[#6366f1]" />
                        {selected.domain_name}
                      </CardTitle>
                      <p className="mt-1 text-xs text-[#71717a] font-mono">{selected.filename}</p>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      className="border-[#6366f1]/30 text-[#818cf8] hover:bg-[#6366f1]/10"
                      onClick={() => handleVerify(selected.filename)}
                      disabled={verifying === selected.filename}
                    >
                      {verifying === selected.filename ? (
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      ) : (
                        <Shield className="mr-2 h-4 w-4" />
                      )}
                      Verify
                    </Button>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {/* Info Grid */}
                    <div className="grid grid-cols-2 gap-4">
                      <div className="rounded-lg border border-[#1e1e2e] bg-[#0a0a0f] p-3">
                        <p className="text-xs text-[#71717a]">Backend</p>
                        <p className="text-sm font-medium text-white">{selected.backend}</p>
                      </div>
                      <div className="rounded-lg border border-[#1e1e2e] bg-[#0a0a0f] p-3">
                        <p className="text-xs text-[#71717a]">Constraints</p>
                        <p className="text-sm font-medium text-white">{selected.constraint_count}</p>
                      </div>
                    </div>

                    {/* ── Rich Verification Result (Feature 1) ── */}
                    {verifyResult && verifyResult.filename === selected.filename && (
                      <div
                        className={`rounded-lg border p-4 ${
                          verifyResult.verified
                            ? "border-[#22c55e]/30 bg-[#22c55e]/5"
                            : "border-[#ef4444]/30 bg-[#ef4444]/5"
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            {verifyResult.verified ? (
                              <CheckCircle2 className="h-5 w-5 text-[#22c55e]" />
                            ) : (
                              <XCircle className="h-5 w-5 text-[#ef4444]" />
                            )}
                            <span
                              className={`text-sm font-medium ${
                                verifyResult.verified ? "text-[#22c55e]" : "text-[#ef4444]"
                              }`}
                            >
                              {verifyResult.verified ? "Verification Passed" : "Verification Failed"}
                            </span>
                          </div>
                          <div className="flex items-center gap-3">
                            <Badge variant="outline" className="border-[#6366f1]/30 text-[#818cf8] text-[10px]">
                              <Zap className="mr-1 h-3 w-3" />
                              {verifyResult.verification_engine === "z3" ? "Z3 Formal" : "Syntax Check"}
                            </Badge>
                            <span className="flex items-center gap-1 text-xs text-[#71717a]">
                              <Clock className="h-3 w-3" />
                              {verifyResult.verification_time_ms}ms
                            </span>
                          </div>
                        </div>

                        {/* Per-constraint results */}
                        {verifyResult.constraint_results.length > 0 && (
                          <div className="mt-3 space-y-1.5">
                            {verifyResult.constraint_results.map((cr) => {
                              const isWarning = cr.status === "UNREACHABLE" || cr.status === "INCONSISTENT";
                              const isSat = cr.status === "SAT";
                              return (
                                <div
                                  key={cr.name}
                                  className="flex items-center justify-between rounded bg-black/20 px-3 py-1.5"
                                >
                                  <span className="font-mono text-xs text-[#e4e4e7]">{cr.name}</span>
                                  <div className="flex items-center gap-2">
                                    <Badge
                                      variant="outline"
                                      className={
                                        isSat
                                          ? "border-[#22c55e]/30 text-[#22c55e] text-[10px]"
                                          : isWarning
                                            ? "border-[#f59e0b]/30 text-[#f59e0b] text-[10px]"
                                            : "border-[#ef4444]/30 text-[#ef4444] text-[10px]"
                                      }
                                    >
                                      {cr.status}
                                    </Badge>
                                    {isSat ? (
                                      <CheckCircle2 className="h-3.5 w-3.5 text-[#22c55e]" />
                                    ) : isWarning ? (
                                      <AlertTriangle className="h-3.5 w-3.5 text-[#f59e0b]" />
                                    ) : (
                                      <XCircle className="h-3.5 w-3.5 text-[#ef4444]" />
                                    )}
                                  </div>
                                </div>
                              );
                            })}

                            {/* Explanation for UNREACHABLE warnings */}
                            {verifyResult.constraint_results.some(cr => cr.status === "UNREACHABLE" || cr.status === "INCONSISTENT") && (
                              <div className="mt-2 flex items-start gap-2 rounded-lg border border-[#f59e0b]/20 bg-[#f59e0b]/5 px-3 py-2">
                                <Info className="h-3.5 w-3.5 text-[#f59e0b] mt-0.5 shrink-0" />
                                <p className="text-[11px] text-[#f59e0b]/80 leading-relaxed">
                                  <strong className="text-[#f59e0b]">UNREACHABLE</strong> means Z3 determined that a constraint&apos;s WHEN condition, combined with other constraints, leaves no valid input space for its THEN clause. This is often intentional (e.g. fully blocking a role) — review to confirm it matches your intent.
                                </p>
                              </div>
                            )}
                          </div>
                        )}

                        {verifyResult.messages.length > 0 && (
                          <ul className="mt-2 space-y-1">
                            {verifyResult.messages.map((m, i) => (
                              <li key={i} className="text-xs text-[#71717a] font-mono">{m}</li>
                            ))}
                          </ul>
                        )}
                      </div>
                    )}

                    <Separator className="bg-[#1e1e2e]" />

                    {/* Constraints */}
                    <div>
                      <h3 className="flex items-center gap-2 text-sm font-medium text-white mb-3">
                        <Lock className="h-4 w-4 text-[#6366f1]" />
                        Constraints
                      </h3>
                      <div className="space-y-2">
                        {selected.constraint_names.map((name) => (
                          <div key={name} className="rounded-lg border border-[#1e1e2e] bg-[#0a0a0f] px-3 py-2">
                            <span className="font-mono text-xs text-[#e4e4e7]">{name}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    <Separator className="bg-[#1e1e2e]" />

                    {/* Variables */}
                    <div>
                      <h3 className="flex items-center gap-2 text-sm font-medium text-white mb-3">
                        <Variable className="h-4 w-4 text-[#f59e0b]" />
                        Variables
                      </h3>
                      <div className="space-y-2">
                        {selected.variable_names.map((name) => (
                          <div
                            key={name}
                            className="flex items-center justify-between rounded-lg border border-[#1e1e2e] bg-[#0a0a0f] px-3 py-2"
                          >
                            <span className="font-mono text-xs text-[#e4e4e7]">{name}</span>
                            <span className="font-mono text-[10px] text-[#71717a]">
                              {selected.variable_domains[name] || "—"}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Hash */}
                    <div className="rounded-lg border border-[#1e1e2e] bg-[#0a0a0f] p-3">
                      <p className="text-xs text-[#71717a]">Policy Hash</p>
                      <p className="mt-1 font-mono text-[10px] text-[#e4e4e7] break-all">{selected.hash}</p>
                    </div>
                  </CardContent>
                </Card>
              ) : (
                <Card className="border-[#1e1e2e] bg-[#111119]">
                  <CardContent className="py-16 text-center text-[#71717a]">
                    Select a policy to view details
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        </TabsContent>

        {/* ══════════════ TAB 2: Create Policy ══════════════ */}
        <TabsContent value="create" className="mt-6">
          <Card className="border-[#1e1e2e] bg-[#111119]">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Plus className="h-5 w-5 text-[#6366f1]" />
                Create New Policy
              </CardTitle>
              <p className="text-sm text-[#71717a]">
                Write a CSL (with Z3 formal verification) or YAML policy
              </p>
            </CardHeader>
            <CardContent className="space-y-5">
              {/* Format Selector */}
              <div className="flex gap-3">
                <button
                  onClick={() => handleFormatChange("csl")}
                  className={`flex items-center gap-2 rounded-lg border px-4 py-2.5 text-sm transition ${
                    editorFormat === "csl"
                      ? "border-[#6366f1] bg-[#6366f1]/10 text-[#818cf8]"
                      : "border-[#1e1e2e] text-[#71717a] hover:border-[#2e2e3e]"
                  }`}
                >
                  <Zap className="h-4 w-4" />
                  CSL + Z3
                </button>
                <button
                  onClick={() => handleFormatChange("yaml")}
                  className={`flex items-center gap-2 rounded-lg border px-4 py-2.5 text-sm transition ${
                    editorFormat === "yaml"
                      ? "border-[#f59e0b] bg-[#f59e0b]/10 text-[#f59e0b]"
                      : "border-[#1e1e2e] text-[#71717a] hover:border-[#2e2e3e]"
                  }`}
                >
                  <FileText className="h-4 w-4" />
                  YAML
                </button>
              </div>

              {/* Filename */}
              <div>
                <label className="block text-sm text-[#a1a1aa] mb-2">Filename</label>
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    value={editorFilename}
                    onChange={(e) => {
                      setEditorFilename(e.target.value);
                      setSaveMessage(null);
                    }}
                    placeholder={editorFormat === "csl" ? "my-policy" : "my-rules"}
                    className="flex-1 bg-[#0a0a0f] border border-[#1e1e2e] rounded-lg px-4 py-2.5 text-white placeholder:text-[#52525b] focus:border-[#6366f1] focus:ring-1 focus:ring-[#6366f1] outline-none font-mono text-sm"
                  />
                  <span className="text-sm text-[#71717a] font-mono">
                    {editorFormat === "csl" ? ".csl" : ".yaml"}
                  </span>
                </div>
              </div>

              {/* Code Editor */}
              <div>
                <label className="block text-sm text-[#a1a1aa] mb-2">Policy Content</label>
                <textarea
                  value={editorContent}
                  onChange={(e) => {
                    setEditorContent(e.target.value);
                    setSaveMessage(null);
                  }}
                  rows={20}
                  spellCheck={false}
                  className="w-full bg-[#0a0a0f] border border-[#1e1e2e] rounded-lg p-4 text-[#e4e4e7] placeholder:text-[#52525b] focus:border-[#6366f1] focus:ring-1 focus:ring-[#6366f1] outline-none font-mono text-sm leading-relaxed resize-y"
                />
              </div>

              {/* Save Message */}
              {saveMessage && (
                <div
                  className={`rounded-lg border p-3 text-sm ${
                    saveMessage.type === "success"
                      ? "border-[#22c55e]/30 bg-[#22c55e]/5 text-[#22c55e]"
                      : "border-[#ef4444]/30 bg-[#ef4444]/5 text-[#ef4444]"
                  }`}
                >
                  {saveMessage.text}
                </div>
              )}

              {/* Actions */}
              <div className="flex gap-3">
                <Button
                  onClick={handleSave}
                  disabled={saving || !editorFilename.trim()}
                  className="bg-[#6366f1] hover:bg-[#5558e6] text-white"
                >
                  {saving ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <Save className="mr-2 h-4 w-4" />
                  )}
                  Save Policy
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        {/* ══════════════ TAB 3: Simulate ══════════════ */}
        <TabsContent value="simulate" className="mt-6">
          <ProGate feature="Policy Simulation">
            <Card className="border-[#1e1e2e] bg-[#111119]">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <FlaskConical className="h-5 w-5 text-[#6366f1]" />
                  Policy Simulation
                </CardTitle>
                <p className="text-sm text-[#71717a]">
                  Test inputs against a policy to see if they would be ALLOWED or BLOCKED
                </p>
              </CardHeader>
              <CardContent className="space-y-5">
                {/* Policy Selector */}
                <div>
                  <label className="block text-sm text-[#a1a1aa] mb-2">Select Policy</label>
                  <select
                    value={simPolicy}
                    onChange={(e) => handleSimPolicyChange(e.target.value)}
                    className="w-full bg-[#0a0a0f] border border-[#1e1e2e] rounded-lg px-4 py-2.5 text-white focus:border-[#6366f1] focus:ring-1 focus:ring-[#6366f1] outline-none text-sm"
                  >
                    <option value="">Choose a policy...</option>
                    {policies.map((p) => (
                      <option key={p.filename} value={p.filename}>
                        {p.filename} — {p.domain_name}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Variable Inputs */}
                {simDetail && simDetail.variable_names.length > 0 && (
                  <div>
                    <label className="block text-sm text-[#a1a1aa] mb-3">Parameters</label>
                    <div className="grid gap-3 sm:grid-cols-2">
                      {simDetail.variable_names.map((varName) => {
                        const domain = simDetail.variable_domains[varName] || "";
                        const isRange = domain.includes("..");
                        const isEnum = domain.startsWith("{") && domain.endsWith("}");
                        const enumVals = isEnum
                          ? domain.slice(1, -1).split(",").map(s => s.trim().replace(/"/g, ""))
                          : [];

                        return (
                          <div key={varName} className="rounded-lg border border-[#1e1e2e] bg-[#0a0a0f] p-3">
                            <div className="flex items-center justify-between mb-2">
                              <span className="font-mono text-xs text-[#e4e4e7]">{varName}</span>
                              <span className="font-mono text-[10px] text-[#71717a]">{domain}</span>
                            </div>
                            {isEnum ? (
                              <select
                                value={simParams[varName] || ""}
                                onChange={(e) => setSimParams(prev => ({ ...prev, [varName]: e.target.value }))}
                                className="w-full bg-[#111119] border border-[#1e1e2e] rounded px-3 py-1.5 text-white text-sm focus:border-[#6366f1] outline-none"
                              >
                                {enumVals.map((v) => (
                                  <option key={v} value={v}>{v}</option>
                                ))}
                              </select>
                            ) : (
                              <input
                                type={isRange ? "number" : "text"}
                                value={simParams[varName] || ""}
                                onChange={(e) => setSimParams(prev => ({ ...prev, [varName]: e.target.value }))}
                                placeholder={domain}
                                className="w-full bg-[#111119] border border-[#1e1e2e] rounded px-3 py-1.5 text-white text-sm focus:border-[#6366f1] outline-none font-mono"
                              />
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Run Button */}
                <Button
                  onClick={handleSimulate}
                  disabled={!simPolicy || simulating}
                  className="bg-[#6366f1] hover:bg-[#5558e6] text-white"
                >
                  {simulating ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <Play className="mr-2 h-4 w-4" />
                  )}
                  Run Simulation
                </Button>

                {/* Results */}
                {simResult && (
                  <div
                    className={`rounded-lg border p-4 ${
                      simResult.result === "ALLOWED"
                        ? "border-[#22c55e]/30 bg-[#22c55e]/5"
                        : simResult.result === "ERROR"
                          ? "border-[#f59e0b]/30 bg-[#f59e0b]/5"
                          : "border-[#ef4444]/30 bg-[#ef4444]/5"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        {simResult.result === "ALLOWED" ? (
                          <CheckCircle2 className="h-6 w-6 text-[#22c55e]" />
                        ) : (
                          <XCircle className="h-6 w-6 text-[#ef4444]" />
                        )}
                        <div>
                          <span className={`text-lg font-bold ${
                            simResult.result === "ALLOWED" ? "text-[#22c55e]" : "text-[#ef4444]"
                          }`}>
                            {simResult.result}
                          </span>
                          <p className="text-xs text-[#71717a]">
                            Evaluated in {simResult.duration_ms}ms
                          </p>
                        </div>
                      </div>
                      <Badge
                        variant="outline"
                        className={
                          simResult.result === "ALLOWED"
                            ? "border-[#22c55e]/30 text-[#22c55e]"
                            : "border-[#ef4444]/30 text-[#ef4444]"
                        }
                      >
                        {simResult.violations.length} violation{simResult.violations.length !== 1 ? "s" : ""}
                      </Badge>
                    </div>

                    {simResult.violations.length > 0 && (
                      <div className="mt-3 space-y-2">
                        <Separator className="bg-white/10" />
                        {simResult.violations.map((v, i) => (
                          <div key={i} className="rounded bg-black/20 px-3 py-2">
                            <p className="font-mono text-xs text-[#f59e0b]">{v.constraint}</p>
                            <p className="mt-0.5 text-xs text-[#e4e4e7]">{v.explanation}</p>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          </ProGate>
        </TabsContent>

        {/* ══════════════ TAB 4: Marketplace ══════════════ */}
        <TabsContent value="marketplace" className="mt-6">
          <PolicyMarketplace />
        </TabsContent>
      </Tabs>
    </div>
  );
}
