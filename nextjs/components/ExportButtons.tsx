"use client";

import type { ComparisonChange } from "@/lib/types";
import { downloadCsv } from "@/lib/export";

export default function ExportButtons({
  changes,
  filenameBase,
}: {
  changes: ComparisonChange[];
  filenameBase: string;
}) {
  return (
    <div className="no-print flex gap-2">
      <button
        onClick={() => downloadCsv(changes, `${filenameBase}.csv`)}
        disabled={changes.length === 0}
        className="rounded-lg border border-white/10 bg-white/5 px-3.5 py-2 text-sm font-medium text-gray-200 transition hover:border-accent-indigo/40 hover:bg-accent-indigo/20 hover:text-white disabled:cursor-not-allowed disabled:opacity-40"
      >
        Export CSV
      </button>
      <button
        onClick={() => window.print()}
        disabled={changes.length === 0}
        className="rounded-lg border border-white/10 bg-white/5 px-3.5 py-2 text-sm font-medium text-gray-200 transition hover:border-accent-indigo/40 hover:bg-accent-indigo/20 hover:text-white disabled:cursor-not-allowed disabled:opacity-40"
        title="Uses your browser's print dialog - choose 'Save as PDF' as the destination"
      >
        Export PDF
      </button>
    </div>
  );
}
