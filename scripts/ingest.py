"""
Ingest one PDF into the database as a new DocumentVersion.

Usage:
    python scripts/ingest.py \
        --document "Approved Document B, Volume 1: Dwellings" \
        --label "2019 edition" \
        --pdf data/raw/adb_vol1_2019.pdf \
        --source-url "https://assets.publishing.service.gov.uk/media/.../....pdf"

Run this once per version you want in the database. The three versions
recommended for the MVP:
    1. --label "2019 edition"                       (base)
    2. --label "2019 edition + 2020 amendments"
    3. --label "2019 edition + 2020 and 2022 amendments"
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Base, Document, DocumentVersion, Clause
from app.ingestion.pdf_extractor import extract_full_text
from app.ingestion.clause_parser import parse_clauses

DATABASE_URL = "sqlite:///./fire_regs.db"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--document", required=True, help="Document title, e.g. 'Approved Document B, Volume 1'")
    parser.add_argument("--label", required=True, help="Version label, e.g. '2019 edition'")
    parser.add_argument("--pdf", required=True, help="Path to the downloaded PDF")
    parser.add_argument("--source-url", default=None)
    args = parser.parse_args()

    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    # Get-or-create the parent Document
    document = db.query(Document).filter_by(title=args.document).first()
    if document is None:
        document = Document(title=args.document, jurisdiction="UK-England")
        db.add(document)
        db.commit()
        db.refresh(document)
        print(f"Created new Document: {document.title} (id={document.id})")

    # Extract text
    txt_out = Path("data/samples") / (Path(args.pdf).stem + ".txt")
    print(f"Extracting text from {args.pdf} ...")
    full_text = extract_full_text(args.pdf, out_path=str(txt_out))
    page_count = full_text.count("\x0c") + 1
    print(f"Extracted {page_count} pages -> {txt_out}")

    # Create the version
    version = DocumentVersion(
        document_id=document.id,
        label=args.label,
        source_url=args.source_url,
        page_count=page_count,
        raw_text_path=str(txt_out),
    )
    db.add(version)
    db.commit()
    db.refresh(version)

    # Parse and store clauses
    print("Parsing clauses ...")
    parsed = parse_clauses(full_text)
    for c in parsed:
        db.add(Clause(
            version_id=version.id,
            clause_number=c.clause_number,
            section_title=c.section_title,
            text=c.text,
            page_number=c.page_number,
            order_index=c.order_index,
        ))
    db.commit()

    print(f"Ingested {len(parsed)} clauses into version '{version.label}' (version_id={version.id})")


if __name__ == "__main__":
    main()
