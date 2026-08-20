import type { ComparisonChange } from "./types";

function csvEscape(value: string): string {
  if (/[",\n]/.test(value)) {
    return `"${value.replace(/"/g, '""')}"`;
  }
  return value;
}

export function changesToCsv(changes: ComparisonChange[]): string {
  const header = [
    "change_type",
    "old_clause_number",
    "new_clause_number",
    "similarity",
    "method",
    "old_text",
    "new_text",
  ];
  const rows = changes.map((c) =>
    [
      c.change_type,
      c.old_clause_number || "",
      c.new_clause_number || "",
      c.similarity.toString(),
      c.method,
      c.old_text || "",
      c.new_text || "",
    ]
      .map((v) => csvEscape(v))
      .join(",")
  );
  return [header.join(","), ...rows].join("\n");
}

export function downloadCsv(changes: ComparisonChange[], filename: string) {
  const csv = changesToCsv(changes);
  // Prepend a UTF-8 BOM so Excel opens accented/non-Latin clause text correctly.
  const blob = new Blob(["﻿" + csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
