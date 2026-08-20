"""
Sentence-embedding utilities for semantic clause comparison (Stage 3).

Two selectable models:

  "sbert" (default) -> all-MiniLM-L6-v2. Small (~90MB), fast on CPU, strong
      general-purpose baseline for English semantic textual similarity. This
      is the model all of the project's threshold calibration and gold-
      standard evaluation was done against - SEMANTIC_UNCHANGED_THRESHOLD in
      app/nlp/compare.py is only valid for this model.

  "multilingual" -> paraphrase-multilingual-MiniLM-L12-v2. Trained on ~50
      languages projected into one shared embedding space, so a German
      clause and its English counterpart land close together even with zero
      lexical overlap - this is what makes cross-language comparison
      possible (e.g. old version in German, new version in English) without
      a separate translation step. Larger (~470MB) and slightly slower than
      the English-only model. Its similarity distribution is NOT the same as
      all-MiniLM-L6-v2's, so MULTILINGUAL_UNCHANGED_THRESHOLD in compare.py
      is a documented placeholder, not yet calibrated against real gold-
      standard multilingual annotations - see scripts/calibrate_threshold.py
      before trusting it on real dissertation results.

IMPORTANT - first-run download: the first call for a given model name
downloads it from Hugging Face and caches it under ~/.cache/huggingface for
all subsequent runs. This requires normal internet access. Run this on your
own machine, not inside a network-restricted environment.
"""
from __future__ import annotations
import numpy as np

MODEL_NAMES = {
    "sbert": "all-MiniLM-L6-v2",
    "multilingual": "paraphrase-multilingual-MiniLM-L12-v2",
}
DEFAULT_MODEL_KEY = "sbert"
EMBEDDING_DIM = 384  # both models above happen to share this dimensionality

_models: dict[str, object] = {}


def _get_model(model_key: str = DEFAULT_MODEL_KEY):
    if model_key not in MODEL_NAMES:
        raise ValueError(f"Unknown model_key '{model_key}'; expected one of {list(MODEL_NAMES)}")
    if model_key not in _models:
        from sentence_transformers import SentenceTransformer
        model_name = MODEL_NAMES[model_key]
        print(f"Loading sentence-transformer model '{model_name}' ({model_key}) "
              f"(first run downloads it, then it's cached)...")
        _models[model_key] = SentenceTransformer(model_name)
    return _models[model_key]


def embed(texts: list[str], model_key: str = DEFAULT_MODEL_KEY) -> np.ndarray:
    """
    Embed a list of texts. Returns an (n, dim) array of L2-normalized
    embeddings, so cosine similarity between any two rows is just their dot
    product.
    """
    if not texts:
        return np.zeros((0, EMBEDDING_DIM))
    model = _get_model(model_key)
    return model.encode(texts, normalize_embeddings=True, show_progress_bar=False)


def semantic_similarity_matrix(texts_a: list[str], texts_b: list[str], model_key: str = DEFAULT_MODEL_KEY) -> np.ndarray:
    """
    Cosine similarity matrix between two lists of texts, shape (len(a), len(b)).
    Embeddings are pre-normalized so this is just a matrix multiply.
    """
    emb_a = embed(texts_a, model_key)
    emb_b = embed(texts_b, model_key)
    if emb_a.shape[0] == 0 or emb_b.shape[0] == 0:
        return np.zeros((emb_a.shape[0], emb_b.shape[0]))
    return emb_a @ emb_b.T


def paired_similarity(texts_a: list[str], texts_b: list[str], model_key: str = DEFAULT_MODEL_KEY) -> np.ndarray:
    """
    Cosine similarity for paired texts (texts_a[i] vs texts_b[i]), not a
    full cross matrix. Used for same-clause-number pairs where we already
    know the pairing and just need each pair's similarity score.
    """
    assert len(texts_a) == len(texts_b)
    if not texts_a:
        return np.zeros(0)
    emb_a = embed(texts_a, model_key)
    emb_b = embed(texts_b, model_key)
    return np.sum(emb_a * emb_b, axis=1)  # row-wise dot product (both normalized)
