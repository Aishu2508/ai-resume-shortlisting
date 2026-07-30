"""
SQLAlchemy ORM models for persisted candidates and companies.
"""
from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, Text, DateTime, JSON

from database.db import Base


class CandidateModel(Base):
    __tablename__ = "candidates"

    # Internal auto-increment PK (row identity)
    row_id = Column(Integer, primary_key=True, autoincrement=True)

    # Public-facing id used throughout the API, e.g. "C001"
    id = Column(String(20), unique=True, index=True, nullable=False)

    name = Column(String(255), default="")
    skills = Column(JSON, default=list)             # list[str]
    experience_years = Column(Float, default=0)
    projects = Column(JSON, default=list)             # list[str]
    resume_summary = Column(Text, default="")
    source_filename = Column(String(255), nullable=True)

    # Stored as a JSON dict matching InterviewFeedback fields, or null
    interview_feedback = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)


class CompanyModel(Base):
    __tablename__ = "companies"

    row_id = Column(Integer, primary_key=True, autoincrement=True)

    # Public-facing id, e.g. "CO_A"
    id = Column(String(20), unique=True, index=True, nullable=False)

    name = Column(String(255), default="")
    role = Column(String(255), default="")
    required_skills = Column(JSON, default=list)     # list[str]
    min_experience = Column(Float, default=0)
    min_communication = Column(String(50), default="Average")
    description = Column(Text, default="")
    source_filename = Column(String(255), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)


class ShortlistModel(Base):
    __tablename__ = "shortlist"

    row_id = Column(Integer, primary_key=True, autoincrement=True)

    # Public-facing id, e.g. "SL0001"
    id = Column(String(20), unique=True, index=True, nullable=False)

    candidate_id = Column(String(20), nullable=False)
    company_id = Column(String(20), nullable=False)
    status = Column(String(20), default="Shortlisted")
    notes = Column(Text, default="")

    created_date = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
