import type { ComparisonSummary } from "@/lib/types";

const CARDS: { key: keyof ComparisonSummary | "total"; label: string; accent: string }[] = [
  { key: "total", label: "Total Clauses Evaluated", accent: "bg-accent-indigo" },
  { key: "modified", label: "Modified Clauses", accent: "bg-modified" },
  { key: "added", label: "Added Clauses", accent: "bg-added" },
  { key: "removed", label: "Removed Clauses", accent: "bg-removed" },
  { key: "unchanged", label: "Unchanged Clauses", accent: "bg-unchanged" },
];

export default function StatsGrid({ summary }: { summary?: ComparisonSummary }) {
  const s = summary || { unchanged: 0, modified: 0, added: 0, removed: 0 };
  const total = s.unchanged + s.modified + s.added + s.removed;
  const values: Record<string, number> = { total, ...s };

  return (
    <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
      {CARDS.map((c) => (
        <div
          key={c.key}
          className="relative overflow-hidden rounded-xl border border-white/10 bg-white/[0.03] p-4 backdrop-blur-md"
        >
          <div className={`absolute inset-x-0 top-0 h-[3px] ${c.accent}`} />
          <div className="text-xs font-medium text-gray-400">{c.label}</div>
          <div className="mt-1 text-2xl font-bold">{values[c.key] || 0}</div>
        </div>
      ))}
    </div>
  );
}
