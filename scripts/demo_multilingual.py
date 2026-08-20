"""
Proof-of-concept: cross-language clause comparison (e.g. old version in
German, new version in English) using the "multilingual" method added to
app/nlp/embeddings.py / app/nlp/compare.py.

This does NOT require an ingested German document - it demonstrates the
underlying capability directly against a handful of example clause pairs, so
you can see the multilingual model correctly:
  1. Scores a genuine EN/DE translation pair as highly similar ("unchanged").
  2. Scores a translated pair with one real substantive edit as meaningfully
     lower than the exact-translation pair (the model can tell a real
     wording change apart from a correct translation, cross-lingually).
  3. Scores two unrelated sentences (one EN, one DE, different topics) as low.

Usage:
    python scripts/demo_multilingual.py

First run downloads the multilingual model (~470MB) - needs internet access.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Windows consoles often default to a non-UTF-8 codepage, which garbles the
# German special characters (ü, ß, ä) in printed output - force UTF-8 so the
# demo is readable regardless of the terminal's default encoding.
if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from app.nlp.embeddings import paired_similarity

EXAMPLES = [
    (
        "Exact translation (should score HIGH - 'unchanged')",
        "All dwellings should have a fire detection and alarm system, minimum "
        "Grade D2 Category LD3 standard, in accordance with the relevant "
        "recommendations of BS 5839-6.",
        "Alle Wohngebäude sollten über eine Brandmeldeanlage der Mindestklasse "
        "D2 Kategorie LD3 verfügen, gemäß den einschlägigen Empfehlungen der "
        "BS 5839-6.",
    ),
    (
        "Translation with one real edit: 'mains' -> 'battery' operated "
        "(should score MEDIUM - a genuine cross-lingual 'modified' detection)",
        "Smoke alarms should be mains operated and conform to BS EN 14604.",
        "Rauchmelder sollten batteriebetrieben sein und der Norm BS EN 14604 "
        "entsprechen.",
    ),
    (
        "Unrelated topic in each language (should score LOW - correctly 'not a match')",
        "Smoke alarms should be mains operated and conform to BS EN 14604.",
        "Der Bahnhof befindet sich in der Nähe des Stadtzentrums und ist gut "
        "an den öffentlichen Nahverkehr angebunden.",
    ),
]


def main():
    print("Loading multilingual model and computing cross-language similarity...\n")
    en_texts = [ex[1] for ex in EXAMPLES]
    de_texts = [ex[2] for ex in EXAMPLES]
    sims = paired_similarity(en_texts, de_texts, model_key="multilingual")

    for (label, en, de), sim in zip(EXAMPLES, sims):
        print(f"--- {label} ---")
        print(f"  EN: {en}")
        print(f"  DE: {de}")
        print(f"  Cross-lingual similarity: {sim:.4f}\n")

    print(
        "For comparison, MULTILINGUAL_UNCHANGED_THRESHOLD in app/nlp/compare.py "
        "is currently a placeholder (0.92) - see that file's comment for why it "
        "still needs real gold-standard calibration before dissertation use."
    )


if __name__ == "__main__":
    main()
