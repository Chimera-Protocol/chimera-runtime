"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  FileText,
  ScrollText,
  BarChart3,
  Shield,
  BookOpen,
  Settings,
  ChevronLeft,
  ChevronRight,
  Plug,
  Mail,
} from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { useAuth } from "@/lib/auth";

interface NavItem {
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  tier?: string;
  adminOnly?: boolean;
}

const navItems: NavItem[] = [
  {
    label: "Dashboard",
    href: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    label: "Decisions",
    href: "/decisions",
    icon: ScrollText,
  },
  {
    label: "Policies",
    href: "/policies",
    icon: FileText,
  },
  {
    label: "Analytics",
    href: "/analytics",
    icon: BarChart3,
    tier: "pro",
  },
  {
    label: "Compliance",
    href: "/compliance",
    icon: Shield,
    tier: "enterprise",
  },
  {
    label: "Connect Agent",
    href: "/connect",
    icon: Plug,
  },
  {
    label: "Leads",
    href: "/leads",
    icon: Mail,
    tier: "enterprise",
    adminOnly: true,
  },
  {
    label: "Settings",
    href: "/settings",
    icon: Settings,
  },
  {
    label: "Docs",
    href: "/docs",
    icon: BookOpen,
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);
  const { user } = useAuth();

  const tierOrder: Record<string, number> = { free: 0, pro: 1, enterprise: 2 };
  const userLevel = tierOrder[user?.tier || "free"] ?? 0;

  const visibleItems = navItems.filter((item) => {
    if (item.adminOnly) {
      return user?.tier === "enterprise";
    }
    return true;
  });

  return (
    <aside
      className={cn(
        "fixed left-0 top-0 z-40 flex h-screen flex-col border-r border-[#1e1e2e] bg-[#0d0d14] transition-all duration-300",
        collapsed ? "w-16" : "w-64"
      )}
    >
      {/* Logo */}
      <div className="flex h-16 items-center border-b border-[#1e1e2e] px-4">
        <Link href="/" className="flex items-center gap-2">
          <Shield className="h-6 w-6 text-[#6366f1] shrink-0" />
          {!collapsed && (
            <span className="text-lg font-bold text-white">
              Chimera<span className="text-[#6366f1]">.</span>
            </span>
          )}
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-2 py-4">
        {visibleItems.map((item) => {
          const isActive =
            pathname === item.href || pathname?.startsWith(item.href + "/");
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                isActive
                  ? "bg-[#6366f1]/10 text-[#818cf8]"
                  : "text-[#71717a] hover:bg-[#1e1e2e] hover:text-white"
              )}
            >
              <item.icon className="h-5 w-5 shrink-0" />
              {!collapsed && (
                <>
                  <span className="flex-1">{item.label}</span>
                  {item.tier && (
                    <Badge
                      variant="outline"
                      className={cn(
                        "text-[10px] px-1.5 py-0",
                        item.tier === "pro"
                          ? "border-[#6366f1]/30 text-[#818cf8]"
                          : "border-[#f59e0b]/30 text-[#f59e0b]"
                      )}
                    >
                      {item.tier === "pro" ? "PRO" : "ENT"}
                    </Badge>
                  )}
                </>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Collapse toggle */}
      <div className="border-t border-[#1e1e2e] p-2">
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="flex w-full items-center justify-center rounded-lg p-2 text-[#71717a] hover:bg-[#1e1e2e] hover:text-white transition-colors"
        >
          {collapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <ChevronLeft className="h-4 w-4" />
          )}
        </button>
      </div>
    </aside>
  );
}
