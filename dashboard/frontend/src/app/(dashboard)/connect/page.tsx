"use client";

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import { motion, AnimatePresence } from "framer-motion";
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
  Key,
  Rocket,
  ShieldCheck,
  Sparkles,
  Eye,
  EyeOff,
} from "lucide-react";
import type { PolicyDetail } from "@/lib/types";

// ── Framework Data ──────────────────────────────────────────────

interface Framework {
  id: string;
  name: string;
  logo: string;
  installExtra: string;
  color: string;
  description: string;
}

const FRAMEWORKS: Framework[] = [
  { id: "langchain", name: "LangChain", logo: "🦜", installExtra: "langchain", color: "#22c55e", description: "Tool wrapping for ReAct agents" },
  { id: "langgraph", name: "LangGraph", logo: "🔀", installExtra: "langgraph", color: "#06b6d4", description: "Graph node & edge integration" },
  { id: "crewai", name: "CrewAI", logo: "👥", installExtra: "crewai", color: "#a855f7", description: "Multi-agent crew tool guard" },
  { id: "llamaindex", name: "LlamaIndex", logo: "🦙", installExtra: "llamaindex", color: "#f59e0b", description: "Query engine tool wrapping" },
  { id: "autogen", name: "AutoGen", logo: "🤖", installExtra: "autogen", color: "#ef4444", description: "Function call decorator" },
];

// ── Animation Variants ──────────────────────────────────────────

const fadeSlideUp = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -20 },
};

const staggerContainer = {
  animate: {
    transition: { staggerChildren: 0.06 },
  },
};

const staggerItem = {
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0 },
};

const scaleOnHover = {
  whileHover: { scale: 1.03, transition: { duration: 0.2 } },
  whileTap: { scale: 0.98 },
};

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

// ── Sparkle / Confetti Effect ───────────────────────────────────

function SparkleEffect() {
  const particles = Array.from({ length: 24 }, (_, i) => ({
    id: i,
    x: Math.random() * 100,
    y: Math.random() * 100,
    size: Math.random() * 4 + 2,
    delay: Math.random() * 2,
    duration: Math.random() * 2 + 1.5,
  }));

  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {particles.map((p) => (
        <motion.div
          key={p.id}
          className="absolute rounded-full"
          style={{
            left: `${p.x}%`,
            top: `${p.y}%`,
            width: p.size,
            height: p.size,
            background: p.id % 3 === 0 ? "#6366f1" : p.id % 3 === 1 ? "#22c55e" : "#f59e0b",
          }}
          initial={{ opacity: 0, scale: 0 }}
          animate={{
            opacity: [0, 1, 0],
            scale: [0, 1.5, 0],
            y: [0, -30],
          }}
          transition={{
            duration: p.duration,
            delay: p.delay,
            repeat: Infinity,
            repeatDelay: Math.random() * 3,
          }}
        />
      ))}
    </div>
  );
}

// ── Copy Button Component ───────────────────────────────────────

function CopyButton({ text, className = "" }: { text: string; className?: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <button
      onClick={handleCopy}
      className={`text-[#71717a] hover:text-white transition shrink-0 ${className}`}
    >
      <AnimatePresence mode="wait">
        {copied ? (
          <motion.div
            key="check"
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            exit={{ scale: 0 }}
          >
            <Check className="h-4 w-4 text-[#22c55e]" />
          </motion.div>
        ) : (
          <motion.div
            key="copy"
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            exit={{ scale: 0 }}
          >
            <Copy className="h-4 w-4" />
          </motion.div>
        )}
      </AnimatePresence>
    </button>
  );
}

// ── Terminal Block Component ────────────────────────────────────

function TerminalBlock({ command, icon: Icon = Terminal, iconColor = "#6366f1" }: { command: string; icon?: React.ComponentType<{ className?: string; style?: React.CSSProperties }>; iconColor?: string }) {
  return (
    <div className="flex items-center gap-2 rounded-lg bg-[#0a0a0f]/80 backdrop-blur-sm border border-[#1e1e2e] px-4 py-3 group">
      <Icon className={`h-4 w-4 shrink-0`} style={{ color: iconColor }} />
      <code className="flex-1 text-sm text-[#e4e4e7] font-mono select-all">{command}</code>
      <CopyButton text={command} />
    </div>
  );
}

// ── Glassmorphic Card ───────────────────────────────────────────

function GlassCard({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={`rounded-xl border border-[#1e1e2e] bg-[#111119]/80 backdrop-blur-xl shadow-2xl shadow-black/20 ${className}`}>
      {children}
    </div>
  );
}

// ── Component ───────────────────────────────────────────────────

export default function ConnectAgentPage() {
  const { user } = useAuth();
  const [step, setStep] = useState(0);

  // Step 0: API Key
  const [apiKeys, setApiKeys] = useState<Array<{ id: number; key_prefix: string; name: string; created_at: string; last_used: string | null; revoked: boolean }>>([]);
  const [apiKeysLoading, setApiKeysLoading] = useState(true);
  const [newApiKey, setNewApiKey] = useState<string | null>(null);
  const [creatingKey, setCreatingKey] = useState(false);
  const [showKey, setShowKey] = useState(true);

  // Step 1: Framework selection
  const [selectedFramework, setSelectedFramework] = useState<string>("");

  // Step 2: Policy selection
  const [policies, setPolicies] = useState<{ filename: string; domain_name: string; variable_names?: string[] }[]>([]);
  const [selectedPolicy, setSelectedPolicy] = useState<string>("");
  const [policyDetail, setPolicyDetail] = useState<PolicyDetail | null>(null);
  const [policiesLoading, setPoliciesLoading] = useState(false);

  // Step 3: Variable mapping
  const [mappings, setMappings] = useState<Record<string, string>>({});
  const [agentToolName, setAgentToolName] = useState("");

  // Copy states
  const [copiedCode, setCopiedCode] = useState(false);

  // Fetch API keys on mount
  useEffect(() => {
    setApiKeysLoading(true);
    api.getApiKeys()
      .then((res) => {
        const activeKeys = res.keys.filter((k) => !k.revoked);
        setApiKeys(activeKeys);
        setApiKeysLoading(false);
      })
      .catch(() => setApiKeysLoading(false));
  }, []);

  // Fetch policies when entering step 2
  useEffect(() => {
    if (step === 2 && policies.length === 0) {
      setPoliciesLoading(true);
      api.getPolicies()
        .then((res) => {
          setPolicies(res.policies);
          setPoliciesLoading(false);
        })
        .catch(() => setPoliciesLoading(false));
    }
  }, [step, policies.length]);

  // Fetch policy detail when selected
  useEffect(() => {
    if (selectedPolicy) {
      api.getPolicy(selectedPolicy).then(setPolicyDetail).catch(() => {});
    }
  }, [selectedPolicy]);

  const handleCreateApiKey = useCallback(async () => {
    setCreatingKey(true);
    try {
      const res = await api.createApiKey("default");
      setNewApiKey(res.key);
      setApiKeys((prev) => [
        ...prev,
        { id: res.id, key_prefix: res.key_prefix, name: res.name, created_at: res.created_at, last_used: null, revoked: false },
      ]);
    } catch {
      // handle error silently
    } finally {
      setCreatingKey(false);
    }
  }, []);

  const fw = FRAMEWORKS.find((f) => f.id === selectedFramework);
  const installCmd = fw
    ? `pip install chimera-runtime[${fw.installExtra}]`
    : "pip install chimera-runtime";

  const generatedCode = fw && selectedPolicy
    ? generateCode(fw.id, selectedPolicy, mappings, agentToolName)
    : "";

  const hasApiKey = apiKeys.length > 0 || newApiKey !== null;
  const apiKeyDisplay = newApiKey || (apiKeys.length > 0 ? `${apiKeys[0].key_prefix}...` : "chm_xxx");

  const steps = [
    { label: "API Key", icon: Key },
    { label: "Framework", icon: Zap },
    { label: "Policy", icon: FileText },
    { label: "Mapping", icon: Plug },
    { label: "Launch", icon: Rocket },
  ];

  const progressPercent = (step / (steps.length - 1)) * 100;

  const handleCopyCode = async (text: string) => {
    await navigator.clipboard.writeText(text);
    setCopiedCode(true);
    setTimeout(() => setCopiedCode(false), 2000);
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <h1 className="text-2xl font-bold text-white flex items-center gap-3">
          Connect Agent
          <motion.span
            animate={{ rotate: [0, 10, -10, 0] }}
            transition={{ duration: 2, repeat: Infinity, repeatDelay: 3 }}
          >
            <Plug className="h-6 w-6 text-[#6366f1]" />
          </motion.span>
        </h1>
        <p className="mt-1 text-sm text-[#71717a]">
          Set up runtime guard for your AI agent in 5 steps
        </p>
      </motion.div>

      {/* Progress Bar */}
      <div className="relative">
        <div className="h-1 bg-[#1e1e2e] rounded-full overflow-hidden">
          <motion.div
            className="h-full bg-gradient-to-r from-[#6366f1] to-[#818cf8] rounded-full"
            initial={{ width: 0 }}
            animate={{ width: `${progressPercent}%` }}
            transition={{ duration: 0.5, ease: "easeInOut" }}
          />
        </div>
      </div>

      {/* Step Indicator */}
      <div className="flex items-center gap-1 flex-wrap">
        {steps.map((s, i) => (
          <div key={s.label} className="flex items-center">
            <motion.button
              onClick={() => {
                if (i < step) setStep(i);
              }}
              disabled={i > step}
              className={`flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-all ${
                i === step
                  ? "bg-[#6366f1]/10 text-[#818cf8] border border-[#6366f1]/30 shadow-lg shadow-[#6366f1]/5"
                  : i < step
                    ? "text-[#22c55e] cursor-pointer hover:bg-[#22c55e]/5"
                    : "text-[#52525b] cursor-default"
              }`}
              whileHover={i < step ? { scale: 1.05 } : {}}
              whileTap={i < step ? { scale: 0.95 } : {}}
            >
              {i < step ? (
                <motion.div
                  initial={{ scale: 0, rotate: -180 }}
                  animate={{ scale: 1, rotate: 0 }}
                  transition={{ type: "spring", stiffness: 200 }}
                >
                  <CheckCircle2 className="h-4 w-4" />
                </motion.div>
              ) : (
                <s.icon className="h-4 w-4" />
              )}
              <span className="hidden sm:inline">{s.label}</span>
            </motion.button>
            {i < steps.length - 1 && (
              <ChevronRight className="h-4 w-4 text-[#52525b] mx-1" />
            )}
          </div>
        ))}
      </div>

      {/* Step Content */}
      <AnimatePresence mode="wait">
        <motion.div
          key={step}
          variants={fadeSlideUp}
          initial="initial"
          animate="animate"
          exit="exit"
          transition={{ duration: 0.35, ease: "easeOut" }}
        >
          <GlassCard className="p-6 relative overflow-hidden">
            {/* Subtle gradient glow behind active step */}
            <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[300px] h-[1px] bg-gradient-to-r from-transparent via-[#6366f1]/40 to-transparent" />

            {/* ── Step 0: API Key ─────────────────────────────────── */}
            {step === 0 && (
              <div>
                <div className="flex items-center gap-3 mb-1">
                  <div className="h-10 w-10 rounded-xl bg-[#6366f1]/10 border border-[#6366f1]/20 flex items-center justify-center">
                    <Key className="h-5 w-5 text-[#6366f1]" />
                  </div>
                  <div>
                    <h2 className="text-lg font-semibold text-white">Get Your API Key</h2>
                    <p className="text-sm text-[#71717a]">Required for cloud sync and dashboard telemetry</p>
                  </div>
                </div>

                <div className="mt-6">
                  {apiKeysLoading ? (
                    <div className="flex justify-center py-12">
                      <Loader2 className="h-6 w-6 animate-spin text-[#6366f1]" />
                    </div>
                  ) : hasApiKey && !newApiKey ? (
                    /* User already has keys */
                    <motion.div
                      initial={{ opacity: 0, scale: 0.95 }}
                      animate={{ opacity: 1, scale: 1 }}
                      className="rounded-xl border border-[#22c55e]/20 bg-[#22c55e]/5 p-6 text-center"
                    >
                      <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        transition={{ type: "spring", stiffness: 200, delay: 0.1 }}
                      >
                        <CheckCircle2 className="h-12 w-12 text-[#22c55e] mx-auto mb-3" />
                      </motion.div>
                      <p className="text-white font-medium mb-1">API Key Active</p>
                      <p className="text-sm text-[#71717a] mb-4">
                        You have {apiKeys.length} active API key{apiKeys.length > 1 ? "s" : ""}. Your most recent key starts with <code className="text-[#818cf8] bg-[#6366f1]/10 px-1.5 py-0.5 rounded font-mono text-xs">{apiKeys[0]?.key_prefix}...</code>
                      </p>
                      <div className="space-y-2 mt-4">
                        <p className="text-xs text-[#71717a] text-left mb-2">Environment setup:</p>
                        <TerminalBlock command={`export CHIMERA_DASHBOARD_API_KEY=${apiKeyDisplay}`} />
                        <TerminalBlock command="export CHIMERA_DASHBOARD_URL=https://api-runtime.chimera-protocol.com/api/v1" />
                      </div>
                    </motion.div>
                  ) : newApiKey ? (
                    /* Newly created key */
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="space-y-4"
                    >
                      <div className="rounded-xl border border-[#f59e0b]/30 bg-[#f59e0b]/5 p-4">
                        <div className="flex items-start gap-3">
                          <AlertCircle className="h-5 w-5 text-[#f59e0b] shrink-0 mt-0.5" />
                          <div>
                            <p className="text-sm font-medium text-[#f59e0b]">Save this key now</p>
                            <p className="text-xs text-[#f59e0b]/70 mt-1">You will not be able to see this key again. Copy it and store it securely.</p>
                          </div>
                        </div>
                      </div>

                      <div className="rounded-xl border border-[#1e1e2e] bg-[#0a0a0f] p-4">
                        <p className="text-xs text-[#71717a] mb-2">Your API Key:</p>
                        <div className="flex items-center gap-2 bg-[#111119] border border-[#1e1e2e] rounded-lg px-4 py-3">
                          <Key className="h-4 w-4 text-[#6366f1] shrink-0" />
                          <code className="flex-1 text-sm text-[#e4e4e7] font-mono select-all">
                            {showKey ? newApiKey : newApiKey.replace(/./g, "\u2022")}
                          </code>
                          <button
                            onClick={() => setShowKey(!showKey)}
                            className="text-[#71717a] hover:text-white transition shrink-0"
                          >
                            {showKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                          </button>
                          <CopyButton text={newApiKey} />
                        </div>
                      </div>

                      <div className="space-y-2">
                        <p className="text-xs text-[#71717a]">Add to your environment:</p>
                        <TerminalBlock command={`export CHIMERA_DASHBOARD_API_KEY=${newApiKey}`} />
                        <TerminalBlock command="export CHIMERA_DASHBOARD_URL=https://api-runtime.chimera-protocol.com/api/v1" />
                      </div>
                    </motion.div>
                  ) : (
                    /* No keys - create one */
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="text-center py-8"
                    >
                      <div className="mx-auto h-16 w-16 rounded-2xl bg-[#6366f1]/10 border border-[#6366f1]/20 flex items-center justify-center mb-4">
                        <Key className="h-8 w-8 text-[#6366f1]" />
                      </div>
                      <p className="text-white font-medium mb-2">No API Key Found</p>
                      <p className="text-sm text-[#71717a] mb-6 max-w-md mx-auto">
                        Create an API key to enable cloud sync between your agent and this dashboard.
                      </p>
                      <motion.button
                        onClick={handleCreateApiKey}
                        disabled={creatingKey}
                        className="inline-flex items-center gap-2 bg-[#6366f1] hover:bg-[#5558e6] text-white font-medium px-6 py-3 rounded-xl transition disabled:opacity-50 shadow-lg shadow-[#6366f1]/20"
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                      >
                        {creatingKey ? (
                          <Loader2 className="h-5 w-5 animate-spin" />
                        ) : (
                          <Key className="h-5 w-5" />
                        )}
                        {creatingKey ? "Creating..." : "Create API Key"}
                      </motion.button>
                    </motion.div>
                  )}
                </div>

                <div className="mt-6 flex justify-end">
                  <motion.button
                    onClick={() => setStep(1)}
                    className="flex items-center gap-2 bg-[#6366f1] hover:bg-[#5558e6] text-white text-sm font-medium px-5 py-2.5 rounded-lg transition shadow-lg shadow-[#6366f1]/10"
                    whileHover={{ scale: 1.03, x: 3 }}
                    whileTap={{ scale: 0.97 }}
                  >
                    Next <ChevronRight className="h-4 w-4" />
                  </motion.button>
                </div>
              </div>
            )}

            {/* ── Step 1: Framework Selection ─────────────────────── */}
            {step === 1 && (
              <div>
                <div className="flex items-center gap-3 mb-1">
                  <div className="h-10 w-10 rounded-xl bg-[#6366f1]/10 border border-[#6366f1]/20 flex items-center justify-center">
                    <Zap className="h-5 w-5 text-[#6366f1]" />
                  </div>
                  <div>
                    <h2 className="text-lg font-semibold text-white">Install & Choose Framework</h2>
                    <p className="text-sm text-[#71717a]">Which AI agent framework are you using?</p>
                  </div>
                </div>

                <motion.div
                  className="grid grid-cols-2 lg:grid-cols-3 gap-3 mt-6"
                  variants={staggerContainer}
                  initial="initial"
                  animate="animate"
                >
                  {FRAMEWORKS.map((f) => (
                    <motion.button
                      key={f.id}
                      variants={staggerItem}
                      onClick={() => setSelectedFramework(f.id)}
                      className={`relative flex flex-col gap-2 rounded-xl border p-4 transition-all text-left overflow-hidden ${
                        selectedFramework === f.id
                          ? "border-[#6366f1] bg-[#6366f1]/5 shadow-lg shadow-[#6366f1]/10"
                          : "border-[#1e1e2e] hover:border-[#2e2e3e] bg-[#0a0a0f]"
                      }`}
                      {...scaleOnHover}
                    >
                      {selectedFramework === f.id && (
                        <motion.div
                          layoutId="framework-selected"
                          className="absolute inset-0 border-2 border-[#6366f1] rounded-xl"
                          transition={{ type: "spring", stiffness: 300, damping: 30 }}
                        />
                      )}
                      <div className="flex items-center gap-3">
                        <span className="text-2xl">{f.logo}</span>
                        <div>
                          <p className="text-sm font-medium text-white">{f.name}</p>
                          <p className="text-[11px] text-[#52525b] font-mono">chimera-runtime[{f.installExtra}]</p>
                        </div>
                      </div>
                      <p className="text-[11px] text-[#71717a]">{f.description}</p>
                    </motion.button>
                  ))}
                </motion.div>

                <AnimatePresence>
                  {selectedFramework && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: "auto" }}
                      exit={{ opacity: 0, height: 0 }}
                      transition={{ duration: 0.3 }}
                      className="overflow-hidden"
                    >
                      <div className="mt-6 space-y-4">
                        <div>
                          <p className="text-xs text-[#71717a] mb-2">Install command:</p>
                          <TerminalBlock command={installCmd} icon={Terminal} iconColor="#22c55e" />
                        </div>

                        {/* Quick Test Section */}
                        <div className="rounded-xl border border-[#1e1e2e] bg-[#0a0a0f]/60 p-4">
                          <p className="text-xs font-medium text-[#71717a] mb-2 flex items-center gap-1.5">
                            <Zap className="h-3 w-3 text-[#f59e0b]" />
                            Quick Test — verify your API key works
                          </p>
                          <TerminalBlock
                            command={`curl -s -H "Authorization: Bearer $CHIMERA_DASHBOARD_API_KEY" https://api-runtime.chimera-protocol.com/api/v1/health`}
                            icon={Terminal}
                            iconColor="#f59e0b"
                          />
                          <p className="text-[10px] text-[#52525b] mt-2">
                            Expected response: {`{"status": "ok"}`}
                          </p>
                        </div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>

                <div className="mt-6 flex justify-between">
                  <motion.button
                    onClick={() => setStep(0)}
                    className="flex items-center gap-2 text-[#71717a] hover:text-white text-sm font-medium px-4 py-2.5 rounded-lg transition"
                    whileHover={{ x: -3 }}
                  >
                    <ChevronLeft className="h-4 w-4" /> Back
                  </motion.button>
                  <motion.button
                    onClick={() => setStep(2)}
                    disabled={!selectedFramework}
                    className="flex items-center gap-2 bg-[#6366f1] hover:bg-[#5558e6] text-white text-sm font-medium px-5 py-2.5 rounded-lg transition disabled:opacity-30 shadow-lg shadow-[#6366f1]/10"
                    whileHover={selectedFramework ? { scale: 1.03, x: 3 } : {}}
                    whileTap={selectedFramework ? { scale: 0.97 } : {}}
                  >
                    Next <ChevronRight className="h-4 w-4" />
                  </motion.button>
                </div>
              </div>
            )}

            {/* ── Step 2: Policy Selection ────────────────────────── */}
            {step === 2 && (
              <div>
                <div className="flex items-center gap-3 mb-1">
                  <div className="h-10 w-10 rounded-xl bg-[#6366f1]/10 border border-[#6366f1]/20 flex items-center justify-center">
                    <ShieldCheck className="h-5 w-5 text-[#6366f1]" />
                  </div>
                  <div>
                    <h2 className="text-lg font-semibold text-white">Select Policy</h2>
                    <p className="text-sm text-[#71717a]">Choose the enforcement policy for your agent</p>
                  </div>
                </div>

                <div className="mt-6">
                  {policiesLoading ? (
                    <div className="flex justify-center py-12">
                      <Loader2 className="h-6 w-6 animate-spin text-[#6366f1]" />
                    </div>
                  ) : (
                    <motion.div
                      className="space-y-2"
                      variants={staggerContainer}
                      initial="initial"
                      animate="animate"
                    >
                      {policies.map((p) => (
                        <motion.button
                          key={p.filename}
                          variants={staggerItem}
                          onClick={() => setSelectedPolicy(p.filename)}
                          className={`w-full flex items-center justify-between rounded-xl border p-4 transition-all text-left ${
                            selectedPolicy === p.filename
                              ? "border-[#6366f1] bg-[#6366f1]/5 shadow-lg shadow-[#6366f1]/10"
                              : "border-[#1e1e2e] hover:border-[#2e2e3e] bg-[#0a0a0f]"
                          }`}
                          whileHover={{ scale: 1.01, x: 4 }}
                          whileTap={{ scale: 0.99 }}
                        >
                          <div className="flex items-center gap-3">
                            <FileText className="h-4 w-4 text-[#6366f1]" />
                            <div>
                              <p className="text-sm font-medium text-white">{p.filename}</p>
                              <p className="text-xs text-[#71717a]">{p.domain_name}</p>
                            </div>
                          </div>
                          <AnimatePresence>
                            {selectedPolicy === p.filename && (
                              <motion.div
                                initial={{ scale: 0, rotate: -90 }}
                                animate={{ scale: 1, rotate: 0 }}
                                exit={{ scale: 0, rotate: 90 }}
                                transition={{ type: "spring", stiffness: 300 }}
                              >
                                <CheckCircle2 className="h-4 w-4 text-[#6366f1]" />
                              </motion.div>
                            )}
                          </AnimatePresence>
                        </motion.button>
                      ))}
                    </motion.div>
                  )}
                </div>

                {/* Selected policy variables preview */}
                <AnimatePresence>
                  {policyDetail && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: "auto" }}
                      exit={{ opacity: 0, height: 0 }}
                      className="overflow-hidden"
                    >
                      <div className="mt-4 rounded-xl border border-[#1e1e2e] bg-[#0a0a0f] p-4">
                        <p className="text-xs text-[#71717a] mb-3">Policy variables (your agent params must map to these):</p>
                        <motion.div
                          className="flex flex-wrap gap-2"
                          variants={staggerContainer}
                          initial="initial"
                          animate="animate"
                        >
                          {policyDetail.variable_names.map((v) => (
                            <motion.span
                              key={v}
                              variants={staggerItem}
                              className="rounded-lg bg-[#6366f1]/10 border border-[#6366f1]/20 px-2.5 py-1.5 text-xs font-mono text-[#818cf8]"
                            >
                              {v}
                              <span className="text-[#52525b] ml-1">
                                {policyDetail.variable_domains[v] || ""}
                              </span>
                            </motion.span>
                          ))}
                        </motion.div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>

                <div className="mt-6 flex justify-between">
                  <motion.button
                    onClick={() => setStep(1)}
                    className="flex items-center gap-2 text-[#71717a] hover:text-white text-sm font-medium px-4 py-2.5 rounded-lg transition"
                    whileHover={{ x: -3 }}
                  >
                    <ChevronLeft className="h-4 w-4" /> Back
                  </motion.button>
                  <motion.button
                    onClick={() => setStep(3)}
                    disabled={!selectedPolicy}
                    className="flex items-center gap-2 bg-[#6366f1] hover:bg-[#5558e6] text-white text-sm font-medium px-5 py-2.5 rounded-lg transition disabled:opacity-30 shadow-lg shadow-[#6366f1]/10"
                    whileHover={selectedPolicy ? { scale: 1.03, x: 3 } : {}}
                    whileTap={selectedPolicy ? { scale: 0.97 } : {}}
                  >
                    Next <ChevronRight className="h-4 w-4" />
                  </motion.button>
                </div>
              </div>
            )}

            {/* ── Step 3: Variable Mapping ────────────────────────── */}
            {step === 3 && (
              <div>
                <div className="flex items-center gap-3 mb-1">
                  <div className="h-10 w-10 rounded-xl bg-[#6366f1]/10 border border-[#6366f1]/20 flex items-center justify-center">
                    <Plug className="h-5 w-5 text-[#6366f1]" />
                  </div>
                  <div>
                    <h2 className="text-lg font-semibold text-white">Map Parameters</h2>
                    <p className="text-sm text-[#71717a]">Connect your agent&apos;s parameters to policy variables</p>
                  </div>
                </div>

                {/* Flow diagram */}
                <motion.div
                  className="mt-6 rounded-xl border border-[#1e1e2e] bg-[#0a0a0f]/60 p-4"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.2 }}
                >
                  <div className="flex items-center justify-center gap-3 text-xs">
                    <div className="flex items-center gap-2 bg-[#6366f1]/10 border border-[#6366f1]/20 rounded-lg px-3 py-2">
                      <Code2 className="h-3.5 w-3.5 text-[#818cf8]" />
                      <span className="text-[#818cf8] font-medium">Your Params</span>
                    </div>
                    <motion.div
                      animate={{ x: [0, 5, 0] }}
                      transition={{ duration: 1.5, repeat: Infinity }}
                    >
                      <ArrowRight className="h-4 w-4 text-[#6366f1]" />
                    </motion.div>
                    <div className="flex items-center gap-2 bg-[#f59e0b]/10 border border-[#f59e0b]/20 rounded-lg px-3 py-2">
                      <Plug className="h-3.5 w-3.5 text-[#f59e0b]" />
                      <span className="text-[#f59e0b] font-medium">Mapping</span>
                    </div>
                    <motion.div
                      animate={{ x: [0, 5, 0] }}
                      transition={{ duration: 1.5, repeat: Infinity, delay: 0.3 }}
                    >
                      <ArrowRight className="h-4 w-4 text-[#6366f1]" />
                    </motion.div>
                    <div className="flex items-center gap-2 bg-[#22c55e]/10 border border-[#22c55e]/20 rounded-lg px-3 py-2">
                      <ShieldCheck className="h-3.5 w-3.5 text-[#22c55e]" />
                      <span className="text-[#22c55e] font-medium">Policy Variables</span>
                    </div>
                  </div>
                </motion.div>

                <div className="mt-4 flex items-start gap-2 rounded-xl border border-[#6366f1]/20 bg-[#6366f1]/5 px-3 py-2">
                  <AlertCircle className="h-3.5 w-3.5 text-[#818cf8] mt-0.5 shrink-0" />
                  <p className="text-[11px] text-[#818cf8]/80 leading-relaxed">
                    If your tool&apos;s keyword arguments already match the policy variable names (e.g. your function takes <code className="bg-[#6366f1]/10 px-1 rounded">amount</code> and the policy uses <code className="bg-[#6366f1]/10 px-1 rounded">amount</code>), you can skip this step — chimera-runtime will auto-detect them.
                  </p>
                </div>

                {/* Agent tool name */}
                <div className="mt-4 mb-4">
                  <label className="block text-xs text-[#a1a1aa] mb-1.5">Your tool/function name</label>
                  <input
                    type="text"
                    value={agentToolName}
                    onChange={(e) => setAgentToolName(e.target.value)}
                    placeholder="e.g. approve_budget, transfer_funds"
                    className="w-full bg-[#0a0a0f] border border-[#1e1e2e] rounded-lg px-4 py-2.5 text-white placeholder:text-[#52525b] focus:border-[#6366f1] focus:ring-1 focus:ring-[#6366f1] outline-none text-sm font-mono transition"
                  />
                </div>

                {/* Variable mapping table */}
                {policyDetail && (
                  <motion.div
                    className="rounded-xl border border-[#1e1e2e] overflow-hidden"
                    variants={staggerContainer}
                    initial="initial"
                    animate="animate"
                  >
                    <div className="grid grid-cols-[1fr_auto_1fr] gap-0 bg-[#0a0a0f] px-4 py-2.5 border-b border-[#1e1e2e]">
                      <span className="text-xs font-medium text-[#71717a]">Policy Variable</span>
                      <span className="px-4" />
                      <span className="text-xs font-medium text-[#71717a]">Your Parameter Name</span>
                    </div>
                    {policyDetail.variable_names.map((varName, idx) => (
                      <motion.div
                        key={varName}
                        variants={staggerItem}
                        className="grid grid-cols-[1fr_auto_1fr] gap-0 items-center px-4 py-3 border-b border-[#1e1e2e] last:border-0"
                      >
                        <div>
                          <code className="text-sm text-[#818cf8] font-mono">{varName}</code>
                          <span className="ml-2 text-[10px] text-[#52525b]">
                            {policyDetail.variable_domains[varName] || ""}
                          </span>
                        </div>
                        <motion.div
                          animate={{ x: [0, 3, 0] }}
                          transition={{ duration: 1.5, repeat: Infinity, delay: idx * 0.2 }}
                        >
                          <ArrowRight className="h-3.5 w-3.5 text-[#52525b] mx-3" />
                        </motion.div>
                        <input
                          type="text"
                          value={mappings[varName] || ""}
                          onChange={(e) =>
                            setMappings((m) => ({ ...m, [varName]: e.target.value }))
                          }
                          placeholder={varName}
                          className="bg-[#0a0a0f] border border-[#1e1e2e] rounded-lg px-3 py-1.5 text-sm text-white placeholder:text-[#3f3f46] focus:border-[#6366f1] outline-none font-mono transition"
                        />
                      </motion.div>
                    ))}
                  </motion.div>
                )}

                <div className="mt-6 flex justify-between">
                  <motion.button
                    onClick={() => setStep(2)}
                    className="flex items-center gap-2 text-[#71717a] hover:text-white text-sm font-medium px-4 py-2.5 rounded-lg transition"
                    whileHover={{ x: -3 }}
                  >
                    <ChevronLeft className="h-4 w-4" /> Back
                  </motion.button>
                  <motion.button
                    onClick={() => setStep(4)}
                    className="flex items-center gap-2 bg-[#6366f1] hover:bg-[#5558e6] text-white text-sm font-medium px-5 py-2.5 rounded-lg transition shadow-lg shadow-[#6366f1]/10"
                    whileHover={{ scale: 1.03, x: 3 }}
                    whileTap={{ scale: 0.97 }}
                  >
                    Generate Code <ChevronRight className="h-4 w-4" />
                  </motion.button>
                </div>
              </div>
            )}

            {/* ── Step 4: Launch ──────────────────────────────────── */}
            {step === 4 && (
              <div className="relative">
                <SparkleEffect />

                <div className="flex items-center gap-3 mb-1">
                  <motion.div
                    className="h-10 w-10 rounded-xl bg-[#22c55e]/10 border border-[#22c55e]/20 flex items-center justify-center"
                    animate={{ rotate: [0, 5, -5, 0] }}
                    transition={{ duration: 2, repeat: Infinity, repeatDelay: 2 }}
                  >
                    <Rocket className="h-5 w-5 text-[#22c55e]" />
                  </motion.div>
                  <div>
                    <h2 className="text-lg font-semibold text-white">Launch!</h2>
                    <p className="text-sm text-[#71717a]">
                      Your {fw?.name} integration is ready
                    </p>
                  </div>
                </div>

                {/* Complete Setup Checklist */}
                <motion.div
                  className="mt-6 rounded-xl border border-[#1e1e2e] bg-[#0a0a0f]/60 p-5"
                  variants={staggerContainer}
                  initial="initial"
                  animate="animate"
                >
                  <p className="text-xs font-medium text-[#71717a] mb-3 uppercase tracking-wider">Setup Complete</p>
                  {[
                    { label: "API Key created", done: true, icon: Key },
                    { label: `${fw?.name || "Framework"} package installed`, done: true, icon: Zap },
                    { label: `Policy "${selectedPolicy}" selected`, done: true, icon: ShieldCheck },
                    { label: "Parameters mapped", done: true, icon: Plug },
                    { label: "Code ready — paste into your project", done: false, icon: Rocket, highlight: true },
                  ].map((item, idx) => (
                    <motion.div
                      key={idx}
                      variants={staggerItem}
                      className={`flex items-center gap-3 py-2 ${idx < 4 ? "border-b border-[#1e1e2e]/50" : ""}`}
                    >
                      {item.done ? (
                        <motion.div
                          initial={{ scale: 0 }}
                          animate={{ scale: 1 }}
                          transition={{ delay: idx * 0.15, type: "spring" }}
                        >
                          <CheckCircle2 className="h-4 w-4 text-[#22c55e]" />
                        </motion.div>
                      ) : (
                        <motion.div
                          animate={{ scale: [1, 1.2, 1] }}
                          transition={{ duration: 1, repeat: Infinity }}
                        >
                          <Sparkles className="h-4 w-4 text-[#f59e0b]" />
                        </motion.div>
                      )}
                      <span className={`text-sm ${item.highlight ? "text-white font-medium" : "text-[#a1a1aa]"}`}>
                        {item.label}
                      </span>
                    </motion.div>
                  ))}
                </motion.div>

                {/* Install */}
                <div className="mt-6">
                  <p className="text-xs text-[#71717a] mb-2 font-medium">1. Install</p>
                  <TerminalBlock command={installCmd} icon={Terminal} iconColor="#22c55e" />
                </div>

                {/* Code */}
                <div className="mt-4">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-xs text-[#71717a] font-medium">2. Add to your agent</p>
                    <button
                      onClick={() => handleCopyCode(generatedCode)}
                      className="flex items-center gap-1.5 text-xs text-[#71717a] hover:text-white transition"
                    >
                      {copiedCode ? (
                        <>
                          <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }}>
                            <Check className="h-3.5 w-3.5 text-[#22c55e]" />
                          </motion.div>
                          <span className="text-[#22c55e]">Copied!</span>
                        </>
                      ) : (
                        <><Copy className="h-3.5 w-3.5" /> Copy code</>
                      )}
                    </button>
                  </div>
                  <pre className="rounded-xl bg-[#0a0a0f] border border-[#1e1e2e] p-4 overflow-x-auto relative group">
                    {/* Line numbers gutter */}
                    <div className="absolute left-0 top-0 bottom-0 w-10 bg-[#0a0a0f] border-r border-[#1e1e2e]/50 rounded-l-xl flex flex-col items-end pr-2 pt-4 text-[10px] text-[#3f3f46] font-mono leading-[1.625rem] select-none">
                      {generatedCode.split("\n").map((_, i) => (
                        <div key={i}>{i + 1}</div>
                      ))}
                    </div>
                    <code className="text-sm text-[#e4e4e7] font-mono whitespace-pre block pl-8">
                      {generatedCode}
                    </code>
                  </pre>
                </div>

                {/* Cloud Sync Setup (Pro+) */}
                {user && user.tier !== "free" && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 }}
                    className="mt-6 rounded-xl border border-[#6366f1]/20 bg-[#6366f1]/5 p-4"
                  >
                    <p className="text-sm font-medium text-[#818cf8] mb-2 flex items-center gap-2">
                      <Sparkles className="h-4 w-4" />
                      Cloud Sync (Pro)
                    </p>
                    <p className="text-xs text-[#818cf8]/70 mb-3">
                      Set these environment variables so audit logs automatically sync to your dashboard:
                    </p>
                    <div className="space-y-2">
                      <TerminalBlock command={`export CHIMERA_DASHBOARD_API_KEY=${apiKeyDisplay}`} />
                      <TerminalBlock command="export CHIMERA_DASHBOARD_URL=https://api-runtime.chimera-protocol.com/api/v1" />
                    </div>
                  </motion.div>
                )}

                {/* What happens next */}
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.4 }}
                  className="mt-6 rounded-xl border border-[#22c55e]/20 bg-[#22c55e]/5 p-5"
                >
                  <p className="text-sm font-medium text-[#22c55e] mb-3 flex items-center gap-2">
                    <ShieldCheck className="h-4 w-4" />
                    What happens now?
                  </p>
                  <motion.ul
                    className="space-y-2"
                    variants={staggerContainer}
                    initial="initial"
                    animate="animate"
                  >
                    {[
                      <>Every tool call is evaluated against your <code className="bg-[#22c55e]/10 px-1 rounded">{selectedPolicy}</code> policy</>,
                      <>BLOCKED actions raise an exception with violation details</>,
                      <>Every decision is saved locally in <code className="bg-[#22c55e]/10 px-1 rounded">./audit_logs/</code></>,
                      user && user.tier !== "free"
                        ? <>With cloud sync enabled, results appear in this dashboard in real-time</>
                        : <>Upgrade to Pro for real-time cloud sync to this dashboard</>,
                    ].map((text, idx) => (
                      <motion.li
                        key={idx}
                        variants={staggerItem}
                        className="flex items-start gap-2 text-xs text-[#22c55e]/80"
                      >
                        <CheckCircle2 className="h-3.5 w-3.5 mt-0.5 shrink-0" />
                        <span>{text}</span>
                      </motion.li>
                    ))}
                  </motion.ul>
                </motion.div>

                <div className="mt-6 flex justify-between">
                  <motion.button
                    onClick={() => setStep(3)}
                    className="flex items-center gap-2 text-[#71717a] hover:text-white text-sm font-medium px-4 py-2.5 rounded-lg transition"
                    whileHover={{ x: -3 }}
                  >
                    <ChevronLeft className="h-4 w-4" /> Back
                  </motion.button>
                </div>
              </div>
            )}
          </GlassCard>
        </motion.div>
      </AnimatePresence>
    </div>
  );
}
