const CARDS = [
  { key: "total", label: "Total Clauses Evaluated", cls: "total" },
  { key: "modified", label: "Modified Clauses", cls: "modified" },
  { key: "added", label: "Added Clauses", cls: "added" },
  { key: "removed", label: "Removed Clauses", cls: "removed" },
  { key: "unchanged", label: "Unchanged Clauses", cls: "unchanged" },
];

export default function StatsGrid({ summary }) {
  const s = summary || {};
  const total = (s.unchanged || 0) + (s.modified || 0) + (s.added || 0) + (s.removed || 0);
  const values = { total, ...s };

  return (
    <div className="stats-grid">
      {CARDS.map((c) => (
        <div className={`stat-card ${c.cls}`} key={c.key}>
          <div className="stat-label">{c.label}</div>
          <div className="stat-value">{values[c.key] || 0}</div>
        </div>
      ))}
    </div>
  );
}
