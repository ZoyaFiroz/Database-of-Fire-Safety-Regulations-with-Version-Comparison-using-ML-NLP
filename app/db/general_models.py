"""
Schema for the "General Document Comparison" feature - an isolated,
schema-free sibling to the main fire-safety-regulation pipeline (app/db/
models.py). Where the main schema is built around numbered clauses within a
known document family (Approved Document B), this one accepts *any* two
uploaded documents and chunks them generically (by paragraph), with no
assumption about structure, numbering, or subject matter.

Shares the same Base/database as the main schema (simplest ops - one
fire_regs.db file) but is intentionally kept in its own module and its own
tables, uncoupled from Document/DocumentVersion/Clause.
"""
from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship

from app.db.models import Base


class GeneralDocument(Base):
    """One uploaded file (PDF or .txt), text-extracted and ready to compare."""
    __tablename__ = "general_documents"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    extracted_text = Column(Text, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)


class GeneralComparison(Base):
    """
    A saved comparison between two GeneralDocuments. The full chunk-level
    diff and the generated summary are stored as-is (changes_json is a JSON
    string, not a normalized table - there's no fixed schema to normalize
    against here) so revisiting it later is instant, no recomputation.
    """
    __tablename__ = "general_comparisons"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    doc_a_id = Column(Integer, ForeignKey("general_documents.id"), nullable=False)
    doc_b_id = Column(Integer, ForeignKey("general_documents.id"), nullable=False)
    method = Column(String(20), nullable=False)               # "baseline" | "sbert" | "multilingual"
    summary_core_similarities = Column(Text)                    # what both documents share
    summary_unique_to_a = Column(Text)                          # what's unique to Document A
    summary_unique_to_b = Column(Text)                          # what's unique to Document B
    summary_contradictions_json = Column(Text)                  # JSON list of strings - only ever populated by the Gemini provider
    summary_provider = Column(String(20), default="local")      # "gemini" | "local" - which provider produced the summary fields above
    changes_json = Column(Text, nullable=False)                 # JSON list of {change_type, old_text, new_text, similarity}
    similarity_matrix_json = Column(Text)                       # JSON nested list [chunks_a][chunks_b]; null if too large to be worth storing
    chunks_a_json = Column(Text)                                 # JSON list of doc A's chunk texts, in order - heatmap row labels
    chunks_b_json = Column(Text)                                 # JSON list of doc B's chunk texts, in order - heatmap column labels
    global_similarity = Column(Float, default=0.0)              # 0..1 symmetric overall-similarity score, for the heatmap's headline number
    unchanged_count = Column(Integer, default=0)
    added_count = Column(Integer, default=0)
    removed_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    doc_a = relationship("GeneralDocument", foreign_keys=[doc_a_id])
    doc_b = relationship("GeneralDocument", foreign_keys=[doc_b_id])
