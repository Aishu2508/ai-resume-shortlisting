"""
POST   /shortlist                     - shortlist a candidate for a company/job
GET    /shortlist                     - list shortlist entries, filterable by status/company_id/candidate_id
GET    /shortlist/{entry_id}          - get one shortlist entry
PATCH  /shortlist/{entry_id}/status   - mark Shortlisted or Rejected
DELETE /shortlist                     - clear all shortlist entries (demos/testing)
"""
from typing import Optional

from fastapi import APIRouter, HTTPException

from data.shortlist_store import (
    add_shortlist_entry,
    list_shortlist,
    get_shortlist_entry,
    update_shortlist_status,
    clear_shortlist,
)
from data.candidate_store import get_candidate
from data.companies import get_company
from models.schemas import ShortlistCreate, ShortlistStatusUpdate

router = APIRouter(tags=["Shortlist"])


@router.post("/shortlist")
def create_shortlist_entry(data: ShortlistCreate):
    if not get_candidate(data.candidate_id):
        raise HTTPException(status_code=404, detail=f"Candidate '{data.candidate_id}' not found.")
    if not get_company(data.company_id):
        raise HTTPException(status_code=404, detail=f"Company '{data.company_id}' not found.")
    return add_shortlist_entry(data)


@router.get("/shortlist")
def get_shortlist(
    status: Optional[str] = None,
    company_id: Optional[str] = None,
    candidate_id: Optional[str] = None,
):
    return list_shortlist(status=status, company_id=company_id, candidate_id=candidate_id)


@router.get("/shortlist/{entry_id}")
def get_shortlist_detail(entry_id: str):
    entry = get_shortlist_entry(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Shortlist entry not found.")
    return entry


@router.patch("/shortlist/{entry_id}/status")
def update_shortlist_entry_status(entry_id: str, data: ShortlistStatusUpdate):
    entry = update_shortlist_status(entry_id, data)
    if not entry:
        raise HTTPException(status_code=404, detail="Shortlist entry not found.")
    return entry


@router.delete("/shortlist")
def reset_shortlist():
    """Clear all shortlist entries (useful for demos/testing)."""
    clear_shortlist()
    return {"message": "Shortlist cleared."}
