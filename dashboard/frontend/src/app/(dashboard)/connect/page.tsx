"use client";

import { useState } from "react";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import {
  Plug,
  Copy,
  Check,
  ChevronRight,
  ChevronLeft,
  Terminal,
  FileText,
  ArrowRight,
  Zap,
  Code2,
  Loader2,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";
import type { PolicyDetail } from "@/lib/types";
import { useEffect } from "react";

// ── Framework Data ──────────────────────────────────────────────

interface Framework {
  id: string;
  name: string;
  logo: string;
  installExtra: string;
  color: string;
}

const FRAMEWORKS: Framework[] = [
  { id: "langchain", name: "LangChain", logo: "🦜", installExtra: "langchain", color: "#22c55e" },
  { id: "langgraph", name: "LangGraph", logo: "🔀", installExtra: "langgraph", color: "#06b6d4" },
  { id: "crewai", name: "CrewAI", logo: "👥", installExtra: "crewai", color: "#a855f7" },
  { id: "llamaindex", name: "LlamaIndex", logo: "🦙", installExtra: "llamaindex", color: "#f59e0b" },
  { id: "autogen", name: "AutoGen", logo: "🤖", installExtra: "autogen", color: "#ef4444" },
];

// ── Code Generators ─────────────────────────────────────────────

function generateCode(
  framework: string,
  policyFile: string,
  mappings: Record<string, string>,
  agentName: string,
): string {
  const mappingEntries = Object.entries(mappings).filter(([, v]) => v);
  const hasMapping = mappingEntries.length > 0;
  const mappingStr = hasMapping
    ? `\n    param_mapping={\n${mappingEntries.map(([k, v]) => `        "${v}": "${k}",  # your param → policy variable`).join("\n")}\n    },`
    : "";

  switch (framework) {
    case "langchain":
      return `from chimera_runtime.integrations.langchain import wrap_tools

# Wrap your existing tools with runtime guard
guarded_tools = wrap_tools(
    tools=[${agentName || "your_tool"}],
    policy="./policies/${policyFile}",${mappingStr}
)

# Use guarded_tools in your agent instead of raw tools
# agent = create_react_agent(llm, guarded_tools, ...)`;

    case "langgraph":
      return `from chimera_runtime.integrations.langgraph import compliance_node, compliance_edge

# Create enforcement check node
check = compliance_node(
    policy="./policies/${policyFile}",${mappingStr}
)
route = compliance_edge(allowed_node="execute", blocked_node="handle_block")

# Add to your graph
graph.add_node("compliance", check)
graph.add_edge("agent", "compliance")
graph.add_conditional_edges("compliance", route)`;

    case "crewai":
      return `from chimera_runtime.integrations.crewai import wrap_crew_tools

# Wrap your CrewAI tools
guarded_tools = wrap_crew_tools(
    tools=[${agentName || "your_tool"}],
    policy="./policies/${policyFile}",${mappingStr}
)

# Use in your Crew
# crew = Crew(agents=[agent], tasks=[task], tools=guarded_tools)`;

    case "llamaindex":
      return `from chimera_runtime.integrations.llamaindex import wrap_tools

# Wrap your LlamaIndex tools
guarded_tools = wrap_tools(
    tools=[${agentName || "your_tool"}],
    policy="./policies/${policyFile}",${mappingStr}
)

# Use in your agent
# agent = ReActAgent.from_tools(guarded_tools, llm=llm)`;

    case "autogen":
      return `from chimera_runtime.integrations.autogen import guard_function_call

# Decorator: wrap any function with runtime guard
@guard_function_call(
    policy="./policies/${policyFile}",${mappingStr}
)
def ${agentName || "your_function"}(${mappingEntries.map(([, v]) => v).join(", ") || "**kwargs"}):
    # Your function logic
    ...`;

    default:
      return "";
  }
}

// ── Component ───────────────────────────────────────────────────

export default function ConnectAgentPage() {
  const { user } = useAuth();
  const [step, setStep] = useState(0);

  // Step 0: Framework selection
  const [selectedFramework, setSelectedFramework] = useState<string>("");

  // Step 1: Policy selection
  const [policies, setPolicies] = useState<{ filename: string; domain_name: string; variable_names?: string[] }[]>([]);
  const [selectedPolicy, setSelectedPolicy] = useState<string>("");
  const [policyDetail, setPolicyDetail] = useState<PolicyDetail | null>(null);
  const [policiesLoading, setPoliciesLoading] = useState(false);

  // Step 2: Variable mapping
  const [mappings, setMappings] = useState<Record<string, string>>({});
  const [agentToolName, setAgentToolName] = useState("");

  // Copy state
  const [copiedInstall, setCopiedInstall] = useState(false);
  const [copiedCode, setCopiedCode] = useState(false);

  // Fetch policies when entering step 1
  useEffect(() => {
    if (step === 1 && policies.length === 0) {
      setPoliciesLoading(true);
      api.getPolicies().then((res) => {
        setPolicies(res.policies);
        setPoliciesLoading(false);
      }).catch(() => setPoliciesLoading(false));
    }
  }, [step, policies.length]);

  // Fetch policy detail when selected
  useEffect(() => {
    if (selectedPolicy) {
      api.getPolicy(selectedPolicy).then(setPolicyDetail).catch(() => {});
    }
  }, [selectedPolicy]);

  const fw = FRAMEWORKS.find((f) => f.id === selectedFramework);
  const installCmd = fw
    ? `pip install chimera-runtime[${fw.installExtra}]`
    : "pip install chimera-runtime";

  const handleCopy = async (text: string, setter: (v: boolean) => void) => {
    await navigator.clipboard.writeText(text);
    setter(true);
    setTimeout(() => setter(false), 2000);
  };

  const generatedCode = fw && selectedPolicy
    ? generateCode(fw.id, selectedPolicy, mappings, agentToolName)
    : "";

  const steps = [
    { label: "Framework", icon: Zap },
    { label: "Policy", icon: FileText },
    { label: "Mapping", icon: Plug },
    { label: "Integrate", icon: Code2 },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Connect Agent</h1>
        <p className="mt-1 text-sm text-[#71717a]">
          Add runtime guard to your AI agent in 4 steps
        </p>
      </div>

      {/* Step Indicator */}
      <div className="flex items-center gap-1">
        {steps.map((s, i) => (
          <div key={s.label} className="flex items-center">
            <button
              onClick={() => {
                if (i < step) setStep(i);
              }}
              disabled={i > step}
              className={`flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition ${
                i === step
                  ? "bg-[#6366f1]/10 text-[#818cf8] border border-[#6366f1]/30"
                  : i < step
                    ? "text-[#22c55e] cursor-pointer hover:bg-[#22c55e]/5"
                    : "text-[#52525b] cursor-default"
              }`}
            >
              {i < step ? (
                <CheckCircle2 className="h-4 w-4" />
              ) : (
                <s.icon className="h-4 w-4" />
              )}
              {s.label}
            </button>
            {i < steps.length - 1 && (
              <ChevronRight className="h-4 w-4 text-[#52525b] mx-1" />
            )}
          </div>
        ))}
      </div>

      {/* Step Content */}
      <div className="rounded-xl border border-[#1e1e2e] bg-[#111119] p-6">

        {/* ── Step 0: Framework Selection ─────────────────────── */}
        {step === 0 && (
          <div>
            <h2 className="text-lg font-semibold text-white mb-1">Select your framework</h2>
            <p className="text-sm text-[#71717a] mb-6">Which AI agent framework are you using?</p>

            <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
              {FRAMEWORKS.map((f) => (
                <button
                  key={f.id}
                  onClick={() => setSelectedFramework(f.id)}
                  className={`flex items-center gap-3 rounded-xl border p-4 transition text-left ${
                    selectedFramework === f.id
                      ? "border-[#6366f1] bg-[#6366f1]/5"
                      : "border-[#1e1e2e] hover:border-[#2e2e3e] bg-[#0a0a0f]"
                  }`}
                >
                  <span className="text-2xl">{f.logo}</span>
                  <div>
                    <p className="text-sm font-medium text-white">{f.name}</p>
                    <p className="text-[11px] text-[#71717a]">chimera-runtime[{f.installExtra}]</p>
                  </div>
                </button>
              ))}
            </div>

            {selectedFramework && (
              <div className="mt-6">
                <p className="text-xs text-[#71717a] mb-2">Install command:</p>
                <div className="flex items-center gap-2 rounded-lg bg-[#0a0a0f] border border-[#1e1e2e] px-4 py-3">
                  <Terminal className="h-4 w-4 text-[#6366f1] shrink-0" />
                  <code className="flex-1 text-sm text-[#e4e4e7] font-mono">{installCmd}</code>
                  <button
                    onClick={() => handleCopy(installCmd, setCopiedInstall)}
                    className="text-[#71717a] hover:text-white transition shrink-0"
                  >
                    {copiedInstall ? <Check className="h-4 w-4 text-[#22c55e]" /> : <Copy className="h-4 w-4" />}
                  </button>
                </div>
              </div>
            )}

            <div className="mt-6 flex justify-end">
              <button
                onClick={() => setStep(1)}
                disabled={!selectedFramework}
                className="flex items-center gap-2 bg-[#6366f1] hover:bg-[#5558e6] text-white text-sm font-medium px-4 py-2.5 rounded-lg transition disabled:opacity-30"
              >
                Next <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}

        {/* ── Step 1: Policy Selection ────────────────────────── */}
        {step === 1 && (
          <div>
            <h2 className="text-lg font-semibold text-white mb-1">Choose a policy</h2>
            <p className="text-sm text-[#71717a] mb-6">
              Select the enforcement policy your agent will be governed by
            </p>

            {policiesLoading ? (
              <div className="flex justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-[#6366f1]" />
              </div>
            ) : (
              <div className="space-y-2">
                {policies.map((p) => (
                  <button
                    key={p.filename}
                    onClick={() => setSelectedPolicy(p.filename)}
                    className={`w-full flex items-center justify-between rounded-lg border p-4 transition text-left ${
                      selectedPolicy === p.filename
                        ? "border-[#6366f1] bg-[#6366f1]/5"
                        : "border-[#1e1e2e] hover:border-[#2e2e3e] bg-[#0a0a0f]"
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <FileText className="h-4 w-4 text-[#6366f1]" />
                      <div>
                        <p className="text-sm font-medium text-white">{p.filename}</p>
                        <p className="text-xs text-[#71717a]">{p.domain_name}</p>
                      </div>
                    </div>
                    {selectedPolicy === p.filename && (
                      <CheckCircle2 className="h-4 w-4 text-[#6366f1]" />
                    )}
                  </button>
                ))}
              </div>
            )}

            {/* Selected policy variables preview */}
            {policyDetail && (
              <div className="mt-4 rounded-lg border border-[#1e1e2e] bg-[#0a0a0f] p-4">
                <p className="text-xs text-[#71717a] mb-2">Policy variables (your agent params must map to these):</p>
                <div className="flex flex-wrap gap-2">
                  {policyDetail.variable_names.map((v) => (
                    <span
                      key={v}
                      className="rounded-md bg-[#6366f1]/10 border border-[#6366f1]/20 px-2 py-1 text-xs font-mono text-[#818cf8]"
                    >
                      {v}
                      <span className="text-[#52525b] ml-1">
                        {policyDetail.variable_domains[v] || ""}
                      </span>
                    </span>
                  ))}
                </div>
              </div>
            )}

            <div className="mt-6 flex justify-between">
              <button
                onClick={() => setStep(0)}
                className="flex items-center gap-2 text-[#71717a] hover:text-white text-sm font-medium px-4 py-2.5 rounded-lg transition"
              >
                <ChevronLeft className="h-4 w-4" /> Back
              </button>
              <button
                onClick={() => setStep(2)}
                disabled={!selectedPolicy}
                className="flex items-center gap-2 bg-[#6366f1] hover:bg-[#5558e6] text-white text-sm font-medium px-4 py-2.5 rounded-lg transition disabled:opacity-30"
              >
                Next <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}

        {/* ── Step 2: Variable Mapping ────────────────────────── */}
        {step === 2 && (
          <div>
            <h2 className="text-lg font-semibold text-white mb-1">Map your parameters</h2>
            <p className="text-sm text-[#71717a] mb-2">
              Map your agent&apos;s function parameters to policy variables.
              If names match exactly, no mapping is needed.
            </p>

            <div className="mb-4 flex items-start gap-2 rounded-lg border border-[#6366f1]/20 bg-[#6366f1]/5 px-3 py-2">
              <AlertCircle className="h-3.5 w-3.5 text-[#818cf8] mt-0.5 shrink-0" />
              <p className="text-[11px] text-[#818cf8]/80 leading-relaxed">
                If your tool&apos;s keyword arguments already match the policy variable names (e.g. your function takes <code className="bg-[#6366f1]/10 px-1 rounded">amount</code> and the policy uses <code className="bg-[#6366f1]/10 px-1 rounded">amount</code>), you can skip this step — chimera-runtime will auto-detect them.
              </p>
            </div>

            {/* Agent tool name */}
            <div className="mb-4">
              <label className="block text-xs text-[#a1a1aa] mb-1.5">Your tool/function name</label>
              <input
                type="text"
                value={agentToolName}
                onChange={(e) => setAgentToolName(e.target.value)}
                placeholder="e.g. approve_budget, transfer_funds"
                className="w-full bg-[#0a0a0f] border border-[#1e1e2e] rounded-lg px-4 py-2.5 text-white placeholder:text-[#52525b] focus:border-[#6366f1] focus:ring-1 focus:ring-[#6366f1] outline-none text-sm font-mono"
              />
            </div>

            {/* Variable mapping table */}
            {policyDetail && (
              <div className="rounded-lg border border-[#1e1e2e] overflow-hidden">
                <div className="grid grid-cols-[1fr_auto_1fr] gap-0 bg-[#0a0a0f] px-4 py-2 border-b border-[#1e1e2e]">
                  <span className="text-xs font-medium text-[#71717a]">Policy Variable</span>
                  <span className="px-4" />
                  <span className="text-xs font-medium text-[#71717a]">Your Parameter Name</span>
                </div>
                {policyDetail.variable_names.map((varName) => (
                  <div
                    key={varName}
                    className="grid grid-cols-[1fr_auto_1fr] gap-0 items-center px-4 py-2.5 border-b border-[#1e1e2e] last:border-0"
                  >
                    <div>
                      <code className="text-sm text-[#818cf8] font-mono">{varName}</code>
                      <span className="ml-2 text-[10px] text-[#52525b]">
                        {policyDetail.variable_domains[varName] || ""}
                      </span>
                    </div>
                    <ArrowRight className="h-3.5 w-3.5 text-[#52525b] mx-3" />
                    <input
                      type="text"
                      value={mappings[varName] || ""}
                      onChange={(e) =>
                        setMappings((m) => ({ ...m, [varName]: e.target.value }))
                      }
                      placeholder={varName}
                      className="bg-[#0a0a0f] border border-[#1e1e2e] rounded-md px-3 py-1.5 text-sm text-white placeholder:text-[#3f3f46] focus:border-[#6366f1] outline-none font-mono"
                    />
                  </div>
                ))}
              </div>
            )}

            <div className="mt-6 flex justify-between">
              <button
                onClick={() => setStep(1)}
                className="flex items-center gap-2 text-[#71717a] hover:text-white text-sm font-medium px-4 py-2.5 rounded-lg transition"
              >
                <ChevronLeft className="h-4 w-4" /> Back
              </button>
              <button
                onClick={() => setStep(3)}
                className="flex items-center gap-2 bg-[#6366f1] hover:bg-[#5558e6] text-white text-sm font-medium px-4 py-2.5 rounded-lg transition"
              >
                Generate Code <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}

        {/* ── Step 3: Generated Code ──────────────────────────── */}
        {step === 3 && (
          <div>
            <h2 className="text-lg font-semibold text-white mb-1">Integration code</h2>
            <p className="text-sm text-[#71717a] mb-6">
              Copy this code into your {fw?.name} project. Every tool call will be checked against your policy.
            </p>

            {/* Install */}
            <div className="mb-4">
              <p className="text-xs text-[#71717a] mb-2">1. Install</p>
              <div className="flex items-center gap-2 rounded-lg bg-[#0a0a0f] border border-[#1e1e2e] px-4 py-3">
                <Terminal className="h-4 w-4 text-[#22c55e] shrink-0" />
                <code className="flex-1 text-sm text-[#e4e4e7] font-mono">{installCmd}</code>
                <button
                  onClick={() => handleCopy(installCmd, setCopiedInstall)}
                  className="text-[#71717a] hover:text-white transition shrink-0"
                >
                  {copiedInstall ? <Check className="h-4 w-4 text-[#22c55e]" /> : <Copy className="h-4 w-4" />}
                </button>
              </div>
            </div>

            {/* Code */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <p className="text-xs text-[#71717a]">2. Add to your agent</p>
                <button
                  onClick={() => handleCopy(generatedCode, setCopiedCode)}
                  className="flex items-center gap-1.5 text-xs text-[#71717a] hover:text-white transition"
                >
                  {copiedCode ? (
                    <><Check className="h-3.5 w-3.5 text-[#22c55e]" /> Copied</>
                  ) : (
                    <><Copy className="h-3.5 w-3.5" /> Copy code</>
                  )}
                </button>
              </div>
              <pre className="rounded-lg bg-[#0a0a0f] border border-[#1e1e2e] p-4 overflow-x-auto">
                <code className="text-sm text-[#e4e4e7] font-mono whitespace-pre">
                  {generatedCode}
                </code>
              </pre>
            </div>

            {/* What happens next */}
            <div className="mt-6 rounded-lg border border-[#22c55e]/20 bg-[#22c55e]/5 p-4">
              <p className="text-sm font-medium text-[#22c55e] mb-2">What happens now?</p>
              <ul className="space-y-1.5 text-xs text-[#22c55e]/80">
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="h-3.5 w-3.5 mt-0.5 shrink-0" />
                  Every tool call is evaluated against your <code className="bg-[#22c55e]/10 px-1 rounded">{selectedPolicy}</code> policy
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="h-3.5 w-3.5 mt-0.5 shrink-0" />
                  BLOCKED actions raise an exception with violation details
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="h-3.5 w-3.5 mt-0.5 shrink-0" />
                  Every decision is recorded in <code className="bg-[#22c55e]/10 px-1 rounded">./audit_logs/</code>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="h-3.5 w-3.5 mt-0.5 shrink-0" />
                  View results in this dashboard under Decisions
                </li>
              </ul>
            </div>

            <div className="mt-6 flex justify-between">
              <button
                onClick={() => setStep(2)}
                className="flex items-center gap-2 text-[#71717a] hover:text-white text-sm font-medium px-4 py-2.5 rounded-lg transition"
              >
                <ChevronLeft className="h-4 w-4" /> Back
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
