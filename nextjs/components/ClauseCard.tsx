"use client";

import Link from "next/link";
import type { ComparisonChange } from "@/lib/types";
import { highlightDiff, type DiffRun } from "@/lib/diff";

const BADGE_CLASSES: Record<string, string> = {
  modified: "bg-modified/15 text-modified border-modified/30",
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

export default function ClauseCard({
  result,
  detailHref,
}: {
  result: ComparisonChange;
  detailHref: string;
}) {
  const num = result.old_clause_number || result.new_clause_number || "N/A";
  const simPct = (result.similarity * 100).toFixed(1) + "%";
  const { oldRuns, newRuns } = highlightDiff(result.old_text, result.new_text);

  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5 backdrop-blur-md transition hover:border-accent-indigo/30">
      <div className="mb-3.5 flex flex-wrap items-start justify-between gap-2 border-b border-white/5 pb-3">
        <div className="flex flex-wrap items-center gap-3">
          <Link
            href={detailHref}
            className="rounded-lg bg-white/[0.08] px-2.5 py-1 font-mono text-base font-bold hover:text-accent-indigo"
          >
            Clause {num}
          </Link>
          <span className="text-sm text-gray-400">
            Method: <code>{result.method}</code>
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="rounded-md border border-white/10 bg-white/5 px-2 py-1 font-mono text-xs text-gray-200">
            Sim: {simPct}
          </span>
          <span
            className={`rounded-md border px-2.5 py-1 text-xs font-bold uppercase tracking-wide ${BADGE_CLASSES[result.change_type]}`}
          >
            {result.change_type}
          </span>
        </div>
      </div>
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
        <DiffPane label="Version A (Base)" text={result.old_text} runs={oldRuns} mark="diff-del" empty="Clause not present in Version A" />
        <DiffPane label="Version B (Comparison)" text={result.new_text} runs={newRuns} mark="diff-add" empty="Clause not present in Version B" />
      </div>
    </div>
  );
}
