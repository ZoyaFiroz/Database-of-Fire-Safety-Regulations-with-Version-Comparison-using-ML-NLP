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
