"""
Routes for the General Document Comparison feature - upload any two
documents (PDF or .txt), no fixed schema, and compare/summarize them. All
endpoints require a logged-in user; uploads and comparisons are scoped to
that user only.
"""
import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.db.general_models import GeneralComparison, GeneralDocument
from app.db.models import User
from app.db.session import get_db
from app.ingestion.generic_extractor import UnsupportedFileType, extract_text_from_upload
from app.nlp.chunker import chunk_paragraphs
from app.nlp.generic_compare import compare_generic_documents
from app.nlp.summarizer import summarize_changes

router = APIRouter(prefix="/general", tags=["general-compare"])

MAX_UPLOAD_BYTES = 20 * 1024 * 1024  # 20MB - generous for a text-based PDF or .txt, guards against accidental huge uploads


# --- Documents -----------------------------------------------------------------

class GeneralDocumentResponse(BaseModel):
    id: int
    filename: str
    uploaded_at: datetime
    char_count: int


def _to_doc_response(row: GeneralDocument) -> GeneralDocumentResponse:
    return GeneralDocumentResponse(
        id=row.id, filename=row.filename, uploaded_at=row.uploaded_at, char_count=len(row.extracted_text)
    )


@router.post("/documents", response_model=GeneralDocumentResponse, status_code=201)
async def upload_document(
    file: UploadFile, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, f"File too large - max {MAX_UPLOAD_BYTES // (1024 * 1024)}MB")

    try:
        text = extract_text_from_upload(file.filename or "upload", content)
    except UnsupportedFileType as err:
        raise HTTPException(400, str(err))

    if not text.strip():
        raise HTTPException(400, "No extractable text found in this file (empty or scanned/image-only PDF?)")

    row = GeneralDocument(user_id=user.id, filename=file.filename or "upload", extracted_text=text)
    db.add(row)
    db.commit()
    db.refresh(row)
    return _to_doc_response(row)


@router.get("/documents", response_model=list[GeneralDocumentResponse])
def list_documents(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = (
        db.query(GeneralDocument)
        .filter_by(user_id=user.id)
        .order_by(GeneralDocument.uploaded_at.desc())
        .all()
    )
    return [_to_doc_response(r) for r in rows]


@router.delete("/documents/{document_id}", status_code=204)
def delete_document(document_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = db.query(GeneralDocument).filter_by(id=document_id, user_id=user.id).first()
    if row is None:
        raise HTTPException(404, "Document not found")
    db.delete(row)
    db.commit()


# --- Comparisons -----------------------------------------------------------------

class GeneralCompareRequest(BaseModel):
    doc_a_id: int
    doc_b_id: int
    method: str = "baseline"


class GeneralChangeOut(BaseModel):
    change_type: str
    old_text: str | None
    new_text: str | None
    similarity: float


class GeneralComparisonSummary(BaseModel):
    id: int
    doc_a_id: int
    doc_a_filename: str
    doc_b_id: int
    doc_b_filename: str
    method: str
    summary_core_similarities: str | None
    summary_unique_to_a: str | None
    summary_unique_to_b: str | None
    summary_contradictions: list[str]
    summary_provider: str  # "gemini" | "local"
    global_similarity: float
    unchanged_count: int
    added_count: int
    removed_count: int
    created_at: datetime


class GeneralComparisonDetail(GeneralComparisonSummary):
    changes: list[GeneralChangeOut]
    # Nested list [len(chunks_a)][len(chunks_b)] of similarity scores, for a
    # heatmap - None if the document pair was too large to be worth shipping
    # (see MAX_HEATMAP_CELLS in generic_compare.py).
    similarity_matrix: list[list[float]] | None
    chunks_a: list[str]
    chunks_b: list[str]


@router.post("/compare", response_model=GeneralComparisonDetail, status_code=201)
def compare_documents(
    body: GeneralCompareRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    if body.method not in ("baseline", "sbert", "multilingual"):
        raise HTTPException(400, "method must be 'baseline', 'sbert', or 'multilingual'")

    doc_a = db.query(GeneralDocument).filter_by(id=body.doc_a_id, user_id=user.id).first()
    doc_b = db.query(GeneralDocument).filter_by(id=body.doc_b_id, user_id=user.id).first()
    if doc_a is None or doc_b is None:
        raise HTTPException(404, "One or both documents not found")

    chunks_a = chunk_paragraphs(doc_a.extracted_text)
    chunks_b = chunk_paragraphs(doc_b.extracted_text)
    if not chunks_a or not chunks_b:
        raise HTTPException(400, "One or both documents had no usable paragraphs after chunking")

    result = compare_generic_documents(chunks_a, chunks_b, method=body.method)
    report = summarize_changes(result.changes)

    counts = {"unchanged": 0, "added": 0, "removed": 0}
    for c in result.changes:
        counts[c.change_type] += 1

    row = GeneralComparison(
        user_id=user.id,
        doc_a_id=doc_a.id,
        doc_b_id=doc_b.id,
        method=result.method_used,
        summary_core_similarities=report.core_similarities,
        summary_unique_to_a=report.unique_to_a,
        summary_unique_to_b=report.unique_to_b,
        summary_contradictions_json=json.dumps(report.contradictions),
        summary_provider=report.provider,
        changes_json=json.dumps(
            [
                {"change_type": c.change_type, "old_text": c.old_text, "new_text": c.new_text, "similarity": c.similarity}
                for c in result.changes
            ]
        ),
        similarity_matrix_json=json.dumps(result.similarity_matrix) if result.similarity_matrix is not None else None,
        chunks_a_json=json.dumps(chunks_a),
        chunks_b_json=json.dumps(chunks_b),
        global_similarity=result.global_similarity,
        unchanged_count=counts["unchanged"],
        added_count=counts["added"],
        removed_count=counts["removed"],
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    return GeneralComparisonDetail(
        id=row.id,
        doc_a_id=doc_a.id,
        doc_a_filename=doc_a.filename,
        doc_b_id=doc_b.id,
        doc_b_filename=doc_b.filename,
        method=row.method,
        summary_core_similarities=row.summary_core_similarities,
        summary_unique_to_a=row.summary_unique_to_a,
        summary_unique_to_b=row.summary_unique_to_b,
        summary_contradictions=json.loads(row.summary_contradictions_json) if row.summary_contradictions_json else [],
        summary_provider=row.summary_provider,
        global_similarity=row.global_similarity,
        unchanged_count=row.unchanged_count,
        added_count=row.added_count,
        removed_count=row.removed_count,
        created_at=row.created_at,
        changes=[GeneralChangeOut(**c) for c in json.loads(row.changes_json)],
        similarity_matrix=json.loads(row.similarity_matrix_json) if row.similarity_matrix_json else None,
        chunks_a=chunks_a,
        chunks_b=chunks_b,
    )


def _to_summary(row: GeneralComparison) -> GeneralComparisonSummary:
    return GeneralComparisonSummary(
        id=row.id,
        doc_a_id=row.doc_a_id,
        doc_a_filename=row.doc_a.filename,
        doc_b_id=row.doc_b_id,
        doc_b_filename=row.doc_b.filename,
        method=row.method,
        summary_core_similarities=row.summary_core_similarities,
        summary_unique_to_a=row.summary_unique_to_a,
        summary_unique_to_b=row.summary_unique_to_b,
        summary_contradictions=json.loads(row.summary_contradictions_json) if row.summary_contradictions_json else [],
        summary_provider=row.summary_provider,
        global_similarity=row.global_similarity,
        unchanged_count=row.unchanged_count,
        added_count=row.added_count,
        removed_count=row.removed_count,
        created_at=row.created_at,
    )


@router.get("/comparisons", response_model=list[GeneralComparisonSummary])
def list_comparisons(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = (
        db.query(GeneralComparison)
        .filter_by(user_id=user.id)
        .order_by(GeneralComparison.created_at.desc())
        .all()
    )
    return [_to_summary(r) for r in rows]


@router.get("/comparisons/{comparison_id}", response_model=GeneralComparisonDetail)
def get_comparison(comparison_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = db.query(GeneralComparison).filter_by(id=comparison_id, user_id=user.id).first()
    if row is None:
        raise HTTPException(404, "Comparison not found")
    summary = _to_summary(row)
    return GeneralComparisonDetail(
        **summary.model_dump(),
        changes=[GeneralChangeOut(**c) for c in json.loads(row.changes_json)],
        similarity_matrix=json.loads(row.similarity_matrix_json) if row.similarity_matrix_json else None,
        chunks_a=json.loads(row.chunks_a_json) if row.chunks_a_json else [],
        chunks_b=json.loads(row.chunks_b_json) if row.chunks_b_json else [],
    )


@router.delete("/comparisons/{comparison_id}", status_code=204)
def delete_comparison(comparison_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = db.query(GeneralComparison).filter_by(id=comparison_id, user_id=user.id).first()
    if row is None:
        raise HTTPException(404, "Comparison not found")
    db.delete(row)
    db.commit()
