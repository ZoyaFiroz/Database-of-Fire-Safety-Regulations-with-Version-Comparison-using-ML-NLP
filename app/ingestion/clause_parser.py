"""
Splits raw extracted text from Approved Document B into individual numbered
clauses (e.g. "1.1", "5.3"), each tagged with the nearest preceding section
heading.

This is a rule-based baseline (Step 1 of the project's research angle - see
literature review). It's intentionally simple and transparent so its
accuracy can be measured against manual annotation later.

Format notes learned from the real 2019 edition PDF text:
- Every page repeats "ONLINE VERSION" twice as a watermark - strip these.
- Every page has a running footer/header like:
  "Building Regulations 2010 Approved Document B Volume 1, 2019 edition 43"
  or just "43 Approved Document B Volume 1, 2019 edition Building Regulations 2010"
  - strip these too, they are not content.
- Section headings look like: "Section 4: Wall and ceiling linings"
- Requirement headings look like: "Requirement B2: Internal fire spread (linings)"
- Clauses start at the beginning of a line with "N.N " (e.g. "1.1 ", "0.3 ").
- Sub-items (a., b., i., ii.) are treated as part of the parent clause's text.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

NOISE_PATTERNS = [
    re.compile(r"O\s*N\s*L\s*I\s*N\s*E\s*V\s*E\s*R\s*S\s*I\s*O\s*N", re.IGNORECASE),
    re.compile(r"\b\d*\s*Approved Document B\b.*", re.IGNORECASE),
    re.compile(r"\bBuilding Regulations \d{4}\b.*", re.IGNORECASE),
    re.compile(r"^\s*B[1-5]\s*$"),
    re.compile(r"^\s*Diagram\s+\d+\.\d+.*$", re.IGNORECASE),
    re.compile(r"^\s*Table\s+\d+\.\d+.*$", re.IGNORECASE),
    re.compile(r"^\s*See\s+para.*$", re.IGNORECASE),
    re.compile(r"^\s*Stair\s+min\..*$", re.IGNORECASE),
]

SECTION_RE = re.compile(r"^Section\s+(\d+[A-Za-z]?):\s*(.+)$")
REQUIREMENT_RE = re.compile(r"^Requirement\s+(B\d):\s*(.+)$")
# Clause number at start of line, e.g. "1.1 ", "0.12 ", "12.34 " - followed by
# whitespace and then the clause text on the same line.
CLAUSE_RE = re.compile(r"^(\d{1,3}\.\d{1,3})\s+(.*)$")


def is_heading(line: str) -> bool:
    """Identify unnumbered subsection titles so they aren't attached to preceding clause text."""
    s = line.strip()
    if len(s) > 85:
        return False
    if s.endswith(".") or s.endswith(";") or s.endswith(":"):
        return False
    if re.search(r"\b(should|must|may|will|can|is|are|have|has|be|were|been)\b", s, re.IGNORECASE):
        return False
    return True


@dataclass
class ParsedClause:
    clause_number: str
    section_title: str | None
    text: str
    page_number: int | None
    order_index: int


def _strip_noise(raw_text: str) -> list[str]:
    """Remove watermark/header/footer lines, keep page markers (\\x0c)."""
    lines = raw_text.split("\n")
    cleaned = []
    for line in lines:
        l = line
        for pat in NOISE_PATTERNS:
            l = pat.sub("", l)
        stripped = l.strip()
        if stripped:
            cleaned.append(stripped)
    return cleaned


def _max_section_num(lines: list[str]) -> int | None:
    """Highest numbered section in the document (e.g. 17 for Volume 1, 19 for
    Volume 2) - used to recognise the real Appendix A heading (which follows
    the last numbered section) instead of the many inline "Appendix A: ..."
    mentions/cross-references that appear earlier in the body text."""
    nums = []
    for line in lines:
        m = SECTION_RE.match(line.strip())
        if m:
            sec_num_str = m.group(1).rstrip("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
            if sec_num_str.isdigit():
                nums.append(int(sec_num_str))
    return max(nums) if nums else None


def parse_clauses(raw_text: str) -> list[ParsedClause]:
    lines = _strip_noise(raw_text)
    final_section_num = _max_section_num(lines)

    clauses: list[ParsedClause] = []
    current_section_num: int | None = None
    current_section_title: str | None = None
    current_number: str | None = None
    current_text_parts: list[str] = []
    seen_clauses_in_section: set[str] = set()
    current_page = 1
    order_index = 0

    def flush():
        nonlocal current_number, current_text_parts, order_index
        if current_number is not None:
            text = " ".join(p.strip() for p in current_text_parts if p.strip())
            clauses.append(ParsedClause(
                clause_number=current_number,
                section_title=current_section_title,
                text=text,
                page_number=current_page,
                order_index=order_index,
            ))
            order_index += 1
        current_number = None
        current_text_parts = []

    for line in lines:
        if line == "\x0c":
            current_page += 1
            continue

        stripped = line.strip()
        if not stripped:
            continue

        # Ignore Table of Contents lines (headings ending with page numbers)
        if re.search(r"\s+\d+$", stripped) and (SECTION_RE.match(stripped) or REQUIREMENT_RE.match(stripped) or stripped.startswith("Appendix")):
            continue

        # Stop parsing main clauses when hitting the real Appendix A heading,
        # i.e. only once we're in the last numbered section - earlier inline
        # mentions like "Appendix A: Key terms" (front-matter appendix list)
        # or "(see Appendix A)" (cross-references) must not trigger this.
        if (current_section_num is not None and current_section_num == final_section_num
                and re.match(r"^Appendix\s+A\b", stripped)):
            flush()
            break

        section_match = SECTION_RE.match(stripped)
        requirement_match = REQUIREMENT_RE.match(stripped)
        clause_match = CLAUSE_RE.match(stripped)

        if section_match:
            flush()
            sec_num_str = section_match.group(1).rstrip("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
            if sec_num_str.isdigit():
                current_section_num = int(sec_num_str)
            current_section_title = f"Section {section_match.group(1)}: {section_match.group(2)}"
            seen_clauses_in_section = set()
            continue

        if requirement_match:
            flush()
            current_section_title = f"Requirement {requirement_match.group(1)}: {requirement_match.group(2)}"
            continue

        if clause_match:
            cand_num = clause_match.group(1)
            parts = cand_num.split(".")
            if parts[0].isdigit():
                cand_sec_prefix = int(parts[0])

                # Validation 1: Clause N.M must match current section N
                if current_section_num is not None and cand_sec_prefix != current_section_num:
                    if current_number is not None:
                        current_text_parts.append(stripped)
                    continue

            # Validation 2: Clause N.M cannot repeat within the same section (cross-reference wrapped line)
            if cand_num in seen_clauses_in_section:
                if current_number is not None:
                    current_text_parts.append(stripped)
                continue

            flush()
            current_number = cand_num
            seen_clauses_in_section.add(cand_num)
            current_text_parts = [clause_match.group(2)]
            continue

        # Continuation line (sub-item, wrapped text, etc.) - attach to current clause unless it's a section sub-heading
        if current_number is not None:
            if is_heading(stripped):
                continue
            current_text_parts.append(stripped)

    flush()
    return clauses


if __name__ == "__main__":
    import sys
    import json

    path = sys.argv[1] if len(sys.argv) > 1 else "data/samples/adb_vol1_2019_sample.txt"
    text = open(path, encoding="utf-8").read()
    result = parse_clauses(text)
    print(f"Parsed {len(result)} clauses from {path}\n")
    for c in result:
        preview = c.text[:80] + ("..." if len(c.text) > 80 else "")
        print(f"[{c.clause_number}] ({c.section_title}) p.{c.page_number}: {preview}")
