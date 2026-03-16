"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import type { ViolationCount } from "@/lib/types";

interface ViolationsChartProps {
  violations: ViolationCount[];
  loading?: boolean;
}

const COLORS = ["#ef4444", "#f97316", "#f59e0b", "#eab308", "#a3a3a3"];

export function ViolationsChart({ violations, loading }: ViolationsChartProps) {
  if (loading) {
    return (
      <Card className="border-[#1e1e2e] bg-[#111119]">
        <CardHeader>
          <CardTitle className="text-white">Top Violations</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64 animate-pulse rounded bg-[#1e1e2e]" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="border-[#1e1e2e] bg-[#111119]">
      <CardHeader>
        <CardTitle className="text-white">Top Violations</CardTitle>
      </CardHeader>
      <CardContent>
        {violations.length === 0 ? (
          <p className="text-center text-[#71717a] py-8">
            No violations detected yet.
          </p>
        ) : (
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={violations} layout="vertical" margin={{ left: 20 }}>
              <XAxis type="number" tick={{ fill: "#71717a", fontSize: 12 }} />
              <YAxis
                type="category"
                dataKey="constraint"
                tick={{ fill: "#e4e4e7", fontSize: 11 }}
                width={140}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#111119",
                  border: "1px solid #1e1e2e",
                  borderRadius: 8,
                  color: "#e4e4e7",
                }}
              />
              <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                {violations.map((_, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={COLORS[index % COLORS.length]}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}
