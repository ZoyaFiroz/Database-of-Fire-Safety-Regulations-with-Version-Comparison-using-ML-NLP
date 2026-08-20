"""
Print the full text of one clause number, across one or two versions, so you
can sanity-check what the comparison pipeline actually saw. Use this before
trusting any flagged "modified"/"added"/"removed" result.

Usage:
    # single version
    python scripts/inspect_clause.py --version 1 --clause 12.2

    # side-by-side across two versions (what compare_versions.py compared)
    python scripts/inspect_clause.py --old 1 --new 2 --clause 12.2
"""
import argparse
import sys
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Base, Clause, DocumentVersion

DATABASE_URL = "sqlite:///./fire_regs.db"


def show(db, version_id, clause_number):
    v = db.query(DocumentVersion).get(version_id)
    c = db.query(Clause).filter_by(version_id=version_id, clause_number=clause_number).first()
    print(f"\n--- Version {version_id} ({v.label if v else '?'}) — Clause {clause_number} ---")
    if c is None:
        print("  [not found in this version]")
        return
    print(f"  Section: {c.section_title}")
    print(f"  Page: {c.page_number}")
    print(textwrap.fill(c.text, width=90, initial_indent="  ", subsequent_indent="  "))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", type=int, help="single version_id to inspect")
    parser.add_argument("--old", type=int, help="old version_id (for side-by-side)")
    parser.add_argument("--new", type=int, help="new version_id (for side-by-side)")
    parser.add_argument("--clause", required=True, help="clause number, e.g. 12.2")
    args = parser.parse_args()

    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()

    if args.version:
        show(db, args.version, args.clause)
    elif args.old and args.new:
        show(db, args.old, args.clause)
        show(db, args.new, args.clause)
    else:
        print("Specify either --version, or both --old and --new.")


if __name__ == "__main__":
    main()
