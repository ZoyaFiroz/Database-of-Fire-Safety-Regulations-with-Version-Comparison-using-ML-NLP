"""
Comparison logic for the General Document Comparison feature.

Unlike app/nlp/compare.py's staged approach (exact clause-number match first,
then align only the leftovers), there's no reliable identifier to match on
between two arbitrary uploaded documents - paragraph N in document A has no
necessary relationship to paragraph N in document B, and the two documents
may not even share a common structure at all (two different resumes, a
contract vs an essay, etc.).

Deliberately only three categories - "unchanged", "added", "removed" - no
"modified". A "modified" category implies a claimed correspondence between
two paragraphs ("this became that"), which only makes sense for two versions
of the *same* document. For two arbitrary/unrelated documents, forcing a
weak best-available match into "modified" produces misleading pairings (e.g.
two resumes' unrelated bullet points getting paired just because they share
some vocabulary). So: a paragraph in A either has a genuinely equivalent
paragraph in B ("unchanged" - high similarity bar) or it doesn't
("removed"), full stop - no in-between forced pairing. Likewise a paragraph
in B either matches something in A or it's "added". The generated summary
(app/nlp/summarizer.py) is where "this changed to that"-style narration
belongs, in natural language, not as a rigid per-paragraph category.

Also returns the full chunk-by-chunk similarity matrix and a single "global
similarity score" - used by the frontend for a heatmap visualization and an
at-a-glance overall-similarity figure respectively. The matrix is the same
one already computed to derive unchanged/added/removed, just not discarded.

Thresholds below are reasonable starting points, not calibrated against any
gold-standard annotation (there isn't one for arbitrary documents) - unlike
UNCHANGED_THRESHOLD/SEMANTIC_UNCHANGED_THRESHOLD in app/nlp/compare.py, which
were calibrated against a real annotated corpus.
"""
from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

UNCHANGED_THRESHOLD = 0.9
SEMANTIC_UNCHANGED_THRESHOLD = 0.85
MULTILINGUAL_UNCHANGED_THRESHOLD = 0.8

_MODEL_KEYS = {"sbert": "sbert", "multilingual": "multilingual"}

# A heatmap beyond this many cells stops being visually useful (and heavy to
# ship over JSON) - the API omits the matrix above this size rather than
# silently returning something impractical to render.
MAX_HEATMAP_CELLS = 4000


@dataclass
class GenericChange:
    change_type: str  # "unchanged" | "added" | "removed"
    old_text: str | None
    new_text: str | None
    similarity: float


@dataclass
class GenericComparisonResult:
    changes: list[GenericChange]
    method_used: str
    similarity_matrix: list[list[float]] | None  # rows = chunks_a, cols = chunks_b; None if too large to be worth shipping
    global_similarity: float  # 0..1, symmetric "how much of each document's content is reflected in the other"


def _text_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def _similarity_matrix(chunks_a: list[str], chunks_b: list[str], method: str):
    if method in _MODEL_KEYS:
        from app.nlp.embeddings import semantic_similarity_matrix
        return semantic_similarity_matrix(chunks_a, chunks_b, model_key=_MODEL_KEYS[method])

    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf = vectorizer.fit_transform(chunks_a + chunks_b)
    n = len(chunks_a)
    return cosine_similarity(tfidf[:n], tfidf[n:])


def _unchanged_threshold(method: str) -> float:
    if method == "multilingual":
        return MULTILINGUAL_UNCHANGED_THRESHOLD
    if method == "sbert":
        return SEMANTIC_UNCHANGED_THRESHOLD
    return UNCHANGED_THRESHOLD


def _global_similarity(sim_matrix) -> float:
    """Mean of each row's best match, averaged with the mean of each
    column's best match - symmetric, so it doesn't matter which document is
    "A". 1.0 only if every paragraph on both sides has a near-perfect
    counterpart on the other side; 0.0 if the two documents share nothing."""
    n_rows = len(sim_matrix)
    n_cols = len(sim_matrix[0]) if n_rows else 0
    if n_rows == 0 or n_cols == 0:
        return 0.0

    row_best_avg = sum(max(row) for row in sim_matrix) / n_rows
    col_best_avg = sum(max(sim_matrix[i][j] for i in range(n_rows)) for j in range(n_cols)) / n_cols
    return float((row_best_avg + col_best_avg) / 2)


def compare_generic_documents(
    chunks_a: list[str], chunks_b: list[str], method: str = "baseline"
) -> GenericComparisonResult:
    if not chunks_a and not chunks_b:
        return GenericComparisonResult([], method, None, 0.0)
    if not chunks_a:
        return GenericComparisonResult([GenericChange("added", None, c, 0.0) for c in chunks_b], method, None, 0.0)
    if not chunks_b:
        return GenericComparisonResult([GenericChange("removed", c, None, 0.0) for c in chunks_a], method, None, 0.0)

    unchanged_threshold = _unchanged_threshold(method)

    try:
        sim_matrix = _similarity_matrix(chunks_a, chunks_b, method)
        method_used = method
    except Exception as err:
        import warnings
        warnings.warn(f"{method} similarity failed ({err}); falling back to difflib pairwise comparison.")
        sim_matrix = [[_text_similarity(a, b) for b in chunks_b] for a in chunks_a]
        method_used = "baseline"
        unchanged_threshold = _unchanged_threshold("baseline")

    # Normalize to plain nested lists of float (numpy arrays from sklearn/
    # embeddings.py otherwise leak non-JSON-serializable types up to the API).
    sim_matrix = [[float(v) for v in row] for row in sim_matrix]

    results: list[GenericChange] = []
    used_b: set[int] = set()

    for i, a_text in enumerate(chunks_a):
        row = sim_matrix[i]
        best_j = max(range(len(chunks_b)), key=lambda j: row[j])
        best_sim = row[best_j]
        if best_sim >= unchanged_threshold and best_j not in used_b:
            used_b.add(best_j)
            results.append(GenericChange("unchanged", a_text, chunks_b[best_j], best_sim))
        else:
            results.append(GenericChange("removed", a_text, None, 0.0))

    for j, b_text in enumerate(chunks_b):
        if j not in used_b:
            results.append(GenericChange("added", None, b_text, 0.0))

    global_similarity = _global_similarity(sim_matrix)
    exposed_matrix = sim_matrix if len(chunks_a) * len(chunks_b) <= MAX_HEATMAP_CELLS else None

    return GenericComparisonResult(results, method_used, exposed_matrix, global_similarity)
