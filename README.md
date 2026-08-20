# Fire Safety Regulations — Version Comparison (MSc Project)

Database + ML/NLP pipeline + API for comparing versions of UK fire safety
regulations, starting with **Approved Document B, Volume 1 (Dwellings)**.

## Status

This is the MVP scaffold. It has been built and tested against **real text
extracted from the actual gov.uk PDF** (see `data/samples/`), proving the
clause-parsing and comparison logic works before you download the full
documents. What's not yet done: downloading the full PDFs (network-restricted
in this sandbox — you'll do this step), and the Stage 3 embeddings upgrade.

## The three versions to start with

| Label | Source |
|---|---|
| 2019 edition (base) | https://assets.publishing.service.gov.uk/media/677fa35a99c93b7286a3982b/Approved_Document_B__fire_safety__volume_1_-_Dwellings__2019_edition.pdf |
| 2019 + 2020 amendments | https://assets.publishing.service.gov.uk/media/677fa1366f01ae28ab5c0539/Approved_Document_B__fire_safety__volume_1_Dwellings__2019_edition_incorporating_2020_amendments.pdf |
| 2019 + 2020 + 2022 amendments | https://assets.publishing.service.gov.uk/media/67d02386f5aaff610c9f5f06/Approved_Document_B__fire_safety__volume_1_-_Dwellings__2019_edition_incorporating_2020_and_2022_amendments.pdf |

All three are 180-page, fully re-typeset official documents — ideal for
clause-level diffing. Government-published "amendment booklets" for the 2020
and 2022 changes are also on the [gov.uk publication
page](https://www.gov.uk/government/publications/fire-safety-approved-document-b)
— use these as your **manual/ground-truth reference** when evaluating pipeline
accuracy (this is your literature review's "evaluate accuracy of automated
version comparison vs manual annotation" objective).

## Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 1. Download the PDFs

Download the three PDFs above into `data/raw/`, e.g.:
```bash
mkdir -p data/raw
curl -L -o data/raw/adb_vol1_2019.pdf "https://assets.publishing.service.gov.uk/media/677fa35a99c93b7286a3982b/Approved_Document_B__fire_safety__volume_1_-_Dwellings__2019_edition.pdf"
curl -L -o data/raw/adb_vol1_2020.pdf "https://assets.publishing.service.gov.uk/media/677fa1366f01ae28ab5c0539/Approved_Document_B__fire_safety__volume_1_Dwellings__2019_edition_incorporating_2020_amendments.pdf"
curl -L -o data/raw/adb_vol1_2022.pdf "https://assets.publishing.service.gov.uk/media/67d02386f5aaff610c9f5f06/Approved_Document_B__fire_safety__volume_1_-_Dwellings__2019_edition_incorporating_2020_and_2022_amendments.pdf"
```

## 2. Ingest each version

```bash
python scripts/ingest.py --document "Approved Document B, Volume 1: Dwellings" \
    --label "2019 edition" --pdf data/raw/adb_vol1_2019.pdf

python scripts/ingest.py --document "Approved Document B, Volume 1: Dwellings" \
    --label "2019 + 2020 amendments" --pdf data/raw/adb_vol1_2020.pdf

python scripts/ingest.py --document "Approved Document B, Volume 1: Dwellings" \
    --label "2019 + 2020 + 2022 amendments" --pdf data/raw/adb_vol1_2022.pdf
```

Each run prints the assigned `version_id` — note these down.

## 3. Compare versions

Via CLI:
```bash
python scripts/compare_versions.py --old 1 --new 2
python scripts/compare_versions.py --old 1 --new 2 --only modified
```

Via the API:
```bash
uvicorn app.api.main:app --reload
# then visit http://127.0.0.1:8000/docs for interactive Swagger UI
```

## Project structure

```
app/
  db/models.py           SQLAlchemy schema: Document, DocumentVersion, Clause, ClauseMapping
  ingestion/
    pdf_extractor.py      PDF -> raw text (pdfplumber)
    clause_parser.py      raw text -> numbered clauses with section context
  nlp/
    compare.py             clause alignment + change classification (baseline + TF-IDF)
  api/
    main.py                 FastAPI app
scripts/
  ingest.py                 CLI: PDF -> database
  compare_versions.py       CLI: two versions -> readable diff
data/
  raw/                      put downloaded PDFs here (gitignored)
  samples/                  extracted text cache + the test excerpt used to validate parsing
```

## Already validated (see project chat history for full test output)

- **Clause parser**: correctly split a real excerpt of the 2019 edition into
  18 numbered clauses, correctly attributing each to its section/requirement
  heading, while stripping the "ONLINE VERSION" watermarks and running
  header/footer text that appear on every page.
- **Comparison pipeline**: correctly classified unchanged, modified, added,
  removed, *and* renumbered clauses in a simulated-amendment test. One
  finding worth writing up in your dissertation: a clause with a real
  technical change (fire alarm grade + a referenced standard's year) scored
  0.98 similarity — just above the 0.97 "unchanged" cutoff — showing that
  **threshold calibration against manual annotation is a genuine research
  question**, not a formality.

## Roadmap / next steps

1. **Download the real PDFs and run the full ingest** (Section 1-2 above) —
   confirms the parser holds up across all 180 pages x 3 versions, not just
   the excerpt.
2. **Build a small gold-standard annotation set**: manually mark ~30-50
   clause changes between two versions (the amendment booklets will help a
   lot here), store as `ClauseMapping` rows with `source="manual"`.
3. **Evaluate the baseline** (`compare_versions.py`) against the gold
   standard: precision/recall/F1, and tune `UNCHANGED_THRESHOLD` /
   `MIN_MATCH_THRESHOLD` in `app/nlp/compare.py`.
4. **Stage 3 upgrade**: swap TF-IDF for Sentence-BERT embeddings
   (`sentence-transformers`) in `align_unmatched()` for clauses that are
   reworded, not just renumbered. Compare accuracy against the TF-IDF
   baseline — this comparison is itself a nice result for your dissertation.
5. **Build the UI**: a simple side-by-side version viewer with diff
   highlighting, calling the `/compare/{old}/{new}` endpoint.
6. **Extend to Volume 2** and/or BS documents as a stretch goal, using the
   `jurisdiction` field already in the schema for the multi-country angle.
   Done — Volume 2 (Buildings other than dwellings) is ingested as a second
   `Document`; see `app/ingestion/clause_parser.py` for the fix that made the
   Appendix-boundary detection work for documents with a different section
   count than Volume 1.

## Cross-language comparison (Stage 3, multilingual)

A third comparison method, `method=multilingual`, lets the old and new
versions be in *different* languages (e.g. a German edition compared against
an English one) with no separate translation step: `app/nlp/embeddings.py`
adds `paraphrase-multilingual-MiniLM-L12-v2`, a sentence-embedding model
trained across ~50 languages into one shared vector space, so semantically
equivalent clauses in different languages land close together regardless of
lexical overlap.

Try it without ingesting any foreign-language document:
```bash
python scripts/demo_multilingual.py
```
This runs a handful of real EN/DE fire-safety clause pairs (an exact
translation, a translation with one substantive edit, and two unrelated
sentences) through the multilingual model and prints the similarity scores,
so you can see it correctly separates "same meaning, different language"
from "actually changed" from "unrelated" — without any German document
having been ingested into the database yet.

**Not yet calibrated**: `MULTILINGUAL_UNCHANGED_THRESHOLD` in
`app/nlp/compare.py` is a documented placeholder, not an empirically-derived
value — there's no gold-standard multilingual annotation set to calibrate
against yet (mirrors exactly the situation `SEMANTIC_UNCHANGED_THRESHOLD` was
in before Stage 3 was calibrated for English). Before citing multilingual
accuracy numbers in the dissertation, ingest a real bilingual document pair
and run `scripts/calibrate_threshold.py` against it, same as was done for the
English pipeline.
