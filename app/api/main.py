"""
FastAPI app for the Fire Safety Regulations Version-Comparison project.

Run locally with:
    python -m uvicorn app.api.main:app --reload

The UI lives in nextjs/ (deployed separately) - this service is API-only.

Endpoints:
    GET  /                                         API root info (JSON)
    GET  /docs                                     Interactive Swagger API Documentation
    GET  /documents                                List regulations
    GET  /documents/{id}/versions                  List versions of a regulation
    GET  /versions/{id}/clauses                    List clauses in a version
    GET  /compare/{old_version_id}/{new_version_id}?method=sbert  Run comparison pipeline live
"""
from __future__ import annotations

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.db.models import Document, DocumentVersion, Clause
from app.db.session import get_db
from app.nlp.compare import (
    compare_versions, summarize, ClauseRecord,
    SEMANTIC_UNCHANGED_THRESHOLD, MULTILINGUAL_UNCHANGED_THRESHOLD, UNCHANGED_THRESHOLD,
)
from app.api.auth_routes import router as auth_router
from app.api.user_data_routes import router as user_data_router
from app.api.general_routes import router as general_router

app = FastAPI(
    title="Fire Safety Regulations Version Comparison API",
    description="NLP-driven version comparison engine for UK Fire Safety Building Regulations (Approved Document B).",
    version="1.0.0"
)

# Enable CORS for external web testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(user_data_router)
app.include_router(general_router)


@app.get("/")
def root():
    return JSONResponse(content={
        "message": "Fire Safety Regulations Version Comparison API is running",
        "documentation_url": "/docs",
        "endpoints": [
            "GET /docs (Interactive Swagger UI)",
            "GET /documents (List all documents)",
            "GET /documents/{id}/versions (List document versions)",
            "GET /versions/{id}/clauses (List clauses)",
            "GET /compare/{old_version_id}/{new_version_id}?method=sbert (Run live comparison)",
        ],
    })


@app.get("/documents")
def list_documents(db: Session = Depends(get_db)):
    docs = db.query(Document).all()
    return [{"id": d.id, "title": d.title, "jurisdiction": d.jurisdiction} for d in docs]


@app.get("/documents/{document_id}/versions")
def list_versions(document_id: int, db: Session = Depends(get_db)):
    versions = db.query(DocumentVersion).filter_by(document_id=document_id).all()
    if not versions:
        raise HTTPException(404, "No versions found for this document")
    return [
        {"id": v.id, "label": v.label, "effective_date": v.effective_date, "page_count": v.page_count}
        for v in versions
    ]


@app.get("/versions/{version_id}/clauses")
def list_clauses(version_id: int, db: Session = Depends(get_db)):
    clauses = db.query(Clause).filter_by(version_id=version_id).order_by(Clause.order_index).all()
    return [
        {"clause_number": c.clause_number, "section_title": c.section_title, "text": c.text}
        for c in clauses
    ]


# In-memory cache of full comparison results, keyed by (old, new, method).
# Clause data is static once ingested, so a version pair's result never
# changes within a server's lifetime - this makes every comparison after the
# first one instant instead of re-running SBERT (30-45s on CPU) each time.
_compare_cache: dict[tuple[int, int, str], dict] = {}


def _active_threshold(method: str, has_fallback: bool) -> float:
    if has_fallback:
        return UNCHANGED_THRESHOLD
    if method == "sbert":
        return SEMANTIC_UNCHANGED_THRESHOLD
    if method == "multilingual":
        return MULTILINGUAL_UNCHANGED_THRESHOLD
    return UNCHANGED_THRESHOLD


@app.get("/compare/{old_version_id}/{new_version_id}")
def compare(
    old_version_id: int,
    new_version_id: int,
    method: str = Query("baseline", description="Comparison pipeline method: 'baseline' (difflib+TFIDF, fast), 'sbert' (Sentence-BERT, English, semantic), or 'multilingual' (cross-language semantic, e.g. German vs English)"),
    db: Session = Depends(get_db)
):
    if method not in ("baseline", "sbert", "multilingual"):
        raise HTTPException(400, "Method must be 'baseline', 'sbert', or 'multilingual'")

    cache_key = (old_version_id, new_version_id, method)
    if cache_key in _compare_cache:
        return _compare_cache[cache_key]

    old_clauses = db.query(Clause).filter_by(version_id=old_version_id).order_by(Clause.order_index).all()
    new_clauses = db.query(Clause).filter_by(version_id=new_version_id).order_by(Clause.order_index).all()

    if not old_clauses or not new_clauses:
        raise HTTPException(404, "One or both versions have no ingested clauses")

    old_records = [ClauseRecord(c.clause_number, c.text, c.section_title) for c in old_clauses]
    new_records = [ClauseRecord(c.clause_number, c.text, c.section_title) for c in new_clauses]

    try:
        results = compare_versions(old_records, new_records, method=method)
    except Exception as e:
        raise HTTPException(500, f"Error in comparison pipeline: {str(e)}")

    has_fallback = any("fallback" in r.method for r in results)
    active_method = method if not has_fallback else f"{method} (fell back to baseline)"

    response_data = {
        "summary": summarize(results),
        "method": active_method,
        "active_threshold": _active_threshold(method, has_fallback),
        "changes": [
            {
                "change_type": r.change_type,
                "old_clause_number": r.old_clause.clause_number if r.old_clause else None,
                "new_clause_number": r.new_clause.clause_number if r.new_clause else None,
                "similarity": round(r.similarity, 4),
                "method": r.method,
                "old_text": r.old_clause.text if r.old_clause else None,
                "new_text": r.new_clause.text if r.new_clause else None,
            }
            for r in results
        ],
    }

    if has_fallback:
        response_data["warning"] = "Sentence-BERT model encountered an issue; pipeline gracefully degraded to baseline (difflib + TF-IDF)."
    else:
        # Don't cache fallback results - a transient SBERT failure shouldn't
        # be baked in permanently; a later request may succeed normally.
        _compare_cache[cache_key] = response_data

    return response_data


@app.get("/api/calibration")
def calibration_info():
    return {
        "sbert_model": "all-MiniLM-L6-v2",
        "multilingual_model": "paraphrase-multilingual-MiniLM-L12-v2",
        "semantic_unchanged_threshold": SEMANTIC_UNCHANGED_THRESHOLD,
        "multilingual_unchanged_threshold": MULTILINGUAL_UNCHANGED_THRESHOLD,
        "multilingual_threshold_calibrated": False,
        "baseline_unchanged_threshold": UNCHANGED_THRESHOLD,
    }
