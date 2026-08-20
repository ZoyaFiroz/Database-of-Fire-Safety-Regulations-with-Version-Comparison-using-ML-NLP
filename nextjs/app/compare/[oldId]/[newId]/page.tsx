"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import Controls from "@/components/Controls";
import StatsGrid from "@/components/StatsGrid";
import ChangeTypeChart from "@/components/ChangeTypeChart";
import SimilarityHistogram from "@/components/SimilarityHistogram";
import FilterBar from "@/components/FilterBar";
import ClauseCard from "@/components/ClauseCard";
import ExportButtons from "@/components/ExportButtons";
import { compareVersions, listDocuments, listVersions } from "@/lib/api";
import type { ChangeType, ComparisonResponse, Method, VersionSummary } from "@/lib/types";

export default function ComparePage() {
  const params = useParams<{ oldId: string; newId: string }>();
  const searchParams = useSearchParams();
  const router = useRouter();

  const oldVersionId = Number(params.oldId);
  const newVersionId = Number(params.newId);
  const method = (searchParams.get("method") as Method) || "baseline";

  const [documentTitle, setDocumentTitle] = useState<string | null>(null);
  const [versions, setVersions] = useState<VersionSummary[]>([]);
  const [compareData, setCompareData] = useState<ComparisonResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeFilter, setActiveFilter] = useState<ChangeType | "all">("all");
  const [searchTerm, setSearchTerm] = useState("");

  // Find which document these version ids belong to, so Controls can offer
  // its sibling versions in the selectors.
  useEffect(() => {
    const controller = new AbortController();
    (async () => {
      try {
        const docs = await listDocuments(controller.signal);
        for (const doc of docs) {
          const vs = await listVersions(doc.id, controller.signal);
          if (vs.some((v) => v.id === oldVersionId || v.id === newVersionId)) {
            setDocumentTitle(doc.title);
            setVersions(vs);
            return;
          }
        }
      } catch (err) {
        if ((err as Error).name !== "AbortError") {
          setError(`Failed to load document/version metadata: ${(err as Error).message}`);
        }
      }
    })();
    return () => controller.abort();
  }, [oldVersionId, newVersionId]);

  useEffect(() => {
    if (!oldVersionId || !newVersionId) return;
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    compareVersions(oldVersionId, newVersionId, method, controller.signal)
      .then((data) => {
        setCompareData(data);
        setLoading(false);
      })
      .catch((err) => {
        if (err.name !== "AbortError") {
          setError(`Comparison failed: ${err.message}`);
          setLoading(false);
        }
      });
    return () => controller.abort();
  }, [oldVersionId, newVersionId, method]);

  const filteredResults = useMemo(() => {
    if (!compareData?.changes) return [];
    const term = searchTerm.toLowerCase().trim();
    return compareData.changes.filter((r) => {
      if (activeFilter !== "all" && r.change_type !== activeFilter) return false;
      if (term) {
        const clauseNum = (r.old_clause_number || r.new_clause_number || "").toLowerCase();
        const text = ((r.old_text || "") + (r.new_text || "")).toLowerCase();
        return clauseNum.includes(term) || text.includes(term);
      }
      return true;
    });
  }, [compareData, activeFilter, searchTerm]);

  function goToVersions(oldId: number, newId: number) {
    router.push(`/compare/${oldId}/${newId}?method=${method}`);
  }

  function setMethod(m: Method) {
    router.push(`/compare/${oldVersionId}/${newVersionId}?method=${m}`);
  }

  return (
    <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6 sm:py-10">
      <div className="no-print mb-6 flex items-center justify-between gap-3">
        <Link href="/" className="text-sm text-gray-400 hover:text-white">
          ← Documents
        </Link>
        <ExportButtons changes={filteredResults} filenameBase={`comparison-${oldVersionId}-vs-${newVersionId}-${method}`} />
      </div>

      <Controls
        documentTitle={documentTitle}
        versions={versions}
        oldVersionId={oldVersionId}
        newVersionId={newVersionId}
        method={method}
        onVersionsChange={goToVersions}
        onMethodChange={setMethod}
      />

      <StatsGrid summary={compareData?.summary} />

      {compareData && !loading && (
        <div className="mb-6 grid grid-cols-1 gap-4 lg:grid-cols-2">
          <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5 backdrop-blur-md">
            <h3 className="mb-2 text-sm font-semibold text-gray-300">Change type breakdown</h3>
            <ChangeTypeChart summary={compareData.summary} />
          </div>
          <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5 backdrop-blur-md">
            <h3 className="mb-2 text-sm font-semibold text-gray-300">Similarity score distribution (matched pairs)</h3>
            <SimilarityHistogram changes={compareData.changes} />
          </div>
        </div>
      )}

      <FilterBar
        activeFilter={activeFilter}
        onFilterChange={setActiveFilter}
        searchTerm={searchTerm}
        onSearchChange={setSearchTerm}
      />

      {compareData?.warning && (
        <div className="mb-4 rounded-xl border border-modified/40 bg-modified/15 px-4 py-3 text-sm text-modified">
          <strong>System Notice:</strong> {compareData.warning}
        </div>
      )}

      {error && (
        <div className="rounded-2xl border border-removed/30 bg-removed/10 p-10 text-center text-removed">
          {error}
        </div>
      )}

      {!error && loading && (
        <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-10 text-center text-gray-400">
          Executing comparison pipeline
          {method !== "baseline"
            ? " (sentence-embedding model - can take up to a minute on CPU for a full document)"
            : ""}
          ...
        </div>
      )}

      {!error && !loading && filteredResults.length === 0 && (
        <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-10 text-center text-gray-400">
          No matching clauses found for current filter.
        </div>
      )}

      {!error && !loading && filteredResults.length > 0 && (
        <div className="flex flex-col gap-4">
          {filteredResults.map((r) => {
            const num = r.old_clause_number || r.new_clause_number || "na";
            const detailHref = `/compare/${oldVersionId}/${newVersionId}/clause/${encodeURIComponent(
              num
            )}?method=${method}&old=${encodeURIComponent(r.old_clause_number || "")}&new=${encodeURIComponent(
              r.new_clause_number || ""
            )}`;
            return (
              <ClauseCard
                key={`${r.old_clause_number || "-"}-${r.new_clause_number || "-"}-${r.method}`}
                result={r}
                detailHref={detailHref}
              />
            );
          })}
        </div>
      )}
    </main>
  );
}
