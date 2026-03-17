"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { analytics } from "@/lib/analytics";
import { ProGate } from "@/components/pro-gate";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import {
  Settings,
  Key,
  Plus,
  Copy,
  Trash2,
  Loader2,
  Check,
  User,
  Shield,
  Clock,
  Pause,
  Play,
  Bot,
  Users,
  Mail,
  BarChart3,
} from "lucide-react";

interface AdminStats {
  total_users: number;
  tier_distribution: Record<string, number>;
  total_leads: number;
  recent_users: Array<{
    id: number;
    email: string;
    tier: string;
    created_at: string;
    last_login: string | null;
  }>;
}

interface LeadEntry {
  id: number;
  email: string;
  name: string;
  company: string;
  plan: string;
  message: string;
  created_at: string;
}

interface AgentWithStatus {
  name: string;
  total: number;
  allowed: number;
  blocked: number;
  avg_latency_ms: number;
  halted: boolean;
  halted_at: string | null;
  halt_reason: string | null;
}

interface ApiKey {
  id: number;
  key_prefix: string;
  name: string;
  created_at: string;
  last_used: string | null;
  revoked: boolean;
}

export default function SettingsPage() {
  const { user } = useAuth();
  const [keys, setKeys] = useState<ApiKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [newKeyName, setNewKeyName] = useState("");
  const [newRawKey, setNewRawKey] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [revoking, setRevoking] = useState<number | null>(null);

  // Agent state
  const [agentsList, setAgentsList] = useState<AgentWithStatus[]>([]);
  const [agentsLoading, setAgentsLoading] = useState(true);
  const [togglingAgent, setTogglingAgent] = useState<string | null>(null);

  // Password change state
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [changingPassword, setChangingPassword] = useState(false);
  const [passwordMessage, setPasswordMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  // Admin state
  const [adminStats, setAdminStats] = useState<AdminStats | null>(null);
  const [adminLoading, setAdminLoading] = useState(false);
  const [leads, setLeads] = useState<LeadEntry[]>([]);
  const [showLeads, setShowLeads] = useState(false);

  useEffect(() => {
    fetchKeys();
    fetchAgents();
    if (user?.tier === "enterprise") {
      fetchAdminStats();
    }
  }, [user]);

  const fetchKeys = async () => {
    try {
      const data = await api.getApiKeys();
      setKeys(data.keys);
    } catch {
      // Pro tier required — will show ProGate
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    if (!newKeyName.trim()) return;
    setCreating(true);
    try {
      const result = await api.createApiKey(newKeyName.trim());
      setNewRawKey(result.key);
      analytics.licenseGenerate();
      setNewKeyName("");
      await fetchKeys();
    } catch (err) {
      console.error("Failed to create API key:", err);
    } finally {
      setCreating(false);
    }
  };

  const handleCopy = async () => {
    if (!newRawKey) return;
    await navigator.clipboard.writeText(newRawKey);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleRevoke = async (keyId: number) => {
    setRevoking(keyId);
    try {
      await api.revokeApiKey(keyId);
      await fetchKeys();
    } catch (err) {
      console.error("Failed to revoke key:", err);
    } finally {
      setRevoking(null);
    }
  };

  const fetchAgents = async () => {
    try {
      const tier = user?.tier || "free";
      const data = await api.getAgentsFull(tier);
      setAgentsList(data.agents);
    } catch {
      // ignore
    } finally {
      setAgentsLoading(false);
    }
  };

  const handleToggleAgent = async (agentName: string, halted: boolean) => {
    setTogglingAgent(agentName);
    try {
      if (halted) {
        await api.resumeAgent(agentName);
      } else {
        await api.haltAgent(agentName);
      }
      await fetchAgents();
    } catch (err) {
      console.error("Failed to toggle agent:", err);
    } finally {
      setTogglingAgent(null);
    }
  };

  const fetchAdminStats = async () => {
    setAdminLoading(true);
    try {
      const data = await api.getAdminStats();
      setAdminStats(data);
    } catch {
      // Not enterprise — ignore
    } finally {
      setAdminLoading(false);
    }
  };

  const fetchLeads = async () => {
    try {
      const data = await api.getLeads();
      setLeads(data.leads);
      setShowLeads(true);
    } catch {
      // ignore
    }
  };

  const handleChangePassword = async () => {
    if (newPassword !== confirmPassword) {
      setPasswordMessage({ type: "error", text: "Passwords do not match" });
      return;
    }
    if (newPassword.length < 6) {
      setPasswordMessage({ type: "error", text: "Password must be at least 6 characters" });
      return;
    }
    setChangingPassword(true);
    setPasswordMessage(null);
    try {
      await api.auth.changePassword(currentPassword, newPassword);
      setPasswordMessage({ type: "success", text: "Password changed successfully" });
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch {
      setPasswordMessage({ type: "error", text: "Current password is incorrect" });
    } finally {
      setChangingPassword(false);
    }
  };

  const activeKeys = keys.filter((k) => !k.revoked);
  const revokedKeys = keys.filter((k) => k.revoked);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Settings</h1>
        <p className="mt-1 text-sm text-[#71717a]">
          Manage your account and API keys
        </p>
      </div>

      {/* Account Info */}
      <Card className="border-[#1e1e2e] bg-[#111119]">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <User className="h-5 w-5 text-[#6366f1]" />
            Account
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 sm:grid-cols-3">
            <div className="rounded-lg border border-[#1e1e2e] bg-[#0a0a0f] p-3">
              <p className="text-xs text-[#71717a]">Email</p>
              <p className="mt-1 text-sm text-white">{user?.email || "—"}</p>
            </div>
            <div className="rounded-lg border border-[#1e1e2e] bg-[#0a0a0f] p-3">
              <p className="text-xs text-[#71717a]">Tier</p>
              <div className="mt-1 flex items-center gap-2">
                <Badge
                  variant="outline"
                  className={
                    user?.tier === "enterprise"
                      ? "border-[#f59e0b]/30 text-[#f59e0b]"
                      : user?.tier === "pro"
                        ? "border-[#6366f1]/30 text-[#818cf8]"
                        : "border-[#71717a]/30 text-[#71717a]"
                  }
                >
                  {(user?.tier || "free").toUpperCase()}
                </Badge>
              </div>
            </div>
            <div className="rounded-lg border border-[#1e1e2e] bg-[#0a0a0f] p-3">
              <p className="text-xs text-[#71717a]">Member Since</p>
              <p className="mt-1 text-sm text-white">
                {user?.created_at
                  ? new Date(user.created_at).toLocaleDateString()
                  : "—"}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Change Password */}
      <Card className="border-[#1e1e2e] bg-[#111119]">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Shield className="h-5 w-5 text-[#6366f1]" />
            Change Password
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-3 sm:grid-cols-3">
            <div>
              <label className="text-xs text-[#71717a] mb-1 block">Current Password</label>
              <input
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full bg-[#0a0a0f] border border-[#1e1e2e] rounded-lg px-4 py-2 text-white placeholder:text-[#52525b] focus:border-[#6366f1] focus:ring-1 focus:ring-[#6366f1] outline-none text-sm"
              />
            </div>
            <div>
              <label className="text-xs text-[#71717a] mb-1 block">New Password</label>
              <input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full bg-[#0a0a0f] border border-[#1e1e2e] rounded-lg px-4 py-2 text-white placeholder:text-[#52525b] focus:border-[#6366f1] focus:ring-1 focus:ring-[#6366f1] outline-none text-sm"
              />
            </div>
            <div>
              <label className="text-xs text-[#71717a] mb-1 block">Confirm Password</label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="••••••••"
                onKeyDown={(e) => e.key === "Enter" && handleChangePassword()}
                className="w-full bg-[#0a0a0f] border border-[#1e1e2e] rounded-lg px-4 py-2 text-white placeholder:text-[#52525b] focus:border-[#6366f1] focus:ring-1 focus:ring-[#6366f1] outline-none text-sm"
              />
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Button
              onClick={handleChangePassword}
              disabled={changingPassword || !currentPassword || !newPassword || !confirmPassword}
              className="bg-[#6366f1] hover:bg-[#5558e6] text-white"
            >
              {changingPassword ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Key className="mr-2 h-4 w-4" />
              )}
              Update Password
            </Button>
            {passwordMessage && (
              <span className={`text-sm ${passwordMessage.type === "success" ? "text-[#22c55e]" : "text-[#ef4444]"}`}>
                {passwordMessage.text}
              </span>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Admin Panel — Enterprise only */}
      {user?.tier === "enterprise" && (
        <Card className="border-[#f59e0b]/20 bg-[#111119]">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-[#f59e0b]" />
              Admin Panel
              <Badge variant="outline" className="border-[#f59e0b]/30 text-[#f59e0b] text-[10px] ml-2">
                ENTERPRISE
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {adminLoading ? (
              <div className="flex justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-[#f59e0b]" />
              </div>
            ) : adminStats ? (
              <div className="space-y-4">
                {/* Stats Grid */}
                <div className="grid gap-3 sm:grid-cols-3">
                  <div className="rounded-lg border border-[#1e1e2e] bg-[#0a0a0f] p-4">
                    <div className="flex items-center gap-2 mb-1">
                      <Users className="h-4 w-4 text-[#6366f1]" />
                      <span className="text-xs text-[#71717a]">Total Users</span>
                    </div>
                    <p className="text-2xl font-bold text-white">{adminStats.total_users}</p>
                  </div>
                  <div className="rounded-lg border border-[#1e1e2e] bg-[#0a0a0f] p-4">
                    <div className="flex items-center gap-2 mb-1">
                      <Mail className="h-4 w-4 text-[#22c55e]" />
                      <span className="text-xs text-[#71717a]">Sales Leads</span>
                    </div>
                    <p className="text-2xl font-bold text-white">{adminStats.total_leads}</p>
                    {adminStats.total_leads > 0 && !showLeads && (
                      <button
                        onClick={fetchLeads}
                        className="mt-1 text-xs text-[#6366f1] hover:text-[#818cf8] transition"
                      >
                        View leads
                      </button>
                    )}
                  </div>
                  <div className="rounded-lg border border-[#1e1e2e] bg-[#0a0a0f] p-4">
                    <div className="flex items-center gap-2 mb-1">
                      <Shield className="h-4 w-4 text-[#f59e0b]" />
                      <span className="text-xs text-[#71717a]">Tier Distribution</span>
                    </div>
                    <div className="flex items-center gap-2 mt-1">
                      {Object.entries(adminStats.tier_distribution).map(([tier, count]) => (
                        <Badge
                          key={tier}
                          variant="outline"
                          className={
                            tier === "enterprise"
                              ? "border-[#f59e0b]/30 text-[#f59e0b]"
                              : tier === "pro"
                                ? "border-[#6366f1]/30 text-[#818cf8]"
                                : "border-[#71717a]/30 text-[#71717a]"
                          }
                        >
                          {tier}: {count}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Recent Users */}
                <div>
                  <h3 className="text-sm font-medium text-[#a1a1aa] mb-2">Recent Registrations</h3>
                  <div className="space-y-1">
                    {adminStats.recent_users.map((u) => (
                      <div key={u.id} className="flex items-center justify-between rounded-lg border border-[#1e1e2e] bg-[#0a0a0f] px-3 py-2">
                        <div className="flex items-center gap-2">
                          <User className="h-3.5 w-3.5 text-[#71717a]" />
                          <span className="text-sm text-white">{u.email}</span>
                          <Badge
                            variant="outline"
                            className={
                              u.tier === "enterprise"
                                ? "border-[#f59e0b]/30 text-[#f59e0b] text-[9px]"
                                : u.tier === "pro"
                                  ? "border-[#6366f1]/30 text-[#818cf8] text-[9px]"
                                  : "border-[#71717a]/30 text-[#71717a] text-[9px]"
                            }
                          >
                            {u.tier.toUpperCase()}
                          </Badge>
                        </div>
                        <span className="text-xs text-[#52525b]">
                          {new Date(u.created_at).toLocaleDateString()}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Leads List */}
                {showLeads && leads.length > 0 && (
                  <div>
                    <h3 className="text-sm font-medium text-[#a1a1aa] mb-2">Sales Inquiries</h3>
                    <div className="space-y-1">
                      {leads.map((lead) => (
                        <div key={lead.id} className="rounded-lg border border-[#1e1e2e] bg-[#0a0a0f] px-3 py-2">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <Mail className="h-3.5 w-3.5 text-[#6366f1]" />
                              <span className="text-sm text-white">{lead.email}</span>
                              {lead.name && <span className="text-xs text-[#71717a]">({lead.name})</span>}
                              {lead.plan && (
                                <Badge variant="outline" className="text-[9px] border-[#6366f1]/30 text-[#818cf8]">
                                  {lead.plan.toUpperCase()}
                                </Badge>
                              )}
                            </div>
                            <span className="text-xs text-[#52525b]">
                              {new Date(lead.created_at).toLocaleDateString()}
                            </span>
                          </div>
                          {lead.company && <p className="text-xs text-[#71717a] mt-1">Company: {lead.company}</p>}
                          {lead.message && <p className="text-xs text-[#71717a] mt-1">{lead.message}</p>}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-sm text-[#71717a] py-4">Unable to load admin stats.</p>
            )}
          </CardContent>
        </Card>
      )}

      {/* API Keys — Pro+ */}
      <ProGate feature="API Keys">
        <Card className="border-[#1e1e2e] bg-[#111119]">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-white flex items-center gap-2">
              <Key className="h-5 w-5 text-[#6366f1]" />
              API Keys
            </CardTitle>
            <Badge variant="outline" className="border-[#6366f1]/30 text-[#818cf8]">
              {activeKeys.length}/5 active
            </Badge>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-[#71717a]">
              Use API keys for programmatic access to the Chimera Compliance API.
            </p>

            {/* Create New Key */}
            <div className="flex gap-2">
              <input
                type="text"
                value={newKeyName}
                onChange={(e) => setNewKeyName(e.target.value)}
                placeholder="Key name (e.g., Production, CI/CD)"
                className="flex-1 bg-[#0a0a0f] border border-[#1e1e2e] rounded-lg px-4 py-2 text-white placeholder:text-[#52525b] focus:border-[#6366f1] focus:ring-1 focus:ring-[#6366f1] outline-none text-sm"
                onKeyDown={(e) => e.key === "Enter" && handleCreate()}
              />
              <Button
                onClick={handleCreate}
                disabled={creating || !newKeyName.trim() || activeKeys.length >= 5}
                className="bg-[#6366f1] hover:bg-[#5558e6] text-white"
              >
                {creating ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Plus className="mr-2 h-4 w-4" />
                )}
                Create Key
              </Button>
            </div>

            {/* Newly Created Key Banner */}
            {newRawKey && (
              <div className="rounded-lg border border-[#22c55e]/30 bg-[#22c55e]/5 p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-[#22c55e]">
                    New API Key Created
                  </span>
                  <span className="text-xs text-[#71717a]">
                    Copy now — it won&apos;t be shown again
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <code className="flex-1 rounded bg-black/30 px-3 py-2 font-mono text-sm text-[#e4e4e7] break-all">
                    {newRawKey}
                  </code>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleCopy}
                    className="border-[#22c55e]/30 text-[#22c55e] hover:bg-[#22c55e]/10 shrink-0"
                  >
                    {copied ? (
                      <Check className="h-4 w-4" />
                    ) : (
                      <Copy className="h-4 w-4" />
                    )}
                  </Button>
                </div>
              </div>
            )}

            <Separator className="bg-[#1e1e2e]" />

            {/* Active Keys */}
            {loading ? (
              <div className="flex justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-[#6366f1]" />
              </div>
            ) : activeKeys.length === 0 ? (
              <p className="text-center py-8 text-sm text-[#71717a]">
                No active API keys. Create one to get started.
              </p>
            ) : (
              <div className="space-y-2">
                {activeKeys.map((k) => (
                  <div
                    key={k.id}
                    className="flex items-center justify-between rounded-lg border border-[#1e1e2e] bg-[#0a0a0f] px-4 py-3"
                  >
                    <div className="flex items-center gap-3">
                      <Key className="h-4 w-4 text-[#6366f1]" />
                      <div>
                        <p className="text-sm font-medium text-white">{k.name}</p>
                        <div className="flex items-center gap-3 mt-0.5">
                          <code className="text-xs text-[#71717a] font-mono">
                            {k.key_prefix}
                          </code>
                          <span className="flex items-center gap-1 text-xs text-[#71717a]">
                            <Clock className="h-3 w-3" />
                            {new Date(k.created_at).toLocaleDateString()}
                          </span>
                          {k.last_used && (
                            <span className="text-xs text-[#71717a]">
                              Last used: {new Date(k.last_used).toLocaleDateString()}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleRevoke(k.id)}
                      disabled={revoking === k.id}
                      className="border-[#ef4444]/30 text-[#ef4444] hover:bg-[#ef4444]/10"
                    >
                      {revoking === k.id ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Trash2 className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                ))}
              </div>
            )}

            {/* Revoked Keys */}
            {revokedKeys.length > 0 && (
              <>
                <Separator className="bg-[#1e1e2e]" />
                <details className="group">
                  <summary className="cursor-pointer text-sm text-[#71717a] hover:text-white transition-colors">
                    {revokedKeys.length} revoked key{revokedKeys.length !== 1 ? "s" : ""}
                  </summary>
                  <div className="mt-2 space-y-2">
                    {revokedKeys.map((k) => (
                      <div
                        key={k.id}
                        className="flex items-center gap-3 rounded-lg border border-[#1e1e2e] bg-[#0a0a0f] px-4 py-3 opacity-50"
                      >
                        <Key className="h-4 w-4 text-[#71717a]" />
                        <div>
                          <p className="text-sm text-[#71717a] line-through">{k.name}</p>
                          <code className="text-xs text-[#52525b] font-mono">{k.key_prefix}</code>
                        </div>
                        <Badge variant="outline" className="ml-auto border-[#ef4444]/30 text-[#ef4444] text-[10px]">
                          REVOKED
                        </Badge>
                      </div>
                    ))}
                  </div>
                </details>
              </>
            )}
          </CardContent>
        </Card>
      </ProGate>

      {/* Agent Control — Pro+ (Art. 14 Human Oversight) */}
      <ProGate feature="Agent Control (Art. 14)">
        <Card className="border-[#1e1e2e] bg-[#111119]">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Bot className="h-5 w-5 text-[#6366f1]" />
              Agent Control
              <Badge variant="outline" className="border-[#22c55e]/30 text-[#22c55e] text-[10px] ml-2">
                Art. 14
              </Badge>
            </CardTitle>
            <p className="text-sm text-[#71717a]">
              EU AI Act Article 14 — Human oversight: halt or resume AI agents
            </p>
          </CardHeader>
          <CardContent>
            {agentsLoading ? (
              <div className="flex justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-[#6366f1]" />
              </div>
            ) : agentsList.length === 0 ? (
              <p className="text-center py-8 text-sm text-[#71717a]">
                No agents found. Run some decisions to see agents here.
              </p>
            ) : (
              <div className="space-y-3">
                {agentsList.map((agent) => (
                  <div
                    key={agent.name}
                    className={`flex items-center justify-between rounded-lg border px-4 py-3 ${
                      agent.halted
                        ? "border-[#ef4444]/30 bg-[#ef4444]/5"
                        : "border-[#1e1e2e] bg-[#0a0a0f]"
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div className={`h-2.5 w-2.5 rounded-full ${agent.halted ? "bg-[#ef4444]" : "bg-[#22c55e]"}`} />
                      <div>
                        <p className="text-sm font-medium text-white">{agent.name}</p>
                        <div className="flex items-center gap-3 mt-0.5 text-xs text-[#71717a]">
                          <span>{agent.total} decisions</span>
                          <span>{agent.blocked} blocked</span>
                          <span>{Math.round(agent.avg_latency_ms)}ms avg</span>
                          {agent.halted && agent.halted_at && (
                            <span className="text-[#ef4444]">
                              Halted {new Date(agent.halted_at).toLocaleString()}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleToggleAgent(agent.name, agent.halted)}
                      disabled={togglingAgent === agent.name}
                      className={
                        agent.halted
                          ? "border-[#22c55e]/30 text-[#22c55e] hover:bg-[#22c55e]/10"
                          : "border-[#ef4444]/30 text-[#ef4444] hover:bg-[#ef4444]/10"
                      }
                    >
                      {togglingAgent === agent.name ? (
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      ) : agent.halted ? (
                        <Play className="mr-2 h-4 w-4" />
                      ) : (
                        <Pause className="mr-2 h-4 w-4" />
                      )}
                      {agent.halted ? "Resume" : "Halt"}
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </ProGate>
    </div>
  );
}
