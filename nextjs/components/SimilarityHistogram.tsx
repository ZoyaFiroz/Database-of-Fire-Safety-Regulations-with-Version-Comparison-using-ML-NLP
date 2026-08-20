"use client";

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { ComparisonChange } from "@/lib/types";

const BUCKET_COUNT = 10;

export default function SimilarityHistogram({ changes }: { changes: ComparisonChange[] }) {
  // Only "unchanged"/"modified" rows have a meaningful paired similarity score -
  // "added"/"removed" are always ~0 by construction and would just spike the
  // first bucket without telling you anything about match confidence.
  const scored = changes.filter((c) => c.change_type === "unchanged" || c.change_type === "modified");

  const buckets = Array.from({ length: BUCKET_COUNT }, (_, i) => ({
    range: `${(i / BUCKET_COUNT).toFixed(1)}–${((i + 1) / BUCKET_COUNT).toFixed(1)}`,
    count: 0,
  }));

  for (const c of scored) {
    const idx = Math.min(BUCKET_COUNT - 1, Math.floor(c.similarity * BUCKET_COUNT));
    buckets[Math.max(0, idx)].count += 1;
  }

  if (scored.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center text-sm text-gray-500">
        No matched-pair similarity scores to chart yet.
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={buckets} margin={{ top: 8, right: 12, left: -16, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" vertical={false} />
        <XAxis
          dataKey="range"
          tick={{ fill: "#9ca3af", fontSize: 10 }}
          interval={1}
          angle={-35}
          textAnchor="end"
          height={40}
        />
        <YAxis tick={{ fill: "#9ca3af", fontSize: 11 }} allowDecimals={false} />
        <Tooltip
          cursor={{ fill: "rgba(99,102,241,0.1)" }}
          contentStyle={{
            background: "#0f172acc",
            border: "1px solid rgba(255,255,255,0.1)",
            borderRadius: 8,
            color: "#f3f4f6",
          }}
        />
        <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
