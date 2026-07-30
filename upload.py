"""
POST /upload-resumes
Accepts MULTIPLE resume files (PDF/DOCX) in one request, parses each one via
the LLM, and adds them to the candidate pool that /candidates,
/recommend/{company_id}, /recommend-all, and /recommend-from-prompt all read
from — replacing the old hardcoded candidate list.

POST /upload-companies
Accepts MULTIPLE job-requirement documents (PDF/DOCX) in one request, parses
each one via the LLM into company/role fields, and adds them to the company
pool that /companies and /recommend/{company_id} read from — replacing the
old hardcoded company list.

DELETE /candidates
DELETE /companies
Clear the respective pool (handy for re-testing/demos).
"""
import os
import uuid
from typing import List

from fastapi import APIRouter, UploadFile, File, HTTPException

from config import settings
from data.candidate_store import add_candidate, clear_candidates
from data.companies import add_company, clear_companies
from services.resume_parser import extract_resume_text
from services.resume_extractor import extract_candidate_details
from services.company_extractor import extract_company_details

router = APIRouter(tags=["Uploads"])


@router.post("/upload-resumes", tags=["Candidates"])
async def upload_resumes(files: List[UploadFile] = File(...)):
    """Upload one or more candidate resumes (PDF/DOCX) in a single multipart request."""
    if not files:
        raise HTTPException(status_code=400, detail="No files provided.")

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    added, failed = [], []

    for file in files:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in (".pdf", ".docx", ".doc"):
            failed.append({"filename": file.filename, "reason": f"Unsupported file type: {ext}"})
            continue

        try:
            save_path = os.path.join(settings.UPLOAD_DIR, f"{uuid.uuid4().hex}_{file.filename}")
            with open(save_path, "wb") as f:
                f.write(await file.read())

            raw_text = extract_resume_text(save_path)
            if not raw_text:
                failed.append({"filename": file.filename, "reason": "Could not extract any text."})
                continue

            details = extract_candidate_details(raw_text)
            candidate = add_candidate(details, source_filename=file.filename)
            added.append(candidate)

        except Exception as exc:
            failed.append({"filename": file.filename, "reason": str(exc)})

    return {
        "message": f"Processed {len(files)} file(s): {len(added)} added, {len(failed)} failed.",
        "added_candidates": added,
        "failed": failed,
    }


@router.post("/upload-companies", tags=["Companies"])
async def upload_companies(files: List[UploadFile] = File(...)):
    """Upload one or more job-requirement documents (PDF/DOCX) in a single multipart request."""
    if not files:
        raise HTTPException(status_code=400, detail="No files provided.")

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    added, failed = [], []

    for file in files:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in (".pdf", ".docx", ".doc"):
            failed.append({"filename": file.filename, "reason": f"Unsupported file type: {ext}"})
            continue

        try:
            save_path = os.path.join(settings.UPLOAD_DIR, f"{uuid.uuid4().hex}_{file.filename}")
            with open(save_path, "wb") as f:
                f.write(await file.read())

            # Job requirement docs are text-extracted the same way as resumes
            raw_text = extract_resume_text(save_path)
            if not raw_text:
                failed.append({"filename": file.filename, "reason": "Could not extract any text."})
                continue

            details = extract_company_details(raw_text)
            company = add_company(details, source_filename=file.filename)
            added.append(company)

        except Exception as exc:
            failed.append({"filename": file.filename, "reason": str(exc)})

    return {
        "message": f"Processed {len(files)} file(s): {len(added)} added, {len(failed)} failed.",
        "added_companies": added,
        "failed": failed,
    }


@router.delete("/candidates", tags=["Candidates"])
def reset_candidates():
    """Clear all uploaded candidates (useful for demos/testing)."""
    clear_candidates()
    return {"message": "Candidate pool cleared."}


@router.delete("/companies", tags=["Companies"])
def reset_companies():
    """Clear all uploaded companies (useful for demos/testing)."""
    clear_companies()
    return {"message": "Company pool cleared."}
