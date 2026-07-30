"""
GET /candidates            - list all candidates (from uploaded resumes)
GET /candidates/{id}       - get a single candidate
POST /candidates/{id}/interview-feedback - attach interview feedback (resumes
                              don't contain interview data, so it's added
                              separately after an interview takes place)
"""
from fastapi import APIRouter, HTTPException

from data.candidate_store import get_candidates, get_candidate, update_interview_feedback
from models.schemas import InterviewFeedbackUpdate

router = APIRouter(tags=["Candidates"])


@router.get("/candidates")
def list_candidates():
    return get_candidates()


@router.get("/candidates/{candidate_id}")
def get_candidate_detail(candidate_id: str):
    candidate = get_candidate(candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found.")
    return candidate


@router.post("/candidates/{candidate_id}/interview-feedback")
def add_interview_feedback(candidate_id: str, feedback: InterviewFeedbackUpdate):
    candidate = update_interview_feedback(candidate_id, feedback)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found.")
    return candidate
