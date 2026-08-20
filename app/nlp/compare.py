"""
Clause-alignment and change-detection pipeline.

Two selectable methods, both implementing the same staged approach:

  method="baseline" (default, unchanged from before):
    Stage 1: match by identical clause_number, classify via difflib
             character-level similarity.
    Stage 2: for unmatched clauses (renumbering), align via TF-IDF cosine
             similarity.

  method="sbert" (Stage 3):
    Stage 1: match by identical clause_number, classify via sentence-
             embedding cosine similarity instead of difflib. This is the
             important change - it also fixes same-numbered pairs with
             subtle wording edits (e.g. clause 11.5's ", 2" insertion),
             which the baseline's Stage 2 (TF-IDF renumber-matching) never
             touches, because same-numbered pairs never reach Stage 2.
             Uses all-MiniLM-L6-v2 (English).
    Stage 2: for unmatched clauses, align via semantic similarity instead
             of TF-IDF.

  method="multilingual" (Stage 3, cross-language):
    Identical staged approach to "sbert", but uses a multilingual sentence
    embedding model (paraphrase-multilingual-MiniLM-L12-v2) so the old and
    new versions don't need to be in the same language - e.g. comparing a
    German edition against an English one. No translation step: both
    languages are embedded into the same vector space directly.

  All three methods share the "added"/"removed" fallback logic in
  align_unmatched() - only the similarity function and thresholds differ.

Threshold values (UNCHANGED_THRESHOLD / SEMANTIC_UNCHANGED_THRESHOLD) should
be treated as configuration to calibrate against your own gold-standard
annotations - see scripts/calibrate_threshold.py, which does this
empirically rather than by guessing. The SEMANTIC_* defaults below are
placeholders and MUST be recalibrated once you have real similarity scores
from your own corpus - semantic similarity for near-identical long
paragraphs behaves differently to difflib and the right cutoff cannot be
assumed from the difflib value.
"""
from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@dataclass
class ClauseRecord:
    clause_number: str
    text: str
    section_title: str | None = None


@dataclass
class ComparisonResult:
    change_type: str            # "unchanged" | "modified" | "added" | "removed"
    old_clause: ClauseRecord | None
    new_clause: ClauseRecord | None
    similarity: float
    method: str


# --- Baseline (difflib + TF-IDF) thresholds --------------------------------
UNCHANGED_THRESHOLD = 0.97
MIN_MATCH_THRESHOLD = 0.35

# --- Stage 3 (SBERT, English) thresholds ------------------------------------
# Calibrated empirically via scripts/calibrate_threshold.py against gold-standard CSV.
SEMANTIC_UNCHANGED_THRESHOLD = 0.9990
SEMANTIC_MIN_MATCH_THRESHOLD = 0.55

# --- Stage 3 (multilingual, cross-language) thresholds ----------------------
# NOT yet calibrated against gold-standard annotations (no manually-annotated
# multilingual corpus exists for this project) - these are placeholders
# carried over from the English SBERT model's calibrated values as a starting
# point. Cross-lingual similarity scores tend to run lower than same-language
# scores even for a correct translation, so these almost certainly need their
# own run of scripts/calibrate_threshold.py once real bilingual gold data
# exists - do not treat "modified" classifications from this method as
# dissertation-grade accuracy without doing that first.
MULTILINGUAL_UNCHANGED_THRESHOLD = 0.92
MULTILINGUAL_MIN_MATCH_THRESHOLD = 0.45

# Methods that use a sentence-embedding model rather than difflib/TF-IDF,
# mapped to the model key embeddings.py should load for them.
_SEMANTIC_METHODS = {
    "sbert": "sbert",
    "multilingual": "multilingual",
}


def _text_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def compare_by_clause_number(
    old_clauses: list[ClauseRecord], new_clauses: list[ClauseRecord], method: str = "baseline"
) -> tuple[list[ComparisonResult], list[ClauseRecord], list[ClauseRecord]]:
    """
    Stage 1: match by identical clause_number.
    method="baseline"     -> difflib character similarity.
    method="sbert"         -> sentence-embedding cosine similarity, English model (batched).
    method="multilingual" -> sentence-embedding cosine similarity, multilingual model (batched).
    """
    old_by_number = {c.clause_number: c for c in old_clauses}
    new_by_number = {c.clause_number: c for c in new_clauses}

    matched_numbers = [n for n in old_by_number if n in new_by_number]
    unmatched_old = [c for n, c in old_by_number.items() if n not in new_by_number]
    unmatched_new = [c for n, c in new_by_number.items() if n not in old_by_number]

    matched_results: list[ComparisonResult] = []

    if method in _SEMANTIC_METHODS:
        model_key = _SEMANTIC_METHODS[method]
        try:
            from app.nlp.embeddings import paired_similarity
            old_texts = [old_by_number[n].text for n in matched_numbers]
            new_texts = [new_by_number[n].text for n in matched_numbers]
            sims = paired_similarity(old_texts, new_texts, model_key=model_key)  # batched - one model call, not one per pair
            threshold = MULTILINGUAL_UNCHANGED_THRESHOLD if method == "multilingual" else SEMANTIC_UNCHANGED_THRESHOLD
            method_label = f"exact_number+{method}"
        except Exception as err:
            import warnings
            warnings.warn(f"{method} paired similarity failed ({err}); falling back to difflib.")
            sims = [_text_similarity(old_by_number[n].text, new_by_number[n].text) for n in matched_numbers]
            threshold = UNCHANGED_THRESHOLD
            method_label = f"exact_number+difflib ({method} fallback)"
    else:
        sims = [_text_similarity(old_by_number[n].text, new_by_number[n].text) for n in matched_numbers]
        threshold = UNCHANGED_THRESHOLD
        method_label = "exact_number+difflib"

    for number, sim in zip(matched_numbers, sims):
        old_c, new_c = old_by_number[number], new_by_number[number]
        change = "unchanged" if float(sim) >= threshold else "modified"
        matched_results.append(ComparisonResult(
            change_type=change, old_clause=old_c, new_clause=new_c,
            similarity=float(sim), method=method_label,
        ))

    return matched_results, unmatched_old, unmatched_new


def align_unmatched(
    unmatched_old: list[ClauseRecord], unmatched_new: list[ClauseRecord], method: str = "baseline"
) -> list[ComparisonResult]:
    """
    Stage 2: for clauses left over after exact-number matching (renumbering,
    additions, removals), find the best cross-match.
    method="baseline"     -> TF-IDF cosine similarity.
    method="sbert"         -> sentence-embedding cosine similarity, English model.
    method="multilingual" -> sentence-embedding cosine similarity, multilingual model.
    """
    results: list[ComparisonResult] = []
    is_semantic = method in _SEMANTIC_METHODS
    method_label = f"{method} (renumbered)" if is_semantic else "tfidf_cosine (renumbered)"
    min_threshold = (MULTILINGUAL_MIN_MATCH_THRESHOLD if method == "multilingual" else SEMANTIC_MIN_MATCH_THRESHOLD) if is_semantic else MIN_MATCH_THRESHOLD
    unchanged_threshold = (MULTILINGUAL_UNCHANGED_THRESHOLD if method == "multilingual" else SEMANTIC_UNCHANGED_THRESHOLD) if is_semantic else UNCHANGED_THRESHOLD
    no_candidate_label = method if is_semantic else "tfidf_cosine"

    if not unmatched_old or not unmatched_new:
        results += [ComparisonResult("removed", c, None, 0.0, no_candidate_label) for c in unmatched_old]
        results += [ComparisonResult("added", None, c, 0.0, no_candidate_label) for c in unmatched_new]
        return results

    if is_semantic:
        try:
            from app.nlp.embeddings import semantic_similarity_matrix
            sim_matrix = semantic_similarity_matrix(
                [c.text for c in unmatched_old], [c.text for c in unmatched_new],
                model_key=_SEMANTIC_METHODS[method],
            )
        except Exception as err:
            import warnings
            warnings.warn(f"{method} matrix calculation failed ({err}); falling back to TF-IDF.")
            corpus = [c.text for c in unmatched_old] + [c.text for c in unmatched_new]
            vectorizer = TfidfVectorizer(stop_words="english")
            tfidf = vectorizer.fit_transform(corpus)
            n_old = len(unmatched_old)
            sim_matrix = cosine_similarity(tfidf[:n_old], tfidf[n_old:])
            method_label = f"tfidf_cosine ({method} fallback)"
            min_threshold = MIN_MATCH_THRESHOLD
            unchanged_threshold = UNCHANGED_THRESHOLD
    else:
        corpus = [c.text for c in unmatched_old] + [c.text for c in unmatched_new]
        vectorizer = TfidfVectorizer(stop_words="english")
        tfidf = vectorizer.fit_transform(corpus)
        n_old = len(unmatched_old)
        sim_matrix = cosine_similarity(tfidf[:n_old], tfidf[n_old:])

    used_new = set()
    for i, old_c in enumerate(unmatched_old):
        best_j = sim_matrix[i].argmax()
        best_sim = sim_matrix[i][best_j]
        if best_sim >= min_threshold and best_j not in used_new:
            used_new.add(best_j)
            new_c = unmatched_new[best_j]
            change = "unchanged" if best_sim >= unchanged_threshold else "modified"
            results.append(ComparisonResult(
                change_type=change, old_clause=old_c, new_clause=new_c,
                similarity=float(best_sim), method=method_label,
            ))
        else:
            results.append(ComparisonResult("removed", old_c, None, float(best_sim), no_candidate_label))

    for j, new_c in enumerate(unmatched_new):
        if j not in used_new:
            results.append(ComparisonResult("added", None, new_c, 0.0, no_candidate_label))

    return results


def compare_versions(
    old_clauses: list[ClauseRecord], new_clauses: list[ClauseRecord], method: str = "baseline"
) -> list[ComparisonResult]:
    """
    Full pipeline. method="baseline" (difflib+TF-IDF, default, unchanged
    behaviour) or method="sbert" (Stage 3 semantic).
    """
    matched, unmatched_old, unmatched_new = compare_by_clause_number(old_clauses, new_clauses, method=method)
    aligned = align_unmatched(unmatched_old, unmatched_new, method=method)
    return matched + aligned


def summarize(results: list[ComparisonResult]) -> dict:
    summary = {"unchanged": 0, "modified": 0, "added": 0, "removed": 0}
    for r in results:
        summary[r.change_type] += 1
    return summary
