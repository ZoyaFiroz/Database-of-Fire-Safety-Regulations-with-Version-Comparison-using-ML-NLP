"""
Compare two already-ingested versions and print a readable summary.

Usage:
    python scripts/compare_versions.py --old 1 --new 2
    python scripts/compare_versions.py --old 1 --new 2 --method sbert
    python scripts/compare_versions.py --old 1 --new 2 --only modified

--method baseline (default): difflib + TF-IDF, as before.
--method sbert: Stage 3 semantic comparison. Requires sentence-transformers
                and internet access on first run (model download).
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Base, Clause
from app.nlp.compare import compare_versions, summarize, ClauseRecord

DATABASE_URL = "sqlite:///./fire_regs.db"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--old", type=int, required=True, help="old version_id")
    parser.add_argument("--new", type=int, required=True, help="new version_id")
    parser.add_argument("--method", choices=["baseline", "sbert", "multilingual"], default="baseline")
    parser.add_argument("--only", choices=["added", "removed", "modified", "unchanged"], default=None,
                         help="filter output to one change type")
    args = parser.parse_args()

    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()

    old_clauses = db.query(Clause).filter_by(version_id=args.old).order_by(Clause.order_index).all()
    new_clauses = db.query(Clause).filter_by(version_id=args.new).order_by(Clause.order_index).all()
    if not old_clauses or not new_clauses:
        print("One or both versions have no ingested clauses. Run scripts/ingest.py first.")
        return

    old_records = [ClauseRecord(c.clause_number, c.text, c.section_title) for c in old_clauses]
    new_records = [ClauseRecord(c.clause_number, c.text, c.section_title) for c in new_clauses]

    results = compare_versions(old_records, new_records, method=args.method)

    for r in results:
        if args.only and r.change_type != args.only:
            continue
        old_num = r.old_clause.clause_number if r.old_clause else "-"
        new_num = r.new_clause.clause_number if r.new_clause else "-"
        print(f"{r.change_type:10s} | {old_num:>6s} -> {new_num:<6s} | sim={r.similarity:.3f} | {r.method}")

    print(f"\nMethod: {args.method}")
    print("Summary:", summarize(results))


if __name__ == "__main__":
    main()
