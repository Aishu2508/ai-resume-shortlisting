"""
Persistent candidate store, backed by a database (SQLite by default, or
Postgres/MySQL/etc. via DATABASE_URL in .env). Populated exclusively via
/upload-resumes — /candidates starts empty until resumes are uploaded, but
now SURVIVES SERVER RESTARTS.

Function signatures are unchanged from the in-memory version, so routes.py
and services/recommender.py needed zero changes.
"""
from typing import Optional

from sqlalchemy.orm import Session

from database.db import SessionLocal
from database.models import CandidateModel
from models.schemas import Candidate, InterviewFeedback, InterviewFeedbackUpdate


def _next_id(db: Session) -> str:
    """Generate the next sequential candidate id, e.g. C001, C002, ..."""
    count = db.query(CandidateModel).count()
    return f"C{count + 1:03d}"


def _to_schema(row: CandidateModel) -> Candidate:
    return Candidate(
        id=row.id,
        name=row.name,
        skills=row.skills or [],
        experience_years=row.experience_years or 0,
        projects=row.projects or [],
        resume_summary=row.resume_summary or "",
        source_filename=row.source_filename,
        interview_feedback=InterviewFeedback(**row.interview_feedback) if row.interview_feedback else None,
    )


def add_candidate(candidate_data: dict, source_filename: str) -> Candidate:
    db = SessionLocal()
    try:
        new_id = _next_id(db)
        row = CandidateModel(
            id=new_id,
            name=candidate_data.get("name") or "Unknown Candidate",
            skills=candidate_data.get("skills") or [],
            experience_years=candidate_data.get("experience_years") or 0,
            projects=candidate_data.get("projects") or [],
            resume_summary=candidate_data.get("resume_summary") or "",
            source_filename=source_filename,
            interview_feedback=None,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return _to_schema(row)
    finally:
        db.close()


def get_candidates() -> list[Candidate]:
    db = SessionLocal()
    try:
        rows = db.query(CandidateModel).order_by(CandidateModel.created_at.asc()).all()
        return [_to_schema(r) for r in rows]
    finally:
        db.close()


def get_candidate(candidate_id: str) -> Optional[Candidate]:
    db = SessionLocal()
    try:
        row = db.query(CandidateModel).filter(CandidateModel.id == candidate_id).first()
        return _to_schema(row) if row else None
    finally:
        db.close()


def update_interview_feedback(candidate_id: str, feedback: InterviewFeedbackUpdate) -> Optional[Candidate]:
    db = SessionLocal()
    try:
        row = db.query(CandidateModel).filter(CandidateModel.id == candidate_id).first()
        if not row:
            return None
        row.interview_feedback = feedback.model_dump(exclude_none=True)
        db.commit()
        db.refresh(row)
        return _to_schema(row)
    finally:
        db.close()


def clear_candidates() -> None:
    db = SessionLocal()
    try:
        db.query(CandidateModel).delete()
        db.commit()
    finally:
        db.close()
