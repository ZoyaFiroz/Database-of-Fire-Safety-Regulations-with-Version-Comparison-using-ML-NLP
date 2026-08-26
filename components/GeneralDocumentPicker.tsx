"use client";

import { useRef, useState } from "react";
import type { GeneralDocument } from "@/lib/types";
import { ApiError, uploadGeneralDocument } from "@/lib/api";

export default function GeneralDocumentPicker({
  label,
  documents,
  selectedId,
  onSelect,
  onUploaded,
}: {
  label: string;
  documents: GeneralDocument[];
  selectedId: number | null;
  onSelect: (id: number) => void;
  onUploaded: (doc: GeneralDocument) => void;
}) {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  async function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      const doc = await uploadGeneralDocument(file);
      onUploaded(doc);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Upload failed.");
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  return (
    <div className="flex flex-col gap-2 rounded-2xl border border-white/10 bg-white/[0.03] p-5 backdrop-blur-md">
      <label className="text-xs font-semibold uppercase tracking-wide text-gray-400">{label}</label>

      {documents.length > 0 && (
        <select
          value={selectedId ?? ""}
          onChange={(e) => onSelect(Number(e.target.value))}
          className="rounded-lg border border-white/10 bg-slate-900/80 px-3.5 py-2.5 text-sm text-white outline-none focus:border-accent-indigo focus:ring-2 focus:ring-accent-indigo/25"
        >
          <option value="" disabled>
            Select a previously uploaded document…
          </option>
          {documents.map((d) => (
            <option key={d.id} value={d.id}>
              {d.filename} ({d.char_count.toLocaleString()} chars)
            </option>
          ))}
        </select>
      )}

      <div className="flex items-center gap-2">
        <div className="h-px flex-1 bg-white/10" />
        <span className="text-xs text-gray-500">or</span>
        <div className="h-px flex-1 bg-white/10" />
      </div>

      <label className="cursor-pointer rounded-lg border border-dashed border-white/20 bg-slate-900/40 px-3.5 py-3 text-center text-sm text-gray-300 transition hover:border-accent-indigo/50 hover:bg-accent-indigo/10">
        {uploading ? "Uploading…" : "Upload a new PDF or .txt file"}
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.txt"
          onChange={handleFileChange}
          disabled={uploading}
          className="hidden"
        />
      </label>

      {error && <p className="text-xs text-removed">{error}</p>}
    </div>
  );
}
