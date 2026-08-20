"""
Empirically calibrate SEMANTIC_UNCHANGED_THRESHOLD (and sanity-check the
existing difflib UNCHANGED_THRESHOLD) against your gold-standard CSV.

Usage:
    python scripts/calibrate_threshold.py --gold data/annotation/v1_vs_v2_clean.csv

What it does:
    1. For every gold-annotated row with old_text and new_text (i.e. every
       unchanged/modified pair - added/removed rows are skipped, since
       there's no pair to score), computes BOTH the difflib similarity and
       the SBERT semantic similarity.
    2. Sweeps candidate thresholds and reports precision/recall/F1 for
       "modified" at each one, for both methods.
    3. Prints the best threshold for each method, and the resulting metrics
       - so you get a direct, same-data comparison of difflib vs SBERT,
       which is exactly the ablation your dissertation needs.

Requires sentence-transformers with a working internet connection on first
run (downloads the model). Run this locally, not in a restricted sandbox.
"""
import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from difflib import SequenceMatcher


def difflib_sim(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def sweep_thresholds(sims: list[float], labels: list[str], candidates: list[float]) -> list[dict]:
    """
    labels: gold_change_type, one of 'unchanged'/'modified' per row (same
    order as sims). Returns a list of {threshold, precision, recall, f1}
    for the 'modified' class (sim below threshold = predicted modified).
    """
    rows = []
    for t in candidates:
        tp = fp = fn = tn = 0
        for sim, gold in zip(sims, labels):
            predicted_modified = sim < t
            gold_modified = gold == "modified"
            if predicted_modified and gold_modified:
                tp += 1
            elif predicted_modified and not gold_modified:
                fp += 1
            elif not predicted_modified and gold_modified:
                fn += 1
            else:
                tn += 1
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        rows.append({"threshold": t, "precision": precision, "recall": recall, "f1": f1, "tp": tp, "fp": fp, "fn": fn, "tn": tn})
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gold", required=True, help="path to gold-annotated CSV")
    parser.add_argument("--skip-sbert", action="store_true",
                         help="only run the difflib sweep (use if sentence-transformers/model isn't available here)")
    parser.add_argument("--model", choices=["sbert", "multilingual"], default="sbert",
                         help="which embedding model to calibrate: 'sbert' (English, all-MiniLM-L6-v2) or "
                              "'multilingual' (paraphrase-multilingual-MiniLM-L12-v2, for old/new versions in "
                              "different languages) - see MULTILINGUAL_UNCHANGED_THRESHOLD in app/nlp/compare.py")
    args = parser.parse_args()

    with open(args.gold, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    # Only rows with a real pair and a gold label of unchanged/modified are usable here
    usable = [r for r in rows if r.get("gold_change_type", "").strip() in ("unchanged", "modified")
              and r.get("old_text", "").strip() and r.get("new_text", "").strip()]

    if not usable:
        print("No usable rows found (need gold_change_type in {unchanged, modified} plus old_text/new_text).")
        return

    labels = [r["gold_change_type"].strip() for r in usable]
    old_texts = [r["old_text"] for r in usable]
    new_texts = [r["new_text"] for r in usable]

    print(f"Calibrating on {len(usable)} rows "
          f"({labels.count('unchanged')} unchanged, {labels.count('modified')} modified).\n")

    # --- difflib sweep ---
    difflib_sims = [difflib_sim(a, b) for a, b in zip(old_texts, new_texts)]
    difflib_candidates = sorted(set(round(s, 4) for s in difflib_sims) | {0.90, 0.95, 0.97, 0.99, 0.995, 0.999})
    difflib_results = sweep_thresholds(difflib_sims, labels, difflib_candidates)
    best_difflib = max(difflib_results, key=lambda r: r["f1"])

    print("=== difflib ===")
    print(f"Best threshold: {best_difflib['threshold']:.4f}  "
          f"(precision={best_difflib['precision']:.2f}, recall={best_difflib['recall']:.2f}, f1={best_difflib['f1']:.2f})")
    print(f"  TP={best_difflib['tp']} FP={best_difflib['fp']} FN={best_difflib['fn']} TN={best_difflib['tn']}\n")

    if args.skip_sbert:
        print("Skipped SBERT sweep (--skip-sbert). Run without that flag once sentence-transformers works locally.")
        return

    # --- embedding-model sweep (sbert or multilingual) ---
    model_label = "SBERT (all-MiniLM-L6-v2)" if args.model == "sbert" else "Multilingual (paraphrase-multilingual-MiniLM-L12-v2)"
    target_const = "SEMANTIC_UNCHANGED_THRESHOLD" if args.model == "sbert" else "MULTILINGUAL_UNCHANGED_THRESHOLD"
    try:
        from app.nlp.embeddings import paired_similarity
        model_sims = [float(s) for s in paired_similarity(old_texts, new_texts, model_key=args.model)]
    except Exception as e:
        print(f"Could not compute {model_label} similarities ({e}).")
        print("Make sure sentence-transformers is installed and you have internet access for the model download.")
        return

    model_candidates = sorted(set(round(s, 4) for s in model_sims) | {0.90, 0.95, 0.97, 0.99, 0.995, 0.999})
    model_results = sweep_thresholds(model_sims, labels, model_candidates)
    best_model = max(model_results, key=lambda r: r["f1"])

    print(f"=== {model_label} ===")
    print(f"Best threshold: {best_model['threshold']:.4f}  "
          f"(precision={best_model['precision']:.2f}, recall={best_model['recall']:.2f}, f1={best_model['f1']:.2f})")
    print(f"  TP={best_model['tp']} FP={best_model['fp']} FN={best_model['fn']} TN={best_model['tn']}\n")

    print("=== Per-row comparison (sorted by gold label) ===")
    print(f"{'old':>8}{'new':>8}{'gold':>12}{'difflib':>10}{args.model:>14}")
    for r, dsim, msim in sorted(zip(usable, difflib_sims, model_sims), key=lambda x: x[0]["gold_change_type"]):
        print(f"{r['old_clause_number']:>8}{r['new_clause_number']:>8}{r['gold_change_type']:>12}{dsim:>10.4f}{msim:>14.4f}")

    print(f"\nUpdate {target_const} in app/nlp/compare.py to {best_model['threshold']:.4f} based on this result.")


if __name__ == "__main__":
    main()
