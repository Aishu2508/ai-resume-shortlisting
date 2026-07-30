"""
Orchestrates scoring across all candidates for a given company, and returns
the top-N ranked recommendations.
"""
from data.candidate_store import get_candidates
from models.schemas import (
    Company, Candidate, Recommendation, EligibilityReasons, Scores,
)
from services.embedding import semantic_similarity
from services.scoring import (
    compute_skill_match, compute_interview_score, compute_final_score,
    check_eligibility, build_explanation,
)


def _candidate_profile_text(candidate: Candidate) -> str:
    return f"{candidate.resume_summary} Skills: {', '.join(candidate.skills)}"


def _company_profile_text(company: Company) -> str:
    return f"{company.description} Required skills: {', '.join(company.required_skills)}"


def score_candidate_for_company(candidate: Candidate, company: Company) -> Recommendation:
    skill_match, matched_skills, missing_skills = compute_skill_match(candidate, company)
    sim = semantic_similarity(_candidate_profile_text(candidate), _company_profile_text(company))
    interview_score = compute_interview_score(candidate.interview_feedback)
    final_score = compute_final_score(skill_match, sim, interview_score)
    eligible, min_exp_met, min_comm_met = check_eligibility(candidate, company)
    explanation = build_explanation(candidate, company, matched_skills, missing_skills, min_exp_met, interview_score)

    return Recommendation(
        candidate_id=candidate.id,
        name=candidate.name,
        skills=candidate.skills,
        experience_years=candidate.experience_years,
        eligible=eligible,
        eligibility_reasons=EligibilityReasons(
            min_experience_met=min_exp_met,
            min_communication_met=min_comm_met,
        ),
        scores=Scores(
            skill_match=skill_match,
            semantic_similarity=sim,
            interview_score=interview_score,
            final_score=final_score,
        ),
        interview_feedback=candidate.interview_feedback,
        explanation=explanation,
    )


def recommend_for_company(company: Company, top_n: int = 3) -> list[Recommendation]:
    candidates = get_candidates()
    scored = [score_candidate_for_company(c, company) for c in candidates]
    scored.sort(key=lambda r: r.scores.final_score, reverse=True)
    return scored[:top_n]
