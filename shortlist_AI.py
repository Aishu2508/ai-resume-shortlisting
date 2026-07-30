"""
Persistent shortlist store — tracks whether a candidate has been
Shortlisted or Rejected for a specific company/job.

Follows the same pattern as data/candidate_store.py and data/companies.py.
"""
from typing import Optional

from sqlalchemy.orm import Session

from database.db import SessionLocal
from database.models import ShortlistModel
from models.schemas import ShortlistEntry, ShortlistCreate, ShortlistStatusUpdate


def _next_id(db: Session) -> str:
    """Generate the next sequential shortlist entry id, e.g. SL0001, SL0002, ..."""
    count = db.query(ShortlistModel).count()
    return f"SL{count + 1:04d}"


def _to_schema(row: ShortlistModel) -> ShortlistEntry:
    return ShortlistEntry(
        id=row.id,
        candidate_id=row.candidate_id,
        company_id=row.company_id,
        status=row.status,
        notes=row.notes or "",
        created_date=row.created_date,
        last_updated=row.last_updated,
    )


def add_shortlist_entry(data: ShortlistCreate) -> ShortlistEntry:
    db = SessionLocal()
    try:
        new_id = _next_id(db)
        row = ShortlistModel(
            id=new_id,
            candidate_id=data.candidate_id,
            company_id=data.company_id,
            status="Shortlisted",
            notes=data.notes or "",
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return _to_schema(row)
    finally:
        db.close()


def list_shortlist(
    status: Optional[str] = None,
    company_id: Optional[str] = None,
    candidate_id: Optional[str] = None,
) -> list[ShortlistEntry]:
    db = SessionLocal()
    try:
        q = db.query(ShortlistModel)
        if status:
            q = q.filter(ShortlistModel.status == status)
        if company_id:
            q = q.filter(ShortlistModel.company_id == company_id)
        if candidate_id:
            q = q.filter(ShortlistModel.candidate_id == candidate_id)
        rows = q.order_by(ShortlistModel.created_date.desc()).all()
        return [_to_schema(r) for r in rows]
    finally:
        db.close()


def get_shortlist_entry(entry_id: str) -> Optional[ShortlistEntry]:
    db = SessionLocal()
    try:
        row = db.query(ShortlistModel).filter(ShortlistModel.id == entry_id).first()
        return _to_schema(row) if row else None
    finally:
        db.close()


def update_shortlist_status(entry_id: str, data: ShortlistStatusUpdate) -> Optional[ShortlistEntry]:
    db = SessionLocal()
    try:
        row = db.query(ShortlistModel).filter(ShortlistModel.id == entry_id).first()
        if not row:
            return None
        row.status = data.status.value if hasattr(data.status, "value") else data.status
        if data.notes is not None:
            row.notes = data.notes
        db.commit()
        db.refresh(row)
        return _to_schema(row)
    finally:
        db.close()


def clear_shortlist() -> None:
    db = SessionLocal()
    try:
        db.query(ShortlistModel).delete()
        db.commit()
    finally:
        db.close()
