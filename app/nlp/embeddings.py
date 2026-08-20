"""
Sentence-embedding utilities for semantic clause comparison (Stage 3).

Uses sentence-transformers with all-MiniLM-L6-v2 by default: small (~90MB),
fast on CPU, no GPU required, and a strong general-purpose baseline for
semantic textual similarity. Swap MODEL_NAME for a stronger or
legal-domain-specific model later if accuracy needs improving further -
that swap alone (with no other code changes) is a nice ablation to report
in your dissertation.

IMPORTANT - first-run download: the first call to _get_model() downloads
the model from Hugging Face (~90MB) and caches it under
~/.cache/huggingface for all subsequent runs. This requires normal internet
access. Run this on your own machine, not inside a network-restricted
environment.
"""
from __future__ import annotations
import numpy as np

MODEL_NAME = "all-MiniLM-L6-v2"

_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        print(f"Loading sentence-transformer model '{MODEL_NAME}' "
              f"(first run downloads ~90MB, then it's cached)...")
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def embed(texts: list[str]) -> np.ndarray:
    """
    Embed a list of texts. Returns an (n, dim) array of L2-normalized
    embeddings, so cosine similarity between any two rows is just their dot
    product.
    """
    if not texts:
        return np.zeros((0, 384))  # all-MiniLM-L6-v2 has 384-dim embeddings
    model = _get_model()
    return model.encode(texts, normalize_embeddings=True, show_progress_bar=False)


def semantic_similarity_matrix(texts_a: list[str], texts_b: list[str]) -> np.ndarray:
    """
    Cosine similarity matrix between two lists of texts, shape (len(a), len(b)).
    Embeddings are pre-normalized so this is just a matrix multiply.
    """
    emb_a = embed(texts_a)
    emb_b = embed(texts_b)
    if emb_a.shape[0] == 0 or emb_b.shape[0] == 0:
        return np.zeros((emb_a.shape[0], emb_b.shape[0]))
    return emb_a @ emb_b.T


def paired_similarity(texts_a: list[str], texts_b: list[str]) -> np.ndarray:
    """
    Cosine similarity for paired texts (texts_a[i] vs texts_b[i]), not a
    full cross matrix. Used for same-clause-number pairs where we already
    know the pairing and just need each pair's similarity score.
    """
    assert len(texts_a) == len(texts_b)
    if not texts_a:
        return np.zeros(0)
    emb_a = embed(texts_a)
    emb_b = embed(texts_b)
    return np.sum(emb_a * emb_b, axis=1)  # row-wise dot product (both normalized)
