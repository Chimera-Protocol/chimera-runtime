"use client";

import { useAuth } from "@/lib/auth";
import { Lock } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import Link from "next/link";

interface ProGateProps {
  children: React.ReactNode;
  requiredTier?: "pro" | "enterprise";
  feature?: string;
}

export function useIsPro(): boolean {
  const { user } = useAuth();
  return user?.tier === "pro" || user?.tier === "enterprise";
}

export function ProGate({
  children,
  requiredTier = "pro",
  feature,
}: ProGateProps) {
  const { user } = useAuth();
  const tierOrder = { free: 0, pro: 1, enterprise: 2 };
  const userLevel = tierOrder[user?.tier || "free"];
  const requiredLevel = tierOrder[requiredTier];

  if (userLevel >= requiredLevel) {
    return <>{children}</>;
  }

  return (
    <div className="relative">
      <div className="pointer-events-none select-none blur-[3px] opacity-50">
        {children}
      </div>
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="rounded-xl border border-[#6366f1]/20 bg-[#0a0a0f]/90 px-6 py-4 text-center backdrop-blur-sm">
          <Lock className="mx-auto mb-2 h-5 w-5 text-[#818cf8]" />
          <p className="text-sm font-medium text-white">
            {feature || "This feature"} requires{" "}
            <Badge
              variant="outline"
              className="border-[#6366f1]/30 text-[#818cf8] ml-1"
            >
              {requiredTier === "enterprise" ? "ENTERPRISE" : "PRO"}
            </Badge>
          </p>
          <Link
            href="/contact"
            className="mt-2 inline-block text-xs text-[#6366f1] hover:text-[#818cf8] transition-colors"
          >
            Upgrade now &rarr;
          </Link>
        </div>
      </div>
    </div>
  );
}
