"""
Persistent company/job-posting store, backed by a database (SQLite by
default, or Postgres/MySQL/etc. via DATABASE_URL in .env).

Populated exclusively via POST /upload-companies (upload a job-requirement
PDF/DOCX and the LLM extracts role, required_skills, min_experience,
min_communication, description) — no hardcoded companies ship in this
module anymore. /companies starts empty until job postings are uploaded,
and data SURVIVES SERVER RESTARTS.

Same function names as the old hardcoded version (get_companies,
get_company) so routes/recommend.py needed no changes beyond the import.
"""
from typing import Optional

from sqlalchemy.orm import Session

from database.db import SessionLocal
from database.models import CompanyModel
from models.schemas import Company


def _next_id(db: Session) -> str:
    """Generate the next sequential company id, e.g. CO_A, CO_B, ... CO_Z, CO_AA, ..."""
    count = db.query(CompanyModel).count()
    letters = []
    n = count
    while True:
        n, rem = divmod(n, 26)
        letters.append(chr(ord("A") + rem))
        if n == 0:
            break
        n -= 1
    return "CO_" + "".join(reversed(letters))


def _to_schema(row: CompanyModel) -> Company:
    return Company(
        id=row.id,
        name=row.name,
        role=row.role,
        required_skills=row.required_skills or [],
        min_experience=row.min_experience or 0,
        min_communication=row.min_communication or "Average",
        description=row.description or "",
    )


def add_company(company_data: dict, source_filename: str) -> Company:
    db = SessionLocal()
    try:
        new_id = _next_id(db)
        row = CompanyModel(
            id=new_id,
            name=company_data.get("company_name") or company_data.get("name") or "Unknown Company",
            role=company_data.get("role") or company_data.get("job_title") or "",
            required_skills=company_data.get("required_skills") or company_data.get("skills") or [],
            min_experience=company_data.get("min_experience") or company_data.get("experience") or 0,
            min_communication=company_data.get("min_communication") or "Average",
            description=company_data.get("description") or company_data.get("job_description") or "",
            source_filename=source_filename,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return _to_schema(row)
    finally:
        db.close()


def get_companies() -> list[Company]:
    db = SessionLocal()
    try:
        rows = db.query(CompanyModel).order_by(CompanyModel.created_at.asc()).all()
        return [_to_schema(r) for r in rows]
    finally:
        db.close()


def get_company(company_id: str) -> Optional[Company]:
    db = SessionLocal()
    try:
        row = db.query(CompanyModel).filter(CompanyModel.id == company_id).first()
        return _to_schema(row) if row else None
    finally:
        db.close()


def clear_companies() -> None:
    db = SessionLocal()
    try:
        db.query(CompanyModel).delete()
        db.commit()
    finally:
        db.close()
