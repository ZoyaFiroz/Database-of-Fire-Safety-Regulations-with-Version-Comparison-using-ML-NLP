"use client";

import type { ChangeType, ComparisonChange, Method } from "@/lib/types";
import { changesToCsv, downloadCsv } from "@/lib/export";
import { logExport } from "@/lib/api";
import { useAuth } from "./AuthProvider";

export default function ExportButtons({
  changes,
  filenameBase,
  oldVersionId,
  newVersionId,
  method,
  activeFilter,
  searchTerm,
}: {
  changes: ComparisonChange[];
  filenameBase: string;
  oldVersionId: number;
  newVersionId: number;
  method: Method;
  activeFilter: ChangeType | "all";
  searchTerm: string;
}) {
  const { user } = useAuth();

  function maybeLog(exportType: "csv" | "pdf", csvContent?: string) {
    if (!user) return; // export history is a logged-in-only feature; export itself still works either way
    logExport({
      oldVersionId,
      newVersionId,
      method,
      exportType,
      filterChangeType: activeFilter,
      searchTerm,
      csvContent,
    }).catch(() => {
      // logging failure shouldn't block the export the user actually asked for
    });
  }

  function handleCsvExport() {
    const csv = changesToCsv(changes);
    downloadCsv(changes, `${filenameBase}.csv`);
    maybeLog("csv", csv);
  }

  function handlePdfExport() {
    window.print();
    maybeLog("pdf");
  }

  return (
    <div className="no-print flex gap-2">
      <button
        onClick={handleCsvExport}
        disabled={changes.length === 0}
        className="rounded-lg border border-white/10 bg-white/5 px-3.5 py-2 text-sm font-medium text-gray-200 transition hover:border-accent-indigo/40 hover:bg-accent-indigo/20 hover:text-white disabled:cursor-not-allowed disabled:opacity-40"
      >
        Export CSV
      </button>
      <button
        onClick={handlePdfExport}
        disabled={changes.length === 0}
        className="rounded-lg border border-white/10 bg-white/5 px-3.5 py-2 text-sm font-medium text-gray-200 transition hover:border-accent-indigo/40 hover:bg-accent-indigo/20 hover:text-white disabled:cursor-not-allowed disabled:opacity-40"
        title="Uses your browser's print dialog - choose 'Save as PDF' as the destination"
      >
        Export PDF
      </button>
      {!user && (
        <span className="self-center text-xs text-gray-500">(log in to keep export history)</span>
      )}
    </div>
  );
}
