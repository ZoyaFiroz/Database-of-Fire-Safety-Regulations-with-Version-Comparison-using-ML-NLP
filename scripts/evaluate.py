"""
Evaluate the comparison pipeline's predictions against your completed
gold-standard CSV (see export_for_annotation.py).

Usage:
    python scripts/evaluate.py --gold data/annotation/v1_vs_v2.csv

Prints per-category precision/recall/F1 and a macro average, plus a
confusion matrix so you can see exactly which categories the pipeline
confuses (e.g. calling a "modified" clause "unchanged" - which is the
threshold problem flagged in the interim report).
"""
import argparse
import csv
from collections import defaultdict

CATEGORIES = ["unchanged", "modified", "added", "removed"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gold", required=True, help="path to the completed annotation CSV")
    args = parser.parse_args()

    rows = []
    ceiling_rows = []
    with open(args.gold, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            gold = row["gold_change_type"].strip().lower()
            if not gold:
                continue  # skip un-annotated rows
            if gold not in CATEGORIES:
                print(f"WARNING: unrecognised gold_change_type '{gold}' - skipping row "
                      f"({row['old_clause_number']} -> {row['new_clause_number']})")
                continue

            # A "modified" clause whose extracted text is byte-identical between
            # versions can never be caught by a text-similarity method (similarity
            # is 1.0, same as a genuinely unchanged clause) - the real change is
            # almost certainly in a referenced diagram/table, not the clause text.
            # Score these separately instead of counting them as pipeline errors.
            if gold == "modified" and row["old_text"].strip() and row["old_text"].strip() == row["new_text"].strip():
                ceiling_rows.append(row)
                continue

            rows.append((row["predicted_change_type"].strip().lower(), gold))

    if not rows:
        print("No annotated rows found (gold_change_type column is empty). "
              "Fill in some rows in the CSV first.")
        return

    print(f"Evaluating on {len(rows)} annotated rows.\n")

    if ceiling_rows:
        print(f"NOTE: excluded {len(ceiling_rows)} gold 'modified' row(s) with byte-identical "
              "old/new text - no text-similarity method can detect these (likely diagram/table-only "
              "changes outside the clause text). Listed separately, not counted as errors:")
        for r in ceiling_rows:
            print(f"  {r['old_clause_number']} -> {r['new_clause_number']}  "
                  f"(predicted: {r['predicted_change_type']})")
        print()

    # Confusion matrix: confusion[gold][predicted] = count
    confusion = defaultdict(lambda: defaultdict(int))
    for predicted, gold in rows:
        confusion[gold][predicted] += 1

    print("Confusion matrix (rows = gold truth, columns = predicted):")
    header = "gold\\pred".ljust(12) + "".join(c.ljust(12) for c in CATEGORIES)
    print(header)
    for gold in CATEGORIES:
        line = gold.ljust(12)
        for pred in CATEGORIES:
            line += str(confusion[gold][pred]).ljust(12)
        print(line)
    print()

    # Precision / Recall / F1 per category
    print(f"{'Category':<12}{'Precision':<12}{'Recall':<12}{'F1':<12}{'Support':<10}")
    f1_scores = []
    for cat in CATEGORIES:
        tp = confusion[cat][cat]
        fn = sum(confusion[cat][p] for p in CATEGORIES if p != cat)
        fp = sum(confusion[g][cat] for g in CATEGORIES if g != cat)
        support = tp + fn

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        if support > 0:
            f1_scores.append(f1)

        print(f"{cat:<12}{precision:<12.2f}{recall:<12.2f}{f1:<12.2f}{support:<10}")

    macro_f1 = sum(f1_scores) / len(f1_scores) if f1_scores else 0.0
    print(f"\nMacro-average F1: {macro_f1:.3f}")


if __name__ == "__main__":
    main()
