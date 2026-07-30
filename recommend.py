"""
GET /recommend/{company_id}
GET /recommend-all
POST /recommend-from-prompt

All three now score against candidates sourced from uploaded resumes
(data/candidate_store.py) instead of a hardcoded list.
"""
from fastapi import APIRouter, HTTPException, Query

from data.companies import get_companies, get_company
from models.schemas import PromptRequest, CompanyRecommendations
from services.recommender import recommend_for_company
from services.prompt_extractor import extract_requirements_from_prompt, requirements_to_company

router = APIRouter(tags=["Recommendations"])


@router.get("/recommend/{company_id}", response_model=CompanyRecommendations)
def recommend_for_company_route(company_id: str, top_n: int = Query(default=3, ge=1)):
    company = get_company(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found.")

    recommendations = recommend_for_company(company, top_n=top_n)
    return CompanyRecommendations(company=company, recommendations=recommendations)


@router.get("/recommend-all", response_model=list[CompanyRecommendations])
def recommend_all_route(top_n: int = Query(default=3, ge=1)):
    results = []
    for company in get_companies():
        recommendations = recommend_for_company(company, top_n=top_n)
        results.append(CompanyRecommendations(company=company, recommendations=recommendations))
    return results


@router.post("/recommend-from-prompt")
def recommend_from_prompt_route(request: PromptRequest):
    requirements = extract_requirements_from_prompt(request.prompt)
    synthetic_company = requirements_to_company(requirements)
    recommendations = recommend_for_company(synthetic_company, top_n=request.top_n)

    return {
        "extracted_requirements": requirements,
        "recommendations": recommendations,
    }
