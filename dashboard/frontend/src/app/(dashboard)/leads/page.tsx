"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Mail,
  Users,
  Building2,
  MessageSquare,
  Loader2,
  Shield,
  Clock,
  ArrowUpRight,
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

export default function LeadsPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [leads, setLeads] = useState<LeadEntry[]>([]);
  const [adminStats, setAdminStats] = useState<AdminStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (user && user.tier !== "enterprise") {
      router.push("/dashboard");
      return;
    }
    if (user?.tier === "enterprise") {
      fetchData();
    }
  }, [user, router]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [leadsData, statsData] = await Promise.all([
        api.getLeads(),
        api.getAdminStats(),
      ]);
      setLeads(leadsData.leads);
      setAdminStats(statsData);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  if (!user || user.tier !== "enterprise") {
    return null;
  }

  const planColor = (plan: string) => {
    switch (plan?.toLowerCase()) {
      case "enterprise":
        return "border-[#f59e0b]/30 text-[#f59e0b]";
      case "pro":
        return "border-[#6366f1]/30 text-[#818cf8]";
      default:
        return "border-[#71717a]/30 text-[#71717a]";
    }
  };

  const formatDate = (dateStr: string) => {
    const d = new Date(dateStr);
    return d.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Leads & Users</h1>
        <p className="mt-1 text-sm text-[#71717a]">
          Sales inquiries and user registrations
        </p>
      </div>

      {loading ? (
        <div className="flex justify-center py-16">
          <Loader2 className="h-8 w-8 animate-spin text-[#6366f1]" />
        </div>
      ) : (
        <>
          {/* Stats Cards */}
          <div className="grid gap-4 sm:grid-cols-4">
            <Card className="border-[#1e1e2e] bg-[#111119]">
              <CardContent className="p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Mail className="h-4 w-4 text-[#6366f1]" />
                  <span className="text-xs text-[#71717a]">Total Leads</span>
                </div>
                <p className="text-3xl font-bold text-white">
                  {adminStats?.total_leads ?? 0}
                </p>
              </CardContent>
            </Card>

            <Card className="border-[#1e1e2e] bg-[#111119]">
              <CardContent className="p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Users className="h-4 w-4 text-[#22c55e]" />
                  <span className="text-xs text-[#71717a]">Total Users</span>
                </div>
                <p className="text-3xl font-bold text-white">
                  {adminStats?.total_users ?? 0}
                </p>
              </CardContent>
            </Card>

            <Card className="border-[#1e1e2e] bg-[#111119]">
              <CardContent className="p-4">
                <div className="flex items-center gap-2 mb-2">
                  <ArrowUpRight className="h-4 w-4 text-[#f59e0b]" />
                  <span className="text-xs text-[#71717a]">Pro Inquiries</span>
                </div>
                <p className="text-3xl font-bold text-white">
                  {leads.filter((l) => l.plan?.toLowerCase() === "pro").length}
                </p>
              </CardContent>
            </Card>

            <Card className="border-[#1e1e2e] bg-[#111119]">
              <CardContent className="p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Shield className="h-4 w-4 text-[#f59e0b]" />
                  <span className="text-xs text-[#71717a]">
                    Enterprise Inquiries
                  </span>
                </div>
                <p className="text-3xl font-bold text-white">
                  {leads.filter((l) => l.plan?.toLowerCase() === "enterprise").length}
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Tier Distribution */}
          {adminStats && (
            <Card className="border-[#1e1e2e] bg-[#111119]">
              <CardHeader className="pb-3">
                <CardTitle className="text-white text-sm flex items-center gap-2">
                  <Users className="h-4 w-4 text-[#6366f1]" />
                  User Tier Distribution
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-4">
                  {Object.entries(adminStats.tier_distribution).map(
                    ([tier, count]) => (
                      <div
                        key={tier}
                        className="flex items-center gap-2 rounded-lg border border-[#1e1e2e] bg-[#0a0a0f] px-4 py-3"
                      >
                        <Badge
                          variant="outline"
                          className={planColor(tier)}
                        >
                          {tier.toUpperCase()}
                        </Badge>
                        <span className="text-lg font-semibold text-white">
                          {count}
                        </span>
                      </div>
                    )
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Leads Table */}
          <Card className="border-[#1e1e2e] bg-[#111119]">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <MessageSquare className="h-5 w-5 text-[#6366f1]" />
                Sales Inquiries
                <Badge
                  variant="outline"
                  className="border-[#6366f1]/30 text-[#818cf8] text-[10px] ml-2"
                >
                  {leads.length}
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {leads.length === 0 ? (
                <div className="text-center py-12">
                  <Mail className="h-10 w-10 text-[#52525b] mx-auto mb-3" />
                  <p className="text-sm text-[#71717a]">
                    No inquiries yet. They will appear here when someone submits
                    the contact form.
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {leads.map((lead) => (
                    <div
                      key={lead.id}
                      className="rounded-lg border border-[#1e1e2e] bg-[#0a0a0f] p-4 hover:border-[#6366f1]/30 transition"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-3">
                          <div className="h-9 w-9 rounded-full bg-[#6366f1]/10 flex items-center justify-center shrink-0">
                            <Mail className="h-4 w-4 text-[#6366f1]" />
                          </div>
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="text-sm font-medium text-white">
                                {lead.name || "—"}
                              </span>
                              {lead.plan && (
                                <Badge
                                  variant="outline"
                                  className={`text-[10px] ${planColor(lead.plan)}`}
                                >
                                  {lead.plan.toUpperCase()}
                                </Badge>
                              )}
                            </div>
                            <div className="flex items-center gap-3 mt-0.5">
                              <span className="text-xs text-[#a1a1aa]">
                                {lead.email}
                              </span>
                              {lead.company && (
                                <span className="flex items-center gap-1 text-xs text-[#71717a]">
                                  <Building2 className="h-3 w-3" />
                                  {lead.company}
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                        <span className="flex items-center gap-1 text-xs text-[#52525b] shrink-0">
                          <Clock className="h-3 w-3" />
                          {formatDate(lead.created_at)}
                        </span>
                      </div>
                      {lead.message && (
                        <div className="mt-3 ml-12 rounded-lg bg-[#111119] border border-[#1e1e2e] p-3">
                          <p className="text-sm text-[#a1a1aa] leading-relaxed">
                            {lead.message}
                          </p>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Recent Users */}
          {adminStats && adminStats.recent_users.length > 0 && (
            <Card className="border-[#1e1e2e] bg-[#111119]">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2 text-sm">
                  <Users className="h-4 w-4 text-[#22c55e]" />
                  Recent Registrations
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {adminStats.recent_users.map((u) => (
                    <div
                      key={u.id}
                      className="flex items-center justify-between rounded-lg border border-[#1e1e2e] bg-[#0a0a0f] px-4 py-3"
                    >
                      <div className="flex items-center gap-3">
                        <div className="h-8 w-8 rounded-full bg-[#22c55e]/10 flex items-center justify-center">
                          <Users className="h-3.5 w-3.5 text-[#22c55e]" />
                        </div>
                        <div>
                          <span className="text-sm text-white">{u.email}</span>
                          <div className="flex items-center gap-2 mt-0.5">
                            <Badge
                              variant="outline"
                              className={`text-[9px] ${planColor(u.tier)}`}
                            >
                              {u.tier.toUpperCase()}
                            </Badge>
                            {u.last_login && (
                              <span className="text-xs text-[#52525b]">
                                Last login: {new Date(u.last_login).toLocaleDateString()}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                      <span className="text-xs text-[#52525b]">
                        {formatDate(u.created_at)}
                      </span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
