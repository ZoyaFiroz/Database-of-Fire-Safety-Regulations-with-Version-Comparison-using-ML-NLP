"""
Database schema for the Fire Safety Regulations Version-Comparison project.

Design notes
------------
- `Document` is a logical regulation (e.g. "Approved Document B, Volume 1").
- `DocumentVersion` is one dated edition/amendment of a Document.
- `Clause` is a single numbered provision (e.g. "1.1", "5.3") within one
  DocumentVersion. Sub-items (a, b, i, ii...) are kept as part of the parent
  clause's text for v1 - we can split further later if needed.
- `ClauseMapping` records the ML/NLP pipeline's alignment between a clause in
  an "old" version and a clause in a "new" version, together with the
  similarity score and the classified change type. This is the core research
  artefact: it's what gets evaluated against manual annotation.
- `jurisdiction` on Document is included from day one so we don't have to
  retrofit the schema when we add non-UK regulations later.
"""

from datetime import datetime
import enum

from sqlalchemy import (
    Column, Integer, String, Text, Date, DateTime, ForeignKey, Float,
    Enum as SAEnum, UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class ChangeType(str, enum.Enum):
    UNCHANGED = "unchanged"
    MODIFIED = "modified"
    ADDED = "added"
    REMOVED = "removed"


class Document(Base):
    """A logical regulation, independent of any particular edition."""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)          # "Approved Document B, Volume 1: Dwellings"
    jurisdiction = Column(String(100), nullable=False, default="UK-England")
    source_url_base = Column(String(500))                  # gov.uk publication page
    description = Column(Text)

    versions = relationship("DocumentVersion", back_populates="document", cascade="all, delete-orphan")


class DocumentVersion(Base):
    """One dated edition/amendment of a Document."""
    __tablename__ = "document_versions"
    __table_args__ = (UniqueConstraint("document_id", "label", name="uq_document_version_label"),)

    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    label = Column(String(120), nullable=False)            # "2019 edition", "2019 + 2020 amendments"
    effective_date = Column(Date)                           # date the edition took effect
    source_url = Column(String(500))                        # exact PDF URL
    page_count = Column(Integer)
    raw_text_path = Column(String(500))                     # where extracted full text is stored on disk
    ingested_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", back_populates="versions")
    clauses = relationship("Clause", back_populates="version", cascade="all, delete-orphan")


class Clause(Base):
    """A single numbered clause within one DocumentVersion."""
    __tablename__ = "clauses"

    id = Column(Integer, primary_key=True)
    version_id = Column(Integer, ForeignKey("document_versions.id"), nullable=False)
    clause_number = Column(String(30), nullable=False)      # "1.1", "5.3", "B1" (requirement headers), "0.2"
    section_title = Column(String(255))                      # nearest preceding section/subsection heading
    text = Column(Text, nullable=False)
    page_number = Column(Integer)
    order_index = Column(Integer, nullable=False)            # position within the document, for sequence-based matching

    version = relationship("DocumentVersion", back_populates="clauses")


class ClauseMapping(Base):
    """
    An alignment between a clause in an older version and a clause in a
    newer version, produced by the comparison pipeline (or by a human
    annotator, distinguished via `source`).
    """
    __tablename__ = "clause_mappings"

    id = Column(Integer, primary_key=True)
    old_version_id = Column(Integer, ForeignKey("document_versions.id"), nullable=False)
    new_version_id = Column(Integer, ForeignKey("document_versions.id"), nullable=False)

    old_clause_id = Column(Integer, ForeignKey("clauses.id"), nullable=True)   # null if change_type == ADDED
    new_clause_id = Column(Integer, ForeignKey("clauses.id"), nullable=True)   # null if change_type == REMOVED

    similarity_score = Column(Float)                         # 0..1, from the comparison method used
    change_type = Column(SAEnum(ChangeType), nullable=False)
    method = Column(String(50))                               # "exact_number+difflib", "tfidf_cosine", "sbert", "manual"
    source = Column(String(20), default="automated")          # "automated" | "manual" (for gold-standard annotation)

    created_at = Column(DateTime, default=datetime.utcnow)


class User(Base):
    """A registered account on the Next.js frontend (login/signup)."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), nullable=False, unique=True)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    saved_comparisons = relationship("SavedComparison", back_populates="user", cascade="all, delete-orphan")
    clause_notes = relationship("ClauseNote", back_populates="user", cascade="all, delete-orphan")
    export_records = relationship("ExportRecord", back_populates="user", cascade="all, delete-orphan")


class SavedComparison(Base):
    """A version-pair + method a user bookmarked to revisit later."""
    __tablename__ = "saved_comparisons"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    old_version_id = Column(Integer, ForeignKey("document_versions.id"), nullable=False)
    new_version_id = Column(Integer, ForeignKey("document_versions.id"), nullable=False)
    method = Column(String(20), nullable=False)               # "baseline" | "sbert" | "multilingual"
    label = Column(String(255))                                 # optional user-given title, e.g. "For Ch.3 draft"
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="saved_comparisons")


class ClauseNote(Base):
    """A user's free-text note on one clause result within one comparison."""
    __tablename__ = "clause_notes"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    old_version_id = Column(Integer, ForeignKey("document_versions.id"), nullable=False)
    new_version_id = Column(Integer, ForeignKey("document_versions.id"), nullable=False)
    method = Column(String(20), nullable=False)
    old_clause_number = Column(String(30))                      # nullable - clause may be "added" (no old side)
    new_clause_number = Column(String(30))                      # nullable - clause may be "removed" (no new side)
    note_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="clause_notes")


class ExportRecord(Base):
    """
    Log of a user's past CSV/PDF exports. For CSV, csv_content is stored so
    it can be re-downloaded verbatim without re-running the comparison. PDF
    exports happen entirely client-side via the browser's print dialog, so
    there's no file to store server-side - this just logs what was exported
    and links back to the same comparison to re-open it.
    """
    __tablename__ = "export_records"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    old_version_id = Column(Integer, ForeignKey("document_versions.id"), nullable=False)
    new_version_id = Column(Integer, ForeignKey("document_versions.id"), nullable=False)
    method = Column(String(20), nullable=False)
    export_type = Column(String(10), nullable=False)            # "csv" | "pdf"
    filter_change_type = Column(String(20))                      # the active filter tab at export time, if any
    search_term = Column(String(255))                            # the active search text at export time, if any
    csv_content = Column(Text)                                    # only populated when export_type == "csv"
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="export_records")
