"use client";

import type { Method, VersionSummary } from "@/lib/types";

function buildPresets(versions: VersionSummary[]) {
  if (versions.length < 2) return [];
  const sorted = [...versions].sort((a, b) => a.id - b.id);
  const presets: { oldId: number; newId: number; label: string }[] = [];
  for (let i = 0; i < sorted.length - 1; i++) {
    presets.push({
      oldId: sorted[i].id,
      newId: sorted[i + 1].id,
      label: `${sorted[i].label} → ${sorted[i + 1].label}`,
    });
  }
  if (sorted.length > 2) {
    presets.push({
      oldId: sorted[0].id,
      newId: sorted[sorted.length - 1].id,
      label: `${sorted[0].label} → ${sorted[sorted.length - 1].label} (Full Evolution)`,
    });
  }
  return presets;
}

export default function Controls({
  documentTitle,
  versions,
  oldVersionId,
  newVersionId,
  method,
  onVersionsChange,
  onMethodChange,
}: {
  documentTitle: string | null;
  versions: VersionSummary[];
  oldVersionId: number;
  newVersionId: number;
  method: Method;
  onVersionsChange: (oldId: number, newId: number) => void;
  onMethodChange: (method: Method) => void;
}) {
  const presets = buildPresets(versions);

  return (
    <div className="no-print">
      {presets.length > 0 && (
        <div className="mb-4 flex flex-wrap items-center gap-2">
          <span className="text-xs font-semibold uppercase tracking-wide text-gray-400">
            Presets:
          </span>
          {presets.map((p) => (
            <button
              key={`${p.oldId}-${p.newId}`}
              onClick={() => onVersionsChange(p.oldId, p.newId)}
              className={`rounded-full border px-3 py-1.5 text-xs font-medium transition ${
                p.oldId === oldVersionId && p.newId === newVersionId
                  ? "border-accent-indigo/50 bg-accent-indigo/25 text-white"
                  : "border-white/10 bg-white/5 text-gray-200 hover:border-accent-indigo/40 hover:bg-accent-indigo/20"
              }`}
            >
              {p.label}
            </button>
          ))}
        </div>
      )}

      <div className="mb-6 grid grid-cols-1 gap-4 rounded-2xl border border-white/10 bg-white/[0.03] p-5 backdrop-blur-md sm:grid-cols-2 lg:grid-cols-4">
        <div className="flex flex-col gap-1.5">
          <label className="text-xs font-semibold uppercase tracking-wide text-gray-400">
            Regulation Document
          </label>
          <div className="rounded-lg border border-white/10 bg-slate-900/80 px-3.5 py-2.5 text-sm text-gray-300">
            {documentTitle ?? "Loading…"}
          </div>
        </div>

        <div className="flex flex-col gap-1.5">
          <label className="text-xs font-semibold uppercase tracking-wide text-gray-400">
            Version A (Base)
          </label>
          <select
            value={oldVersionId}
            onChange={(e) => onVersionsChange(Number(e.target.value), newVersionId)}
            className="rounded-lg border border-white/10 bg-slate-900/80 px-3.5 py-2.5 text-sm text-white outline-none focus:border-accent-indigo focus:ring-2 focus:ring-accent-indigo/25"
          >
            {versions.map((v) => (
              <option key={v.id} value={v.id}>
                {v.label} (v{v.id})
              </option>
            ))}
          </select>
        </div>

        <div className="flex flex-col gap-1.5">
          <label className="text-xs font-semibold uppercase tracking-wide text-gray-400">
            Version B (Comparison)
          </label>
          <select
            value={newVersionId}
            onChange={(e) => onVersionsChange(oldVersionId, Number(e.target.value))}
            className="rounded-lg border border-white/10 bg-slate-900/80 px-3.5 py-2.5 text-sm text-white outline-none focus:border-accent-indigo focus:ring-2 focus:ring-accent-indigo/25"
          >
            {versions.map((v) => (
              <option key={v.id} value={v.id}>
                {v.label} (v{v.id})
              </option>
            ))}
          </select>
        </div>

        <div className="flex flex-col gap-1.5">
          <label className="text-xs font-semibold uppercase tracking-wide text-gray-400">
            NLP Model Pipeline
          </label>
          <select
            value={method}
            onChange={(e) => onMethodChange(e.target.value as Method)}
            className="rounded-lg border border-white/10 bg-slate-900/80 px-3.5 py-2.5 text-sm text-white outline-none focus:border-accent-indigo focus:ring-2 focus:ring-accent-indigo/25"
          >
            <option value="baseline">Baseline: difflib + TF-IDF</option>
            <option value="sbert">Stage 3: Sentence-BERT (English)</option>
            <option value="multilingual">Stage 3: Multilingual (cross-language)</option>
          </select>
        </div>
      </div>
    </div>
  );
}
