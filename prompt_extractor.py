"""
Turns a free-text hiring prompt (e.g. "Find me a Java developer with 3+
years experience") into a synthetic Company-shaped requirement, so it can
be scored the same way as a real company posting.
"""
import json

from models.schemas import Company
from services.llm import call_llm

SYSTEM_PROMPT = (
    "You extract hiring requirements from a free-text prompt. Output ONLY "
    "valid JSON, no markdown fences, no commentary."
)

TEMPLATE = """\
Extract hiring requirements from the prompt below. Return ONLY a JSON object
with exactly these keys:

- role (string, "Open Role" if not specified)
- skills (array of strings, required skills mentioned)
- experience (number, minimum years of experience required, 0 if not specified)
- communication (string, one of "Excellent" | "Good" | "Average" | "Poor", "Average" if not specified)

Prompt:
\"\"\"
{prompt}
\"\"\"
"""


def _safe_json_parse(raw: str) -> dict:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.replace("json\n", "", 1).replace("json\r\n", "", 1)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1:
            return json.loads(cleaned[start:end + 1])
        raise


def extract_requirements_from_prompt(prompt: str) -> dict:
    try:
        raw_response = call_llm(TEMPLATE.format(prompt=prompt), system_prompt=SYSTEM_PROMPT)
        data = _safe_json_parse(raw_response)
    except Exception:
        data = {"role": "Open Role", "skills": [], "experience": 0, "communication": "Average"}

    defaults = {"role": "Open Role", "skills": [], "experience": 0, "communication": "Average"}
    defaults.update(data)
    defaults["raw_prompt"] = prompt
    return defaults


def requirements_to_company(requirements: dict) -> Company:
    """Wrap extracted requirements in a synthetic Company so scoring can reuse recommender logic."""
    return Company(
        id="PROMPT_REQUEST",
        name="Prompt-Derived Requirement",
        role=requirements.get("role", "Open Role"),
        required_skills=requirements.get("skills", []),
        min_experience=requirements.get("experience", 0),
        min_communication=requirements.get("communication", "Average"),
        description=requirements.get("raw_prompt", ""),
    )
