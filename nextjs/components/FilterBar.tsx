"use client";

import type { ChangeType } from "@/lib/types";

const FILTERS: (ChangeType | "all")[] = ["all", "modified", "added", "removed", "unchanged"];

export default function FilterBar({
  activeFilter,
  onFilterChange,
  searchTerm,
  onSearchChange,
}: {
  activeFilter: ChangeType | "all";
  onFilterChange: (f: ChangeType | "all") => void;
  searchTerm: string;
  onSearchChange: (s: string) => void;
}) {
  return (
    <div className="no-print mb-5 flex flex-wrap items-center justify-between gap-3">
      <div className="flex flex-wrap gap-1.5 rounded-xl border border-white/10 bg-slate-900/60 p-1">
        {FILTERS.map((f) => (
          <button
            key={f}
            onClick={() => onFilterChange(f)}
            className={`rounded-lg px-3.5 py-2 text-sm font-semibold capitalize transition ${
              activeFilter === f
                ? "bg-accent-indigo text-white shadow-[0_2px_8px_rgba(99,102,241,0.4)]"
                : "text-gray-400 hover:text-white"
            }`}
          >
            {f}
          </button>
        ))}
      </div>
      <input
        type="text"
        value={searchTerm}
        onChange={(e) => onSearchChange(e.target.value)}
        placeholder="Search clause (e.g. 11.5, 7.4)..."
        className="w-full max-w-xs rounded-lg border border-white/10 bg-slate-900/80 px-3.5 py-2 text-sm text-white outline-none focus:border-accent-indigo focus:ring-2 focus:ring-accent-indigo/25"
      />
    </div>
  );
}
