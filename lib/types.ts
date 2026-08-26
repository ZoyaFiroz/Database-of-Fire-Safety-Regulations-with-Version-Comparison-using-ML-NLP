export type ChangeType = "unchanged" | "modified" | "added" | "removed";
export type Method = "baseline" | "sbert" | "multilingual";

export interface DocumentSummary {
  id: number;
  title: string;
  jurisdiction: string;
}

export interface VersionSummary {
  id: number;
  label: string;
  effective_date: string | null;
  page_count: number | null;
}

export interface ClauseSummary {
  clause_number: string;
  section_title: string | null;
  text: string;
}

export interface ComparisonChange {
  change_type: ChangeType;
  old_clause_number: string | null;
  new_clause_number: string | null;
  similarity: number;
  method: string;
  old_text: string | null;
  new_text: string | null;
}

export interface ComparisonSummary {
  unchanged: number;
  modified: number;
  added: number;
  removed: number;
}

export interface ComparisonResponse {
  summary: ComparisonSummary;
  method: string;
  active_threshold: number;
  changes: ComparisonChange[];
  warning?: string;
}

export interface AuthUser {
  id: number;
  email: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: AuthUser;
}

export interface SavedComparison {
  id: number;
  old_version_id: number;
  new_version_id: number;
  method: Method;
  label: string | null;
  created_at: string;
}

export interface ClauseNote {
  id: number;
  old_version_id: number;
  new_version_id: number;
  method: Method;
  old_clause_number: string | null;
  new_clause_number: string | null;
  note_text: string;
  created_at: string;
  updated_at: string;
}

export interface ExportRecord {
  id: number;
  old_version_id: number;
  new_version_id: number;
  method: Method;
  export_type: "csv" | "pdf";
  filter_change_type: string | null;
  search_term: string | null;
  created_at: string;
  has_stored_content: boolean;
}

// --- General Document Comparison (schema-free, any two uploaded documents) ---

export interface GeneralDocument {
  id: number;
  filename: string;
  uploaded_at: string;
  char_count: number;
}

// No "modified" here, deliberately - see app/nlp/generic_compare.py's
// docstring for why a forced "this became that" pairing doesn't make sense
// for two arbitrary/unrelated documents.
export type GeneralChangeType = "unchanged" | "added" | "removed";

export interface GeneralChange {
  change_type: GeneralChangeType;
  old_text: string | null;
  new_text: string | null;
  similarity: number;
}

export interface GeneralComparisonSummary {
  id: number;
  doc_a_id: number;
  doc_a_filename: string;
  doc_b_id: number;
  doc_b_filename: string;
  method: Method;
  summary_core_similarities: string | null;
  summary_unique_to_a: string | null;
  summary_unique_to_b: string | null;
  summary_contradictions: string[];
  summary_provider: "gemini" | "local";
  global_similarity: number;
  unchanged_count: number;
  added_count: number;
  removed_count: number;
  created_at: string;
}

export interface GeneralComparisonDetail extends GeneralComparisonSummary {
  similarity_matrix: number[][] | null;
  chunks_a: string[];
  chunks_b: string[];
  changes: GeneralChange[];
}
