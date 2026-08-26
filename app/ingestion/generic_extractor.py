"""
Text extraction for the General Document Comparison feature. Unlike
pdf_extractor.py (which reads from a path on disk as part of the fixed
ingest.py pipeline), this works directly on uploaded file bytes and accepts
either a PDF or a plain .txt file - there's no assumption here about the
document being Approved Document B or any particular structure.

A PDF page can carry a real, selectable text layer, or it can be effectively
a picture (a scanned page, or a screenshot/photo pasted in) with no text
layer at all - pdfplumber's extract_text() returns nothing useful for those.
When a page's text layer is empty or near-empty, we render that page to an
image and OCR it with Tesseract instead, so scanned pages still contribute
real, comparable text rather than silently vanishing from the comparison.
This does NOT compare the pixel content of images that sit alongside real
text on an otherwise-text page (e.g. a diagram next to a paragraph) - only
pages whose text layer is too thin to be useful on its own fall back to OCR.
"""
from __future__ import annotations

import io
import os

import pdfplumber
import pytesseract

SUPPORTED_EXTENSIONS = {".pdf", ".txt"}

# Below this many characters, a page's real text layer is treated as
# "effectively empty" (e.g. just a page number) and OCR is attempted instead.
MIN_TEXT_LAYER_CHARS = 20

# Languages Tesseract should try to read, in order of the trained data
# packs installed on the host. "eng+spa" matches this project's English and
# multilingual (Spanish) test documents; override with OCR_LANGUAGES for a
# different deployment. TESSERACT_CMD/TESSDATA_PREFIX let a local dev
# machine point at a Tesseract install and language-data folder that aren't
# on the system PATH/default tessdata dir (see .env.example) - a Docker host
# with `apt-get install tesseract-ocr tesseract-ocr-spa` needs neither.
DEFAULT_OCR_LANGUAGES = "eng+spa"

_tesseract_cmd = os.environ.get("TESSERACT_CMD")
if _tesseract_cmd:
    pytesseract.pytesseract.tesseract_cmd = _tesseract_cmd


class UnsupportedFileType(ValueError):
    pass


def extract_text_from_upload(filename: str, content: bytes) -> str:
    """Dispatch on file extension. Raises UnsupportedFileType for anything
    else (caught by the route and turned into a 400)."""
    lower = filename.lower()
    if lower.endswith(".pdf"):
        return _extract_pdf(content)
    if lower.endswith(".txt"):
        return _extract_txt(content)
    raise UnsupportedFileType(
        f"Unsupported file type for '{filename}' - only PDF (.pdf) and plain text (.txt) are accepted."
    )


def _extract_pdf(content: bytes) -> str:
    pages = []
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        for page in pdf.pages:
            text = (page.extract_text() or "").strip()
            if len(text) < MIN_TEXT_LAYER_CHARS:
                ocr_text = _ocr_page(page)
                if len(ocr_text) > len(text):
                    text = ocr_text
            pages.append(text)
    return "\n\n".join(pages)


def _ocr_page(page) -> str:
    """Best-effort OCR fallback for a page with little or no real text
    layer. Never raises - a render/OCR failure just means this page
    contributes nothing, same as before OCR support existed."""
    try:
        image = page.to_image(resolution=200).original
    except Exception:
        return ""

    # TESSDATA_PREFIX (if set) is read by tesseract.exe itself from the
    # subprocess environment it inherits from this process - it does NOT go
    # through pytesseract's `config` string. That matters on Windows: pytesseract
    # splits `config` on whitespace without shell-style quote handling, so a
    # `--tessdata-dir "C:\path with spaces"` argument silently breaks apart at
    # each space instead of being treated as one quoted path.
    languages = os.environ.get("OCR_LANGUAGES") or DEFAULT_OCR_LANGUAGES
    try:
        return pytesseract.image_to_string(image, lang=languages).strip()
    except pytesseract.TesseractError:
        # A requested language pack isn't installed on this host (e.g. a
        # fresh deploy with only the default English data) - retry with
        # just English rather than losing the page entirely.
        try:
            return pytesseract.image_to_string(image, lang="eng").strip()
        except Exception:
            return ""
    except Exception:
        return ""


def _extract_txt(content: bytes) -> str:
    # Try UTF-8 first (most common), fall back to latin-1 (never fails,
    # covers Windows-saved text files that aren't UTF-8) rather than raising
    # a decode error on an otherwise-valid upload.
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError:
        return content.decode("latin-1")
