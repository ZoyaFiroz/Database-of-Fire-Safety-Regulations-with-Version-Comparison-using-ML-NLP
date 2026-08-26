import type {
  AuthResponse,
  ClauseNote,
  ClauseSummary,
  ComparisonResponse,
  DocumentSummary,
  ExportRecord,
  GeneralComparisonDetail,
  GeneralComparisonSummary,
  GeneralDocument,
  Method,
  SavedComparison,
  VersionSummary,
} from "./types";
import { getToken } from "./auth";

// 127.0.0.1, not localhost: Node's fetch (undici) resolves "localhost" to
// ::1 (IPv6) first, which fails to connect since uvicorn listens on IPv4
// only - this bit both this Server Component's data fetching and, if left
// as "localhost", would silently work in the browser but fail during SSR.
const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(
  path: string,
  options: { method?: string; body?: unknown; signal?: AbortSignal; auth?: boolean } = {}
): Promise<T> {
  const headers: Record<string, string> = {};
  if (options.body !== undefined) headers["Content-Type"] = "application/json";
  if (options.auth) {
    const token = getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, {
    method: options.method || "GET",
    headers,
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
    signal: options.signal,
    cache: "no-store",
  });

  if (!res.ok) {
    let message = res.statusText;
    try {
      const body = await res.json();
      message = body.detail || message;
    } catch {
      // response wasn't JSON - keep statusText
    }
    throw new ApiError(res.status, message);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

// --- Documents / versions / comparison ---------------------------------------

export function listDocuments(signal?: AbortSignal) {
  return request<DocumentSummary[]>("/documents", { signal });
}

export function listVersions(documentId: number, signal?: AbortSignal) {
  return request<VersionSummary[]>(`/documents/${documentId}/versions`, { signal });
}

export function listClauses(versionId: number, signal?: AbortSignal) {
  return request<ClauseSummary[]>(`/versions/${versionId}/clauses`, { signal });
}

export function compareVersions(oldId: number, newId: number, method: Method, signal?: AbortSignal) {
  return request<ComparisonResponse>(`/compare/${oldId}/${newId}?method=${method}`, { signal });
}

// --- Auth ----------------------------------------------------------------------

export function register(email: string, password: string) {
  return request<AuthResponse>("/auth/register", { method: "POST", body: { email, password } });
}

export function login(email: string, password: string) {
  return request<AuthResponse>("/auth/login", { method: "POST", body: { email, password } });
}

export function getMe(signal?: AbortSignal) {
  return request<{ id: number; email: string }>("/auth/me", { auth: true, signal });
}

// --- Saved comparisons -----------------------------------------------------------

export function listSavedComparisons(signal?: AbortSignal) {
  return request<SavedComparison[]>("/saved-comparisons", { auth: true, signal });
}

export function createSavedComparison(
  oldVersionId: number,
  newVersionId: number,
  method: Method,
  label?: string
) {
  return request<SavedComparison>("/saved-comparisons", {
    method: "POST",
    auth: true,
    body: { old_version_id: oldVersionId, new_version_id: newVersionId, method, label },
  });
}

export function deleteSavedComparison(id: number) {
  return request<void>(`/saved-comparisons/${id}`, { method: "DELETE", auth: true });
}

// --- Clause notes ---------------------------------------------------------------

export function listClauseNotes(
  oldVersionId: number,
  newVersionId: number,
  method: Method,
  signal?: AbortSignal
) {
  return request<ClauseNote[]>(
    `/clause-notes?old_version_id=${oldVersionId}&new_version_id=${newVersionId}&method=${method}`,
    { auth: true, signal }
  );
}

export function upsertClauseNote(params: {
  oldVersionId: number;
  newVersionId: number;
  method: Method;
  oldClauseNumber: string | null;
  newClauseNumber: string | null;
  noteText: string;
}) {
  return request<ClauseNote>("/clause-notes", {
    method: "POST",
    auth: true,
    body: {
      old_version_id: params.oldVersionId,
      new_version_id: params.newVersionId,
      method: params.method,
      old_clause_number: params.oldClauseNumber,
      new_clause_number: params.newClauseNumber,
      note_text: params.noteText,
    },
  });
}

export function deleteClauseNote(id: number) {
  return request<void>(`/clause-notes/${id}`, { method: "DELETE", auth: true });
}

// --- Export history ---------------------------------------------------------------

export function logExport(params: {
  oldVersionId: number;
  newVersionId: number;
  method: Method;
  exportType: "csv" | "pdf";
  filterChangeType?: string;
  searchTerm?: string;
  csvContent?: string;
}) {
  return request<ExportRecord>("/exports", {
    method: "POST",
    auth: true,
    body: {
      old_version_id: params.oldVersionId,
      new_version_id: params.newVersionId,
      method: params.method,
      export_type: params.exportType,
      filter_change_type: params.filterChangeType || null,
      search_term: params.searchTerm || null,
      csv_content: params.csvContent || null,
    },
  });
}

export function listExports(signal?: AbortSignal) {
  return request<ExportRecord[]>("/exports", { auth: true, signal });
}

export function exportDownloadUrl(id: number) {
  return `${API_BASE}/exports/${id}/download`;
}

// --- General Document Comparison (any two uploaded documents, no fixed schema) ---

export async function uploadGeneralDocument(file: File, signal?: AbortSignal): Promise<GeneralDocument> {
  const token = getToken();
  const form = new FormData();
  form.append("file", file);

  const res = await fetch(`${API_BASE}/general/documents`, {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    body: form,
    signal,
    cache: "no-store",
  });

  if (!res.ok) {
    let message = res.statusText;
    try {
      message = (await res.json()).detail || message;
    } catch {
      // not JSON - keep statusText
    }
    throw new ApiError(res.status, message);
  }
  return res.json();
}

export function listGeneralDocuments(signal?: AbortSignal) {
  return request<GeneralDocument[]>("/general/documents", { auth: true, signal });
}

export function deleteGeneralDocument(id: number) {
  return request<void>(`/general/documents/${id}`, { method: "DELETE", auth: true });
}

export function compareGeneralDocuments(docAId: number, docBId: number, method: Method) {
  return request<GeneralComparisonDetail>("/general/compare", {
    method: "POST",
    auth: true,
    body: { doc_a_id: docAId, doc_b_id: docBId, method },
  });
}

export function listGeneralComparisons(signal?: AbortSignal) {
  return request<GeneralComparisonSummary[]>("/general/comparisons", { auth: true, signal });
}

export function getGeneralComparison(id: number, signal?: AbortSignal) {
  return request<GeneralComparisonDetail>(`/general/comparisons/${id}`, { auth: true, signal });
}

export function deleteGeneralComparison(id: number) {
  return request<void>(`/general/comparisons/${id}`, { method: "DELETE", auth: true });
}
