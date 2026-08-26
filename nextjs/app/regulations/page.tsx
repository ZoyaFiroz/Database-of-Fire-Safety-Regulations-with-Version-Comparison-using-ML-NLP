import Link from "next/link";
import { listClauses, listDocuments, listVersions } from "@/lib/api";
import type { VersionSummary } from "@/lib/types";

interface VersionWithCount extends VersionSummary {
  clauseCount: number;
}

async function loadDocuments() {
  const documents = await listDocuments();
  const withVersions = await Promise.all(
    documents.map(async (doc) => {
      const versions = await listVersions(doc.id);
      const versionsWithCounts: VersionWithCount[] = await Promise.all(
        versions.map(async (v) => {
          const clauses = await listClauses(v.id);
          return { ...v, clauseCount: clauses.length };
        })
      );
      versionsWithCounts.sort((a, b) => a.id - b.id);
      return { ...doc, versions: versionsWithCounts };
    })
  );
  return withVersions;
}

function buildPresets(versions: VersionWithCount[]) {
  const presets: { oldId: number; newId: number; label: string }[] = [];
  for (let i = 0; i < versions.length - 1; i++) {
    presets.push({
      oldId: versions[i].id,
      newId: versions[i + 1].id,
      label: `${versions[i].label} → ${versions[i + 1].label}`,
    });
  }
  return presets;
}

export default async function RegulationsPage() {
  let documents: Awaited<ReturnType<typeof loadDocuments>> = [];
  let error: string | null = null;
  try {
    documents = await loadDocuments();
  } catch (err) {
    error = err instanceof Error ? err.message : String(err);
  }

  return (
    <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6 sm:py-10">
      <Link href="/" className="text-sm text-gray-400 hover:text-white">
        ← Dashboard
      </Link>

      <div className="mt-4 flex items-center gap-3">
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-brand-teal/30 bg-brand-teal/15 text-lg">
          🛡️
        </div>
        <div>
          <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">UK Safety Regulation Comparison</h1>
          <p className="mt-1 max-w-2xl text-sm text-gray-400">
            Structured, clause-level comparison across ingested versions of Approved Document B.
          </p>
        </div>
      </div>

      {error && (
        <div className="mt-8 rounded-2xl border border-removed/30 bg-removed/10 p-6 text-removed">
          Failed to load documents from the API: {error}
          <div className="mt-1 text-xs text-gray-400">
            Is the FastAPI backend running at {process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"}?
          </div>
        </div>
      )}

      <div className="mt-8 grid grid-cols-1 gap-6 lg:grid-cols-2">
        {documents.map((doc) => {
          const presets = buildPresets(doc.versions);
          const totalClauses = doc.versions.reduce((sum, v) => sum + v.clauseCount, 0);
          return (
            <div
              key={doc.id}
              className="rounded-2xl border border-brand-teal/15 bg-white/[0.03] p-6 backdrop-blur-md"
            >
              <div className="flex items-start justify-between gap-3">
                <h2 className="text-lg font-semibold">{doc.title}</h2>
                <span className="shrink-0 rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-xs text-gray-400">
                  {doc.jurisdiction}
                </span>
              </div>

              <div className="mt-4 flex gap-4 text-sm text-gray-400">
                <div>
                  <span className="font-semibold text-white">{doc.versions.length}</span> versions
                </div>
                <div>
                  <span className="font-semibold text-white">{totalClauses}</span> total clauses ingested
                </div>
              </div>

              <ul className="mt-4 space-y-1.5 text-sm">
                {doc.versions.map((v) => (
                  <li key={v.id} className="flex items-center justify-between text-gray-300">
                    <span>
                      {v.label} <span className="text-gray-500">(v{v.id})</span>
                    </span>
                    <span className="text-gray-500">{v.clauseCount} clauses · {v.page_count ?? "?"} pages</span>
                  </li>
                ))}
              </ul>

              {presets.length > 0 ? (
                <div className="mt-5 flex flex-wrap gap-2">
                  {presets.map((p) => (
                    <Link
                      key={`${p.oldId}-${p.newId}`}
                      href={`/compare/${p.oldId}/${p.newId}`}
                      className="rounded-full border border-brand-teal/20 bg-brand-teal/10 px-3 py-1.5 text-xs font-medium text-gray-200 transition hover:border-brand-teal/50 hover:bg-brand-teal/25 hover:text-white"
                    >
                      Compare {p.label} →
                    </Link>
                  ))}
                </div>
              ) : (
                <p className="mt-5 text-xs text-gray-500">Need at least two versions to compare.</p>
              )}
            </div>
          );
        })}
      </div>

      {!error && documents.length === 0 && (
        <p className="mt-8 text-sm text-gray-400">No documents ingested yet.</p>
      )}
    </main>
  );
}
