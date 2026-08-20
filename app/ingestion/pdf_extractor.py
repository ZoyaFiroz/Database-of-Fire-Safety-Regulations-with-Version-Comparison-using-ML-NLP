"""
Extracts raw text (page by page) from a PDF using pdfplumber.

Approved Document B is a native, text-based PDF (not scanned), so plain
text extraction works well - no OCR needed. Run `pip install pdfplumber`.
"""
from pathlib import Path
import pdfplumber


def extract_pages(pdf_path: str) -> list[str]:
    """Return a list of per-page raw text strings."""
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            pages.append(text)
    return pages


def extract_full_text(pdf_path: str, out_path: str | None = None) -> str:
    """
    Extract all pages, join with a page-break marker (so downstream code can
    still recover page numbers if needed), and optionally write to disk.
    """
    pages = extract_pages(pdf_path)
    full_text = "\n\x0c\n".join(pages)  # \x0c = form feed, used as an explicit page marker
    if out_path:
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        Path(out_path).write_text(full_text, encoding="utf-8")
    return full_text


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python pdf_extractor.py <input.pdf> <output.txt>")
        sys.exit(1)
    extract_full_text(sys.argv[1], sys.argv[2])
    print(f"Extracted text written to {sys.argv[2]}")
