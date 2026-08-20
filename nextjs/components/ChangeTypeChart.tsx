"use client";

import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import type { ComparisonSummary } from "@/lib/types";

const COLORS: Record<string, string> = {
  Unchanged: "#6b7280",
  Modified: "#f59e0b",
  Added: "#10b981",
  Removed: "#ef4444",
};

export default function ChangeTypeChart({ summary }: { summary?: ComparisonSummary }) {
  const s = summary || { unchanged: 0, modified: 0, added: 0, removed: 0 };
  const data = [
    { name: "Unchanged", value: s.unchanged },
    { name: "Modified", value: s.modified },
    { name: "Added", value: s.added },
    { name: "Removed", value: s.removed },
  ].filter((d) => d.value > 0);

  if (data.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center text-sm text-gray-500">
        No data to chart yet.
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={260}>
      <PieChart>
        <Pie
          data={data}
          dataKey="value"
          nameKey="name"
          innerRadius={55}
          outerRadius={90}
          paddingAngle={2}
        >
          {data.map((d) => (
            <Cell key={d.name} fill={COLORS[d.name]} stroke="#090d16" strokeWidth={2} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{
            background: "#0f172acc",
            border: "1px solid rgba(255,255,255,0.1)",
            borderRadius: 8,
            color: "#f3f4f6",
          }}
        />
        <Legend
          verticalAlign="bottom"
          height={28}
          formatter={(value) => <span style={{ color: "#9ca3af", fontSize: 12 }}>{value}</span>}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}
