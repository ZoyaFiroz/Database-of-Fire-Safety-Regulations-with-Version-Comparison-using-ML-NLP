const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function getJson(path, signal) {
  const res = await fetch(`${API_BASE}${path}`, { signal });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText}: ${body || path}`);
  }
  return res.json();
}

export function listDocuments(signal) {
  return getJson("/documents", signal);
}

export function listVersions(documentId, signal) {
  return getJson(`/documents/${documentId}/versions`, signal);
}

export function compareVersions(oldId, newId, method, signal) {
  return getJson(`/compare/${oldId}/${newId}?method=${method}`, signal);
}
