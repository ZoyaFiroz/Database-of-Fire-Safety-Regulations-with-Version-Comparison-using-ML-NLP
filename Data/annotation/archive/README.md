# Archived — pre-parser-fix annotation exports

These six CSVs (390 comparison rows each) were generated before the clause
parser was fixed to stop clause text from running away into later Appendix
content. In this batch, clause "2.5" absorbed **27,845 characters** of
unrelated Appendix B–E text (vs. 1,429 chars in the current, correct parse),
and several other clauses were duplicated.

All 53 unique gold-labelled clause pairs across
`v1_vs_v2_reparsed_final.csv` / `_gold_corrected.csv` / `_annotated.csv` are
already present in `../v1_vs_v2_clean_gold.csv` (the current 381-row parse),
so no annotation work is lost by archiving these. Kept for reference only —
do not evaluate against them, the similarity scores for anything touching
clause 2.5 are meaningless (SBERT's 256-token limit truncated before the
real edit, reporting ~1.0 similarity despite genuine content differences).
