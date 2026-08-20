"""
Export every clause-pair comparison between two versions to a CSV, for
manual gold-standard annotation or re-scoring against an existing gold set.

Usage:
    python scripts/export_for_annotation.py --old 1 --new 2 --out data/annotation/v1_vs_v2_sbert.csv --method sbert

--method baseline (default): difflib + TF-IDF, as before.
--method sbert: Stage 3 semantic comparison.
"""
import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Base, Clause
from app.nlp.compare import compare_versions, ClauseRecord

DATABASE_URL = "sqlite:///./fire_regs.db"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--old", type=int, required=True)
    parser.add_argument("--new", type=int, required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--method", choices=["baseline", "sbert"], default="baseline")
    args = parser.parse_args()

    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()

    old_clauses = db.query(Clause).filter_by(version_id=args.old).order_by(Clause.order_index).all()
    new_clauses = db.query(Clause).filter_by(version_id=args.new).order_by(Clause.order_index).all()

    old_records = [ClauseRecord(c.clause_number, c.text, c.section_title) for c in old_clauses]
    new_records = [ClauseRecord(c.clause_number, c.text, c.section_title) for c in new_clauses]

    results = compare_versions(old_records, new_records, method=args.method)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "old_clause_number", "new_clause_number", "predicted_change_type",
            "similarity", "method", "old_text", "new_text",
            "gold_change_type", "notes",
        ])
        for r in results:
            writer.writerow([
                r.old_clause.clause_number if r.old_clause else "",
                r.new_clause.clause_number if r.new_clause else "",
                r.change_type,
                round(r.similarity, 4),
                r.method,
                r.old_clause.text if r.old_clause else "",
                r.new_clause.text if r.new_clause else "",
                "",
                "",
            ])

    print(f"Wrote {len(results)} rows to {out_path} (method={args.method})")


if __name__ == "__main__":
    main()
