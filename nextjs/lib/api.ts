import type {
  ClauseSummary,
  ComparisonResponse,
  DocumentSummary,
  Method,
  VersionSummary,
} from "./types";

// 127.0.0.1, not localhost: Node's fetch (undici) resolves "localhost" to
// ::1 (IPv6) first, which fails to connect since uvicorn listens on IPv4
// only - this bit both this Server Component's data fetching and, if left
// as "localhost", would silently work in the browser but fail during SSR.
const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

async function getJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { signal, cache: "no-store" });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText}: ${body || path}`);
  }
  return res.json();
}

export function listDocuments(signal?: AbortSignal) {
  return getJson<DocumentSummary[]>("/documents", signal);
}

export function listVersions(documentId: number, signal?: AbortSignal) {
  return getJson<VersionSummary[]>(`/documents/${documentId}/versions`, signal);
}

export function listClauses(versionId: number, signal?: AbortSignal) {
  return getJson<ClauseSummary[]>(`/versions/${versionId}/clauses`, signal);
}

export function compareVersions(
  oldId: number,
  newId: number,
  method: Method,
  signal?: AbortSignal
) {
  return getJson<ComparisonResponse>(`/compare/${oldId}/${newId}?method=${method}`, signal);
}
