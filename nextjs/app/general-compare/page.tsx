"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/AuthProvider";
import GeneralDocumentPicker from "@/components/GeneralDocumentPicker";
import FilterBar from "@/components/FilterBar";
import GeneralChangeCard from "@/components/GeneralChangeCard";
import SimilarityHeatmap from "@/components/SimilarityHeatmap";
import ConceptualMatchDiagram from "@/components/ConceptualMatchDiagram";
import {
  ApiError,
  compareGeneralDocuments,
  deleteGeneralComparison,
  getGeneralComparison,
  listGeneralComparisons,
  listGeneralDocuments,
} from "@/lib/api";
import type {
  ChangeType,
  GeneralComparisonDetail,
  GeneralComparisonSummary,
  GeneralDocument,
  Method,
} from "@/lib/types";

const GENERAL_FILTERS: (ChangeType | "all")[] = ["all", "added", "removed", "unchanged"];

export default function GeneralComparePage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();

  const [documents, setDocuments] = useState<GeneralDocument[]>([]);
  const [docAId, setDocAId] = useState<number | null>(null);
  const [docBId, setDocBId] = useState<number | null>(null);
  const [method, setMethod] = useState<Method>("baseline");

  const [history, setHistory] = useState<GeneralComparisonSummary[]>([]);
  const [result, setResult] = useState<GeneralComparisonDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [activeFilter, setActiveFilter] = useState<ChangeType | "all">("all");
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    if (!authLoading && !user) router.push("/login");
  }, [authLoading, user, router]);

  useEffect(() => {
    if (!user) return;
    refreshDocuments();
    refreshHistory();
  }, [user]);

  function refreshDocuments() {
    listGeneralDocuments()
      .then(setDocuments)
      .catch(() => {});
  }

  function refreshHistory() {
    listGeneralComparisons()
      .then(setHistory)
      .catch(() => {});
  }

  async function handleCompare() {
    if (!docAId || !docBId) return;
    setLoading(true);
    setError(null);
    setActiveFilter("all");
    setSearchTerm("");
    try {
      const data = await compareGeneralDocuments(docAId, docBId, method);
      setResult(data);
      refreshHistory();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Comparison failed.");
    } finally {
      setLoading(false);
    }
  }

  async function handleLoadHistory(id: number) {
    setLoading(true);
    setError(null);
    setActiveFilter("all");
    setSearchTerm("");
    try {
      const data = await getGeneralComparison(id);
      setResult(data);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load this comparison.");
    } finally {
      setLoading(false);
    }
  }

  async function handleDeleteHistory(id: number) {
    await deleteGeneralComparison(id);
    setHistory((prev) => prev.filter((h) => h.id !== id));
    if (result?.id === id) setResult(null);
  }

  const filteredChanges = useMemo(() => {
    if (!result?.changes) return [];
    const term = searchTerm.toLowerCase().trim();
    return result.changes.filter((c) => {
      if (activeFilter !== "all" && c.change_type !== activeFilter) return false;
      if (term) {
        const text = ((c.old_text || "") + (c.new_text || "")).toLowerCase();
        return text.includes(term);
      }
      return true;
    });
  }, [result, activeFilter, searchTerm]);

  const matchThreads = useMemo(() => {
    if (!result?.changes) return { pairs: [], uniqueA: [], uniqueB: [] };
    const clean = (t: string | null) => (t || "").replace(/\s+/g, " ").trim();

    const pairs = result.changes
      .filter((c) => c.change_type === "unchanged")
      .slice()
      .sort((a, b) => b.similarity - a.similarity)
      .slice(0, 6)
      .map((c) => ({
        labelA: clean(c.old_text) || "(untitled excerpt)",
        labelB: clean(c.new_text) || "(untitled excerpt)",
        similarity: c.similarity,
      }));

    const uniqueA = result.changes
      .filter((c) => c.change_type === "removed")
      .slice(0, 6)
      .map((c) => clean(c.old_text))
      .filter(Boolean);

    const uniqueB = result.changes
      .filter((c) => c.change_type === "added")
      .slice(0, 6)
      .map((c) => clean(c.new_text))
      .filter(Boolean);

    return { pairs, uniqueA, uniqueB };
  }, [result]);

  if (authLoading || !user) {
    return <main className="mx-auto max-w-4xl px-4 py-10 text-gray-400">Loading…</main>;
  }

  return (
    <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6 sm:py-10">
      <div className="flex items-center gap-3">
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-brand-gold/30 bg-brand-gold/15 text-lg">
          🔗
        </div>
        <div>
          <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">Custom Document Comparison</h1>
          <p className="mt-1 max-w-3xl text-sm text-gray-400">
            Upload any two documents - not just fire safety regulations - and compare them. No fixed
            clause-numbering schema: text is aligned by content similarity, then summarized in plain
            language.
          </p>
        </div>
      </div>

      <div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-2">
        <GeneralDocumentPicker
          label="Document A"
          documents={documents}
          selectedId={docAId}
          onSelect={setDocAId}
          onUploaded={(doc) => {
            setDocuments((prev) => [doc, ...prev]);
            setDocAId(doc.id);
          }}
        />
        <GeneralDocumentPicker
          label="Document B"
          documents={documents}
          selectedId={docBId}
          onSelect={setDocBId}
          onUploaded={(doc) => {
            setDocuments((prev) => [doc, ...prev]);
            setDocBId(doc.id);
          }}
        />
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-3">
        <select
          value={method}
          onChange={(e) => setMethod(e.target.value as Method)}
          className="rounded-lg border border-white/10 bg-slate-900/80 px-3.5 py-2.5 text-sm text-white outline-none focus:border-brand-gold focus:ring-2 focus:ring-brand-gold/25"
        >
          <option value="baseline">Baseline: difflib + TF-IDF</option>
          <option value="sbert">Stage 3: Sentence-BERT (English)</option>
          <option value="multilingual">Stage 3: Multilingual (cross-language)</option>
        </select>
        <button
          onClick={handleCompare}
          disabled={!docAId || !docBId || loading}
          className="rounded-lg bg-gradient-to-r from-brand-gold to-brand-goldDark px-4 py-2.5 text-sm font-semibold text-[#071a1f] transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading ? "Comparing…" : "Compare & Summarize"}
        </button>
      </div>

      {error && (
        <div className="mt-6 rounded-2xl border border-removed/30 bg-removed/10 p-6 text-removed">{error}</div>
      )}

      {result && !loading && (
        <div className="mt-8">
          <ConceptualMatchDiagram
            docALabel={result.doc_a_filename}
            docBLabel={result.doc_b_filename}
            globalSimilarity={result.global_similarity}
            pairs={matchThreads.pairs}
            uniqueA={matchThreads.uniqueA}
            uniqueB={matchThreads.uniqueB}
          />

          <div className="mt-6 rounded-2xl border border-brand-teal/20 bg-brand-teal/5 p-5">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="text-xs font-semibold uppercase tracking-wide text-brand-teal">
                AI Synthesis Report
                <span className="ml-2 rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-medium normal-case text-gray-400">
                  {result.summary_provider === "gemini" ? "Gemini" : "Local model"}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-400">Global Similarity</span>
                <span className="rounded-full border border-brand-teal/40 bg-brand-teal/20 px-2.5 py-0.5 font-mono text-sm font-bold text-white">
                  {(result.global_similarity * 100).toFixed(1)}%
                </span>
              </div>
            </div>

            <div className="mt-4 flex flex-col gap-3">
              {result.summary_core_similarities && (
                <div>
                  <div className="text-xs font-bold uppercase tracking-wide text-unchanged">Core Similarities</div>
                  <p className="mt-1 text-sm leading-relaxed text-gray-100">{result.summary_core_similarities}</p>
                </div>
              )}
              {result.summary_unique_to_a && (
                <div>
                  <div className="text-xs font-bold uppercase tracking-wide text-removed">
                    Unique to {result.doc_a_filename}
                  </div>
                  <p className="mt-1 text-sm leading-relaxed text-gray-100">{result.summary_unique_to_a}</p>
                </div>
              )}
              {result.summary_unique_to_b && (
                <div>
                  <div className="text-xs font-bold uppercase tracking-wide text-added">
                    Unique to {result.doc_b_filename}
                  </div>
                  <p className="mt-1 text-sm leading-relaxed text-gray-100">{result.summary_unique_to_b}</p>
                </div>
              )}
              {result.summary_contradictions.length > 0 && (
                <div>
                  <div className="text-xs font-bold uppercase tracking-wide text-modified">Contradictions</div>
                  <ul className="mt-1 list-inside list-disc text-sm leading-relaxed text-gray-100">
                    {result.summary_contradictions.map((c, i) => (
                      <li key={i}>{c}</li>
                    ))}
                  </ul>
                </div>
              )}
              {result.summary_provider === "local" && (
                <p className="text-xs text-gray-500">
                  Contradiction detection isn&apos;t available with the local model - only Gemini (when
                  GEMINI_API_KEY is configured) attempts that.
                </p>
              )}
            </div>
          </div>

          <div className="mt-6 rounded-2xl border border-white/10 bg-white/[0.03] p-5 backdrop-blur-md">
            <h3 className="mb-2 text-sm font-semibold text-gray-300">
              Paragraph-to-paragraph similarity heatmap
            </h3>
            {result.similarity_matrix ? (
              <SimilarityHeatmap
                matrix={result.similarity_matrix}
                chunksA={result.chunks_a}
                chunksB={result.chunks_b}
                docALabel={result.doc_a_filename}
                docBLabel={result.doc_b_filename}
              />
            ) : (
              <p className="text-sm text-gray-500">
                This document pair has too many paragraphs to render a heatmap ({result.chunks_a.length} ×{" "}
                {result.chunks_b.length} would be impractical to visualize) - the stats and diff list below
                still cover the full comparison.
              </p>
            )}
          </div>

          <div className="mt-6">
            <FilterBar
              activeFilter={activeFilter}
              onFilterChange={setActiveFilter}
              searchTerm={searchTerm}
              onSearchChange={setSearchTerm}
              searchPlaceholder="Search paragraph text..."
              filters={GENERAL_FILTERS}
            />
          </div>

          <div className="flex flex-col gap-4">
            {filteredChanges.map((c, i) => (
              <GeneralChangeCard
                key={i}
                change={c}
                docALabel={result.doc_a_filename}
                docBLabel={result.doc_b_filename}
              />
            ))}
          </div>
        </div>
      )}

      <section className="mt-12">
        <h2 className="mb-3 text-lg font-semibold">Past Comparisons</h2>
        {history.length === 0 ? (
          <p className="text-sm text-gray-500">None yet - run a comparison above.</p>
        ) : (
          <div className="flex flex-col gap-2">
            {history.map((h) => (
              <div
                key={h.id}
                className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-white/10 bg-white/[0.03] px-4 py-3"
              >
                <button onClick={() => handleLoadHistory(h.id)} className="text-left">
                  <div className="font-medium text-white hover:text-accent-indigo">
                    {h.doc_a_filename} → {h.doc_b_filename}
                  </div>
                  <div className="text-xs text-gray-500">
                    {h.method} · {(h.global_similarity * 100).toFixed(0)}% similar · {h.added_count} added,{" "}
                    {h.removed_count} removed · {new Date(h.created_at).toLocaleString()}
                  </div>
                </button>
                <button
                  onClick={() => handleDeleteHistory(h.id)}
                  className="text-xs font-medium text-removed hover:underline"
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}
