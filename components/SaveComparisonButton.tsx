"use client";

import { useState } from "react";
import { createSavedComparison } from "@/lib/api";
import { ApiError } from "@/lib/api";
import type { Method } from "@/lib/types";
import { useAuth } from "./AuthProvider";

export default function SaveComparisonButton({
  oldVersionId,
  newVersionId,
  method,
}: {
  oldVersionId: number;
  newVersionId: number;
  method: Method;
}) {
  const { user } = useAuth();
  const [saved, setSaved] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!user) return null;

  async function handleClick() {
    setSaving(true);
    setError(null);
    try {
      await createSavedComparison(oldVersionId, newVersionId, method);
      setSaved(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to save.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="flex items-center gap-2">
      <button
        onClick={handleClick}
        disabled={saving || saved}
        className="rounded-lg border border-white/10 bg-white/5 px-3.5 py-2 text-sm font-medium text-gray-200 transition hover:border-accent-indigo/40 hover:bg-accent-indigo/20 hover:text-white disabled:cursor-default disabled:opacity-60"
      >
        {saved ? "Saved ✓" : saving ? "Saving…" : "Save this comparison"}
      </button>
      {error && <span className="text-xs text-removed">{error}</span>}
    </div>
  );
}
