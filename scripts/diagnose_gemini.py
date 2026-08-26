"""
Standalone diagnostic - reads GEMINI_API_KEY from .env (or your shell
environment, if you set it there instead) and makes one real test call.

    python scripts/diagnose_gemini.py

Prints the raw exception (not swallowed) so we can see exactly what's
failing - invalid key, wrong model name, quota/billing, bad response shape,
etc.
"""
import os
import sys

sys.path.insert(0, ".")
import app  # noqa: F401 - triggers .env loading via app/__init__.py, same as the real app

api_key = os.environ.get("GEMINI_API_KEY")
print("GEMINI_API_KEY set:", bool(api_key))
if api_key:
    print("Key starts with:", api_key[:6] + "...")

model_name = os.environ.get("GEMINI_MODEL") or "gemini-2.5-flash"
print("Model:", model_name)

from google import genai
from google.genai import types
from pydantic import BaseModel


class GeminiReport(BaseModel):
    core_similarities: str
    unique_to_document_a: str
    unique_to_document_b: str
    contradictions: list[str]


client = genai.Client(api_key=api_key)

print("\nCalling Gemini...")
response = client.models.generate_content(
    model=model_name,
    contents="Compare excerpts from two documents.\n\nDocument A: The sky is blue.\nDocument B: The sky is grey today.\n\n"
    "Provide a JSON report with core_similarities, unique_to_document_a, unique_to_document_b, and contradictions (a list).",
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        response_json_schema=GeminiReport.model_json_schema(),
    ),
)

print("\nRaw response.text:")
print(response.text)
