"""
Generates a structured, natural-language comparison report for the General
Document Comparison feature.

Two providers, tried in order:

1. Gemini (google-genai SDK), if GEMINI_API_KEY is set in the environment.
   Free-tier, and capable enough to attempt real contradiction detection
   (identifying where the two documents make conflicting claims) via
   structured JSON output - something the local model below cannot do
   reliably. Set GEMINI_MODEL to override the default model name.

2. Local flan-t5-base (HuggingFace, via transformers - already a project
   dependency through sentence-transformers, no extra download beyond the
   model weights themselves). Used automatically if GEMINI_API_KEY isn't
   set, or if the Gemini call fails for any reason (network, quota, bad
   response) - the feature must keep working with zero configuration and
   zero cost. This path does NOT attempt contradiction detection: that's a
   distinct, harder NLP task (natural language inference) that a model this
   small does not do reliably, so it's honestly left empty rather than
   faked. It generates the "core similarities" / "unique to A" / "unique to
   B" sections as three SEPARATE model calls rather than one combined
   "write a report" call - a single combined call was tested and found
   unreliable at this model size, sometimes echoing one side's content and
   silently dropping the rest.

Either way, callers get back the same ComparisonReport shape - the frontend
doesn't need to know which provider produced it (report.provider is there
for transparency, e.g. to note it in a dissertation appendix).
"""
from __future__ import annotations

import os
import re
import threading
from dataclasses import dataclass, field

from app.nlp.generic_compare import GenericChange

LOCAL_MODEL_NAME = "google/flan-t5-base"
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"

_tokenizer = None
_model = None
# FastAPI runs sync endpoints in a thread pool, so two overlapping
# /general/compare requests can call generate() on this same cached model
# instance concurrently. transformers/torch generation isn't guaranteed
# thread-safe for concurrent calls on one model object - serialize access
# rather than risk an intermittent crash under concurrent load.
_generate_lock = threading.Lock()

MAX_EXCERPTS_PER_SIDE = 4
MIN_EXCERPT_CHARS = 60  # skip low-information fragments (headers, contact lines) when better material exists


@dataclass
class ComparisonReport:
    core_similarities: str | None    # what both documents share, or None if nothing matched
    unique_to_a: str | None          # what's only in Document A, or None if nothing was removed
    unique_to_b: str | None          # what's only in Document B, or None if nothing was added
    contradictions: list[str] = field(default_factory=list)  # only ever populated by the Gemini path
    provider: str = "local"          # "gemini" | "local" - which provider actually produced this report


def _clean(text: str) -> str:
    # U+FFFD is the Unicode replacement character - it shows up when a PDF's
    # font encoding doesn't map cleanly to text extraction (smart quotes,
    # bullets, etc. in some fonts). Strip it rather than feeding visible
    # garbage into the prompt. Deliberately NOT stripping all non-ASCII -
    # that would break genuine non-English content for multilingual
    # comparisons.
    return re.sub(r"�+", " ", text)


def _pick_excerpts(texts: list[str]) -> list[str]:
    substantial = [t for t in texts if len(t) >= MIN_EXCERPT_CHARS]
    pool = substantial if substantial else texts
    return [_clean(t) for t in pool[:MAX_EXCERPTS_PER_SIDE]]


# --- Gemini path -----------------------------------------------------------------

def _summarize_with_gemini(shared: list[str], removed: list[str], added: list[str]) -> ComparisonReport | None:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return None

    try:
        from google import genai
        from google.genai import types
        from pydantic import BaseModel

        class GeminiReport(BaseModel):
            core_similarities: str
            unique_to_document_a: str
            unique_to_document_b: str
            contradictions: list[str]

        def bullets(items: list[str]) -> str:
            return "\n".join(f"- {t}" for t in items) if items else "(none)"

        prompt = f"""Compare excerpts from two documents, Document A and Document B.

Excerpts common to both documents:
{bullets(shared)}

Excerpts unique to Document A:
{bullets(removed)}

Excerpts unique to Document B:
{bullets(added)}

Provide a JSON report with:
- core_similarities: one or two sentences on what both documents share (empty string if nothing is shared)
- unique_to_document_a: one or two sentences synthesizing what's unique to Document A (empty string if nothing is unique to it)
- unique_to_document_b: one or two sentences synthesizing what's unique to Document B (empty string if nothing is unique to it)
- contradictions: specific points where Document A and Document B make conflicting or opposing statements about the same topic. Return an empty list if you don't find any genuine contradictions - do not invent ones that aren't there."""

        client = genai.Client(api_key=api_key)
        model_name = os.environ.get("GEMINI_MODEL") or DEFAULT_GEMINI_MODEL
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_json_schema=GeminiReport.model_json_schema(),
            ),
        )

        import json
        data = json.loads(response.text)
        return ComparisonReport(
            core_similarities=data.get("core_similarities") or None,
            unique_to_a=data.get("unique_to_document_a") or None,
            unique_to_b=data.get("unique_to_document_b") or None,
            contradictions=data.get("contradictions") or [],
            provider="gemini",
        )
    except Exception as err:
        import warnings
        warnings.warn(f"Gemini summarization failed ({err}); falling back to the local model.")
        return None


# --- Local (flan-t5-base) path ----------------------------------------------------

def _get_local_model():
    global _tokenizer, _model
    if _model is None:
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
        print(f"Loading summarization model '{LOCAL_MODEL_NAME}' (first run downloads it, then it's cached)...")
        _tokenizer = AutoTokenizer.from_pretrained(LOCAL_MODEL_NAME)
        _model = AutoModelForSeq2SeqLM.from_pretrained(LOCAL_MODEL_NAME)
    return _tokenizer, _model


def _local_generate(prompt: str) -> str | None:
    # Locked end-to-end (including lazy model load, not just generate()) so
    # two concurrent requests can't both see the model as unloaded and race
    # to initialize it, and can't call generate() on it at the same time.
    with _generate_lock:
        tokenizer, model = _get_local_model()
        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=1024)
        output_ids = model.generate(
            **inputs,
            max_new_tokens=100,
            num_beams=4,
            repetition_penalty=1.3,
            no_repeat_ngram_size=3,
        )
    result = tokenizer.decode(output_ids[0], skip_special_tokens=True).strip()
    return result if len(result) >= 10 else None


def _local_summarize_topic(excerpts: list[str], subject: str) -> str | None:
    if not excerpts:
        return None
    prompt = (
        f"Write one sentence summarizing the main topic of the excerpts below, which are {subject}. "
        "Synthesize, don't just repeat the excerpts verbatim.\n\n"
        + "\n".join(f"- {t}" for t in excerpts)
        + "\n\nOne-sentence summary:"
    )
    return _local_generate(prompt)


def _summarize_with_local_model(shared: list[str], removed: list[str], added: list[str]) -> ComparisonReport:
    try:
        return ComparisonReport(
            core_similarities=_local_summarize_topic(shared, "common to both Document A and Document B"),
            unique_to_a=_local_summarize_topic(removed, "unique to Document A and not found in Document B"),
            unique_to_b=_local_summarize_topic(added, "unique to Document B and not found in Document A"),
            provider="local",
        )
    except Exception as err:
        import warnings
        warnings.warn(f"Local summarization failed ({err}); falling back to a stats-only description.")
        return ComparisonReport(
            core_similarities=None,
            unique_to_a=f"(Summary generation failed) {len(removed)} paragraph(s) sampled from Document A." if removed else None,
            unique_to_b=f"(Summary generation failed) {len(added)} paragraph(s) sampled from Document B." if added else None,
            provider="local",
        )


# --- Entry point -----------------------------------------------------------------

def summarize_changes(changes: list[GenericChange]) -> ComparisonReport:
    shared = _pick_excerpts([c.old_text for c in changes if c.change_type == "unchanged" and c.old_text])
    removed = _pick_excerpts([c.old_text for c in changes if c.change_type == "removed" and c.old_text])
    added = _pick_excerpts([c.new_text for c in changes if c.change_type == "added" and c.new_text])

    gemini_report = _summarize_with_gemini(shared, removed, added)
    if gemini_report is not None:
        return gemini_report

    return _summarize_with_local_model(shared, removed, added)
