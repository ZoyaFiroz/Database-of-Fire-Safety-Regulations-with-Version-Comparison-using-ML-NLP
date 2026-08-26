"use client";

import { useState } from "react";
import type { ClauseNote } from "@/lib/types";

export default function ClauseNoteEditor({
  note,
  onSave,
}: {
  note: ClauseNote | undefined;
  onSave: (text: string) => Promise<void>;
}) {
  const [editing, setEditing] = useState(false);
  const [text, setText] = useState(note?.note_text ?? "");
  const [saving, setSaving] = useState(false);

  async function handleSave() {
    setSaving(true);
    try {
      await onSave(text);
      setEditing(false);
    } finally {
      setSaving(false);
    }
  }

  if (!editing && !note) {
    return (
      <button
        onClick={() => setEditing(true)}
        className="no-print mt-3 text-xs font-medium text-gray-500 hover:text-accent-indigo"
      >
        + Add a note
      </button>
    );
  }

  if (!editing && note) {
    return (
      <div className="no-print mt-3 rounded-lg border border-modified/20 bg-modified/5 px-3 py-2">
        <div className="text-xs font-semibold uppercase tracking-wide text-modified">Your note</div>
        <p className="mt-1 whitespace-pre-wrap text-sm text-gray-200">{note.note_text}</p>
        <button
          onClick={() => {
            setText(note.note_text);
            setEditing(true);
          }}
          className="mt-1.5 text-xs font-medium text-gray-500 hover:text-accent-indigo"
        >
          Edit
        </button>
      </div>
    );
  }

  return (
    <div className="no-print mt-3">
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        rows={3}
        placeholder="Your observation on this clause..."
        className="w-full rounded-lg border border-white/10 bg-slate-900/80 px-3 py-2 text-sm text-white outline-none focus:border-accent-indigo focus:ring-2 focus:ring-accent-indigo/25"
      />
      <div className="mt-1.5 flex gap-2">
        <button
          onClick={handleSave}
          disabled={saving || !text.trim()}
          className="rounded-md bg-accent-indigo px-3 py-1 text-xs font-semibold text-white disabled:opacity-50"
        >
          {saving ? "Saving…" : "Save"}
        </button>
        <button
          onClick={() => {
            setEditing(false);
            setText(note?.note_text ?? "");
          }}
          className="rounded-md px-3 py-1 text-xs text-gray-400 hover:text-white"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}
