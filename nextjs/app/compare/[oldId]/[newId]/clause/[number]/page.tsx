"use client";

import { useEffect, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import Link from "next/link";
import ClauseCard from "@/components/ClauseCard";
import { compareVersions } from "@/lib/api";
import type { ComparisonChange, Method } from "@/lib/types";

export default function ClauseDetailPage() {
  const params = useParams<{ oldId: string; newId: string; number: string }>();
  const searchParams = useSearchParams();

  const oldVersionId = Number(params.oldId);
  const newVersionId = Number(params.newId);
  const method = (searchParams.get("method") as Method) || "baseline";
  const oldClauseNumber = searchParams.get("old") || "";
  const newClauseNumber = searchParams.get("new") || "";

  const [result, setResult] = useState<ComparisonChange | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    // Relies on the backend's compare-result cache - this comparison was
    // almost certainly just run from the list page, so this resolves
    // instantly rather than re-running the full pipeline.
    compareVersions(oldVersionId, newVersionId, method, controller.signal)
      .then((data) => {
        const match = data.changes.find(
          (c) =>
            (c.old_clause_number || "") === oldClauseNumber &&
            (c.new_clause_number || "") === newClauseNumber
        );
        setResult(match || null);
        setLoading(false);
      })
      .catch((err) => {
        if (err.name !== "AbortError") {
          setError(`Failed to load clause: ${err.message}`);
          setLoading(false);
        }
      });
    return () => controller.abort();
  }, [oldVersionId, newVersionId, method, oldClauseNumber, newClauseNumber]);

  return (
    <main className="mx-auto max-w-4xl px-4 py-8 sm:px-6 sm:py-10">
      <Link
        href={`/compare/${oldVersionId}/${newVersionId}?method=${method}`}
        className="mb-6 inline-block text-sm text-gray-400 hover:text-white"
      >
        ← Back to comparison
      </Link>

      <h1 className="mb-6 text-2xl font-bold tracking-tight">
        Clause {params.number}
      </h1>

      {loading && (
        <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-10 text-center text-gray-400">
          Loading...
        </div>
      )}

      {!loading && error && (
        <div className="rounded-2xl border border-removed/30 bg-removed/10 p-10 text-center text-removed">
          {error}
        </div>
      )}

      {!loading && !error && !result && (
        <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-10 text-center text-gray-400">
          Couldn&apos;t find this clause in the current comparison.
        </div>
      )}

      {!loading && !error && result && (
        <ClauseCard
          result={result}
          detailHref={`/compare/${oldVersionId}/${newVersionId}/clause/${params.number}?method=${method}&old=${oldClauseNumber}&new=${newClauseNumber}`}
        />
      )}
    </main>
  );
}
