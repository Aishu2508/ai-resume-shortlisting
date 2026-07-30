"""
Scoring logic for matching a Candidate against a Company job posting.

final_score = WEIGHT_SKILL_MATCH   * skill_match
            + WEIGHT_SEMANTIC_SIMILARITY * semantic_similarity
            + WEIGHT_INTERVIEW_SCORE * interview_score

Weights are configurable via .env (config.settings).
"""
from typing import Optional

from config import settings
from models.schemas import Candidate, Company, InterviewFeedback

_RATING_MAP = {
    "excellent": 1.0,
    "good": 0.75,
    "average": 0.5,
    "below average": 0.25,
    "poor": 0.25,
}

# Neutral interview score used when a candidate has no interview feedback
# yet (e.g. freshly uploaded resume, not yet interviewed).
_NO_FEEDBACK_INTERVIEW_SCORE = 0.5


def _normalize_skill(skill: str) -> str:
    return skill.strip().lower()


def compute_skill_match(candidate: Candidate, company: Company) -> tuple[float, list[str], list[str]]:
    """Return (skill_match_ratio, matched_skills, missing_skills)."""
    if not company.required_skills:
        return 0.0, [], []

    candidate_skills_normalized = {_normalize_skill(s) for s in candidate.skills}

    matched, missing = [], []
    for skill in company.required_skills:
        if _normalize_skill(skill) in candidate_skills_normalized:
            matched.append(skill)
        else:
            missing.append(skill)

    ratio = round(len(matched) / len(company.required_skills), 3)
    return ratio, matched, missing


def compute_interview_score(feedback: Optional[InterviewFeedback]) -> float:
    """Average of the 4 qualitative categories + overall_rating/10, all on a 0-1 scale."""
    if feedback is None:
        return _NO_FEEDBACK_INTERVIEW_SCORE

    values = []
    for field in ("communication", "problem_solving", "coding", "leadership"):
        rating = getattr(feedback, field, None)
        if rating:
            values.append(_RATING_MAP.get(rating.strip().lower(), 0.5))

    if feedback.overall_rating is not None:
        values.append(feedback.overall_rating / 10)

    if not values:
        return _NO_FEEDBACK_INTERVIEW_SCORE

    return round(sum(values) / len(values), 3)


def compute_final_score(skill_match: float, semantic_similarity: float, interview_score: float) -> float:
    score = (
        settings.WEIGHT_SKILL_MATCH * skill_match
        + settings.WEIGHT_SEMANTIC_SIMILARITY * semantic_similarity
        + settings.WEIGHT_INTERVIEW_SCORE * interview_score
    )
    return round(score, 4)


def check_eligibility(candidate: Candidate, company: Company) -> tuple[bool, bool, bool]:
    """Return (eligible, min_experience_met, min_communication_met)."""
    min_experience_met = candidate.experience_years >= company.min_experience

    comm_rank = {"poor": 0, "below average": 0, "average": 1, "good": 2, "excellent": 3}
    required_rank = comm_rank.get(company.min_communication.strip().lower(), 1)

    if candidate.interview_feedback and candidate.interview_feedback.communication:
        candidate_rank = comm_rank.get(candidate.interview_feedback.communication.strip().lower(), 1)
    else:
        # No interview feedback yet: don't penalize, treat as meeting the bar.
        candidate_rank = required_rank

    min_communication_met = candidate_rank >= required_rank
    return (min_experience_met and min_communication_met), min_experience_met, min_communication_met


def build_explanation(
    candidate: Candidate,
    company: Company,
    matched_skills: list[str],
    missing_skills: list[str],
    min_experience_met: bool,
    interview_score: float,
) -> str:
    parts = []

    if matched_skills:
        parts.append(
            f"{candidate.name} matches {len(matched_skills)}/{len(company.required_skills)} "
            f"required skills ({', '.join(matched_skills)})"
        )
    else:
        parts.append(f"{candidate.name} did not match any required skills")

    if min_experience_met:
        parts.append(f"meets the {company.min_experience}+ year experience requirement ({candidate.experience_years} yrs)")
    else:
        parts.append(f"does not meet the {company.min_experience}+ year experience requirement ({candidate.experience_years} yrs)")

    if candidate.interview_feedback:
        strong_categories = [
            field.replace("_", " ")
            for field in ("communication", "problem_solving", "coding", "leadership")
            if getattr(candidate.interview_feedback, field, "") and
            getattr(candidate.interview_feedback, field).strip().lower() == "excellent"
        ]
        if strong_categories:
            rating = candidate.interview_feedback.overall_rating
            parts.append(
                f"rated Excellent in {', '.join(strong_categories)} during interview "
                f"(overall {rating}/10)" if rating is not None else
                f"rated Excellent in {', '.join(strong_categories)} during interview"
            )
    else:
        parts.append("no interview feedback recorded yet")

    if missing_skills:
        parts.append(f"gap in: {', '.join(missing_skills)}")

    return "; ".join(parts) + "."
