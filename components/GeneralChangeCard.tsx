"use client";

import type { GeneralChange } from "@/lib/types";
import { highlightDiff, type DiffRun } from "@/lib/diff";

const BADGE_CLASSES: Record<string, string> = {
  added: "bg-added/15 text-added border-added/30",
  removed: "bg-removed/15 text-removed border-removed/30",
  unchanged: "bg-unchanged/15 text-unchanged border-unchanged/30",
};

function DiffPane({ label, text, runs, mark, empty }: { label: string; text: string | null; runs: DiffRun[]; mark: "diff-del" | "diff-add"; empty: string }) {
  return (
    <div className="rounded-lg border border-white/5 bg-slate-900/60 p-3.5 text-sm text-gray-300">
      <div className="mb-2 text-xs font-bold uppercase tracking-wide text-gray-500">{label}</div>
      <div className="break-words">
        {text ? (
          runs.map((run, i) =>
            run.changed ? (
              <mark key={i} className={mark}>
                {run.text}
              </mark>
            ) : (
              <span key={i}>{run.text}</span>
            )
          )
        ) : (
          <em className="text-gray-500">{empty}</em>
        )}
      </div>
    </div>
  );
}

export default function GeneralChangeCard({ change, docALabel, docBLabel }: { change: GeneralChange; docALabel: string; docBLabel: string }) {
  const simPct = (change.similarity * 100).toFixed(1) + "%";
  const { oldRuns, newRuns } = highlightDiff(change.old_text, change.new_text);

  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5 backdrop-blur-md transition hover:border-accent-indigo/30">
      <div className="mb-3.5 flex flex-wrap items-center justify-end gap-2 border-b border-white/5 pb-3">
        {change.change_type === "unchanged" && (
          <span className="rounded-md border border-white/10 bg-white/5 px-2 py-1 font-mono text-xs text-gray-200">
            Sim: {simPct}
          </span>
        )}
        <span className={`rounded-md border px-2.5 py-1 text-xs font-bold uppercase tracking-wide ${BADGE_CLASSES[change.change_type]}`}>
          {change.change_type}
        </span>
      </div>
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
        <DiffPane label={docALabel} text={change.old_text} runs={oldRuns} mark="diff-del" empty="Not present in this document" />
        <DiffPane label={docBLabel} text={change.new_text} runs={newRuns} mark="diff-add" empty="Not present in this document" />
      </div>
    </div>
  );
}
