"""
Per-user saved data for the Next.js frontend: bookmarked comparisons,
per-clause notes, and export history. Everything here requires a logged-in
user (get_current_user) and only ever reads/writes that user's own rows.
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.db.models import ClauseNote, ExportRecord, SavedComparison, User
from app.db.session import get_db

router = APIRouter(tags=["user-data"])


# --- Saved comparisons -------------------------------------------------------

class SavedComparisonCreate(BaseModel):
    old_version_id: int
    new_version_id: int
    method: str
    label: str | None = None


class SavedComparisonResponse(BaseModel):
    id: int
    old_version_id: int
    new_version_id: int
    method: str
    label: str | None
    created_at: datetime


@router.post("/saved-comparisons", response_model=SavedComparisonResponse, status_code=201)
def create_saved_comparison(
    body: SavedComparisonCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    row = SavedComparison(user_id=user.id, **body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/saved-comparisons", response_model=list[SavedComparisonResponse])
def list_saved_comparisons(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return (
        db.query(SavedComparison)
        .filter_by(user_id=user.id)
        .order_by(SavedComparison.created_at.desc())
        .all()
    )


@router.delete("/saved-comparisons/{comparison_id}", status_code=204)
def delete_saved_comparison(
    comparison_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    row = db.query(SavedComparison).filter_by(id=comparison_id, user_id=user.id).first()
    if row is None:
        raise HTTPException(404, "Saved comparison not found")
    db.delete(row)
    db.commit()


# --- Clause notes -------------------------------------------------------------

class ClauseNoteUpsert(BaseModel):
    old_version_id: int
    new_version_id: int
    method: str
    old_clause_number: str | None = None
    new_clause_number: str | None = None
    note_text: str = Field(min_length=1, max_length=5000)


class ClauseNoteResponse(BaseModel):
    id: int
    old_version_id: int
    new_version_id: int
    method: str
    old_clause_number: str | None
    new_clause_number: str | None
    note_text: str
    created_at: datetime
    updated_at: datetime


@router.post("/clause-notes", response_model=ClauseNoteResponse, status_code=201)
def upsert_clause_note(
    body: ClauseNoteUpsert, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    existing = (
        db.query(ClauseNote)
        .filter_by(
            user_id=user.id,
            old_version_id=body.old_version_id,
            new_version_id=body.new_version_id,
            method=body.method,
            old_clause_number=body.old_clause_number,
            new_clause_number=body.new_clause_number,
        )
        .first()
    )
    if existing is not None:
        existing.note_text = body.note_text
        existing.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing

    row = ClauseNote(user_id=user.id, **body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/clause-notes", response_model=list[ClauseNoteResponse])
def list_clause_notes(
    old_version_id: int,
    new_version_id: int,
    method: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return (
        db.query(ClauseNote)
        .filter_by(
            user_id=user.id, old_version_id=old_version_id, new_version_id=new_version_id, method=method
        )
        .all()
    )


@router.delete("/clause-notes/{note_id}", status_code=204)
def delete_clause_note(note_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = db.query(ClauseNote).filter_by(id=note_id, user_id=user.id).first()
    if row is None:
        raise HTTPException(404, "Note not found")
    db.delete(row)
    db.commit()


# --- Export history -----------------------------------------------------------

class ExportRecordCreate(BaseModel):
    old_version_id: int
    new_version_id: int
    method: str
    export_type: str = Field(pattern="^(csv|pdf)$")
    filter_change_type: str | None = None
    search_term: str | None = None
    csv_content: str | None = None  # only meaningful when export_type == "csv"


class ExportRecordResponse(BaseModel):
    id: int
    old_version_id: int
    new_version_id: int
    method: str
    export_type: str
    filter_change_type: str | None
    search_term: str | None
    created_at: datetime
    has_stored_content: bool


def _to_export_response(row: ExportRecord) -> ExportRecordResponse:
    return ExportRecordResponse(
        id=row.id,
        old_version_id=row.old_version_id,
        new_version_id=row.new_version_id,
        method=row.method,
        export_type=row.export_type,
        filter_change_type=row.filter_change_type,
        search_term=row.search_term,
        created_at=row.created_at,
        has_stored_content=bool(row.csv_content),
    )


@router.post("/exports", response_model=ExportRecordResponse, status_code=201)
def log_export(body: ExportRecordCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = ExportRecord(user_id=user.id, **body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return _to_export_response(row)


@router.get("/exports", response_model=list[ExportRecordResponse])
def list_exports(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.query(ExportRecord).filter_by(user_id=user.id).order_by(ExportRecord.created_at.desc()).all()
    return [_to_export_response(r) for r in rows]


@router.get("/exports/{export_id}/download")
def download_export(export_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = db.query(ExportRecord).filter_by(id=export_id, user_id=user.id).first()
    if row is None:
        raise HTTPException(404, "Export record not found")
    if row.export_type != "csv" or not row.csv_content:
        raise HTTPException(
            400,
            "This export has no stored file to re-download - PDF exports are generated entirely in "
            "your browser's print dialog and were never sent to the server, so only the CSV type can "
            "be re-downloaded here.",
        )
    return PlainTextResponse(
        row.csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="export-{row.id}.csv"'},
    )
