"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/AuthProvider";
import {
  deleteSavedComparison,
  exportDownloadUrl,
  listDocuments,
  listExports,
  listSavedComparisons,
  listVersions,
} from "@/lib/api";
import type { ExportRecord, SavedComparison, VersionSummary } from "@/lib/types";

export default function AccountPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();

  const [saved, setSaved] = useState<SavedComparison[]>([]);
  const [exports, setExports] = useState<ExportRecord[]>([]);
  const [versionLabels, setVersionLabels] = useState<Record<number, string>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/login");
    }
  }, [authLoading, user, router]);

  useEffect(() => {
    if (!user) return;
    const controller = new AbortController();
    (async () => {
      try {
        const [savedData, exportsData, docs] = await Promise.all([
          listSavedComparisons(controller.signal),
          listExports(controller.signal),
          listDocuments(controller.signal),
        ]);
        setSaved(savedData);
        setExports(exportsData);

        const labels: Record<number, string> = {};
        for (const doc of docs) {
          const versions: VersionSummary[] = await listVersions(doc.id, controller.signal);
          for (const v of versions) labels[v.id] = v.label;
        }
        setVersionLabels(labels);
      } catch {
        // silently ignore - individual sections just render empty
      } finally {
        setLoading(false);
      }
    })();
    return () => controller.abort();
  }, [user]);

  async function handleDelete(id: number) {
    await deleteSavedComparison(id);
    setSaved((prev) => prev.filter((s) => s.id !== id));
  }

  if (authLoading || !user) {
    return (
      <main className="mx-auto max-w-4xl px-4 py-10 text-gray-400">Loading…</main>
    );
  }

  return (
    <main className="mx-auto max-w-4xl px-4 py-8 sm:px-6 sm:py-10">
      <h1 className="text-2xl font-bold tracking-tight">My Account</h1>
      <p className="mt-1 text-sm text-gray-400">Signed in as {user.email}</p>

      <section className="mt-8">
        <h2 className="mb-3 text-lg font-semibold">Saved Comparisons</h2>
        {loading ? (
          <p className="text-sm text-gray-500">Loading…</p>
        ) : saved.length === 0 ? (
          <p className="text-sm text-gray-500">
            None yet - use &quot;Save this comparison&quot; on any comparison page.
          </p>
        ) : (
          <div className="flex flex-col gap-2">
            {saved.map((s) => (
              <div
                key={s.id}
                className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-white/10 bg-white/[0.03] px-4 py-3"
              >
                <div>
                  <Link
                    href={`/compare/${s.old_version_id}/${s.new_version_id}?method=${s.method}`}
                    className="font-medium text-white hover:text-accent-indigo"
                  >
                    {versionLabels[s.old_version_id] ?? `v${s.old_version_id}`} →{" "}
                    {versionLabels[s.new_version_id] ?? `v${s.new_version_id}`}
                  </Link>
                  <div className="text-xs text-gray-500">
                    {s.method} {s.label && `· "${s.label}"`} · saved{" "}
                    {new Date(s.created_at).toLocaleDateString()}
                  </div>
                </div>
                <button
                  onClick={() => handleDelete(s.id)}
                  className="text-xs font-medium text-removed hover:underline"
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
        )}
      </section>

      <section className="mt-10">
        <h2 className="mb-3 text-lg font-semibold">Export History</h2>
        {loading ? (
          <p className="text-sm text-gray-500">Loading…</p>
        ) : exports.length === 0 ? (
          <p className="text-sm text-gray-500">
            None yet - exports you make while logged in are logged here.
          </p>
        ) : (
          <div className="flex flex-col gap-2">
            {exports.map((e) => (
              <div
                key={e.id}
                className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-white/10 bg-white/[0.03] px-4 py-3"
              >
                <div>
                  <Link
                    href={`/compare/${e.old_version_id}/${e.new_version_id}?method=${e.method}`}
                    className="font-medium text-white hover:text-accent-indigo"
                  >
                    {versionLabels[e.old_version_id] ?? `v${e.old_version_id}`} →{" "}
                    {versionLabels[e.new_version_id] ?? `v${e.new_version_id}`}
                  </Link>
                  <div className="text-xs text-gray-500">
                    {e.export_type.toUpperCase()} · {e.method}
                    {e.filter_change_type && e.filter_change_type !== "all" && ` · filtered: ${e.filter_change_type}`}
                    {e.search_term && ` · search: "${e.search_term}"`} ·{" "}
                    {new Date(e.created_at).toLocaleString()}
                  </div>
                </div>
                {e.has_stored_content ? (
                  <a
                    href={exportDownloadUrl(e.id)}
                    className="text-xs font-medium text-accent-indigo hover:underline"
                  >
                    Re-download CSV
                  </a>
                ) : (
                  <span className="text-xs text-gray-500" title="PDF exports are generated in your browser and aren't stored on the server">
                    Not re-downloadable
                  </span>
                )}
              </div>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}
