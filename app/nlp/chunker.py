"""
Generic paragraph-based chunking for the General Document Comparison
feature. Unlike app/ingestion/clause_parser.py (which relies on Approved
Document B's numbered-clause structure, e.g. "1.1 ..."), this makes no
assumption about the document's structure - it has to work for prose,
contracts, articles, and dense single-column layouts alike (e.g. a resume
PDF, which pdfplumber often extracts with almost no blank lines at all, and
whose "lines" are just wherever the PDF happened to wrap - not sentence or
paragraph boundaries).

Hierarchical fallback, since no single split strategy works for every
document layout:
  1. Split on blank lines (works for prose/contracts/articles).
  2. Any resulting block still too large (e.g. a resume with one blank line
     in the whole document) gets its line-wraps rejoined into continuous
     text first - splitting on the raw PDF line breaks instead would chop
     mid-sentence at whatever column width the PDF happened to wrap at -
     then split on sentence boundaries.
  3. If a "sentence" is still too large (e.g. a long bullet list that got
     joined into one line with no terminal punctuation at all), fall back
     to fixed-size slices as a last resort.
"""
from __future__ import annotations

import re

MIN_CHUNK_CHARS = 20   # drop stray short fragments (page numbers, single words from layout artifacts)
MAX_CHUNK_CHARS = 500  # blocks larger than this get split further - keeps chunks fine-grained enough to align meaningfully

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")


def _collapse(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def _split_large_block(block: str) -> list[str]:
    # Rejoin the block's line-wraps into one continuous string before
    # splitting further - the raw lines are layout artifacts, not sentence
    # or item boundaries.
    joined = _collapse(block)
    if len(joined) <= MAX_CHUNK_CHARS:
        return [joined] if len(joined) >= MIN_CHUNK_CHARS else []

    pieces = []
    for sentence in _SENTENCE_SPLIT_RE.split(joined):
        sentence = sentence.strip()
        if not sentence:
            continue
        if len(sentence) <= MAX_CHUNK_CHARS:
            pieces.append(sentence)
        else:
            # No sentence-ending punctuation to split on at all (e.g. a
            # long bullet list with no periods, joined into one line) -
            # fixed-size slices are better than one giant unsplit chunk.
            for i in range(0, len(sentence), MAX_CHUNK_CHARS):
                piece = sentence[i : i + MAX_CHUNK_CHARS].strip()
                if piece:
                    pieces.append(piece)

    return [p for p in pieces if len(p) >= MIN_CHUNK_CHARS]


def chunk_paragraphs(text: str) -> list[str]:
    raw_paragraphs = re.split(r"\n\s*\n", text)
    chunks = []
    for p in raw_paragraphs:
        if not p.strip():
            continue
        collapsed = _collapse(p)
        if len(collapsed) <= MAX_CHUNK_CHARS:
            if len(collapsed) >= MIN_CHUNK_CHARS:
                chunks.append(collapsed)
        else:
            chunks.extend(_split_large_block(p))
    return chunks
