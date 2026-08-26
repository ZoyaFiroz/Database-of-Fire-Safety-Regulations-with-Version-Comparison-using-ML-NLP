interface Counts {
  unchanged: number;
  modified?: number;
  added: number;
  removed: number;
}

function buildCards(itemLabel: string) {
  return [
    { key: "total", label: `Total ${itemLabel} Evaluated`, accent: "bg-accent-indigo" },
    { key: "modified", label: `Modified ${itemLabel}`, accent: "bg-modified" },
    { key: "added", label: `Added ${itemLabel}`, accent: "bg-added" },
    { key: "removed", label: `Removed ${itemLabel}`, accent: "bg-removed" },
    { key: "unchanged", label: `Unchanged ${itemLabel}`, accent: "bg-unchanged" },
  ] as const;
}

export default function StatsGrid({
  summary,
  itemLabel = "Clauses",
  hideKeys = [],
}: {
  summary?: Counts;
  itemLabel?: string;
  hideKeys?: string[];
}) {
  const s = summary || { unchanged: 0, modified: 0, added: 0, removed: 0 };
  const total = s.unchanged + (s.modified || 0) + s.added + s.removed;
  const values: Record<string, number> = { total, ...s };
  const cards = buildCards(itemLabel).filter((c) => !hideKeys.includes(c.key));

  return (
    <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
      {cards.map((c) => (
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
