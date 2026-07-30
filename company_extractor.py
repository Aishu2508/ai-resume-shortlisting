"""
Uses the LLM to extract structured company/job-posting details from a raw
job-requirement document (PDF/DOCX) — the company-side equivalent of
resume_extractor.py.
"""
import json
import re

from services.llm import call_llm

SYSTEM_PROMPT = (
    "You are an expert HR data-extraction assistant. You read raw job "
    "requirement documents and output ONLY valid JSON, with no markdown "
    "fences, no preamble, and no commentary."
)

EXTRACTION_TEMPLATE = """\
Extract the following fields from the job requirement text below.
Return ONLY a JSON object with exactly these keys:

- company_name (string, "Unknown Company" if not mentioned)
- role (string, the job title being hired for)
- required_skills (array of strings, the key technical/professional skills required)
- min_experience (number, minimum years of experience required, 0 if not specified)
- min_communication (string, one of "Excellent" | "Good" | "Average" | "Poor" —
  infer from tone/requirements if not explicit, default "Average")
- description (string, a concise 2-3 sentence summary of the role and requirements)

Job Requirement Text:
\"\"\"
{text}
\"\"\"
"""

# Same keyword list style as resume_extractor.py's fallback, used only when
# no LLM key is configured.
_KNOWN_SKILLS = [
    "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "Go", "Rust",
    "FastAPI", "Django", "Flask", "Spring Boot", "Node.js", "Express",
    "React", "Angular", "Vue", "Next.js", "GraphQL", "REST APIs",
    "MySQL", "PostgreSQL", "MongoDB", "Redis", "SQL", "NoSQL",
    "Kafka", "RabbitMQ", "Microservices", "Docker", "Kubernetes",
    "AWS", "Azure", "GCP", "Terraform", "CI/CD", "Git",
    "Machine Learning", "Deep Learning", "Gen AI", "LLMs", "RAG",
    "TensorFlow", "PyTorch", "Pandas", "NumPy", "Power BI", "Tableau",
    "Data Analyst", "DevOps", "HTML", "CSS",
]


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


def _extract_skills(text: str) -> list[str]:
    lowered = text.lower()
    return [s for s in _KNOWN_SKILLS if s.lower() in lowered]


def _extract_min_experience(text: str) -> float:
    match = re.search(r"(\d+(?:\.\d+)?)\s*\+?\s*years?", text, re.IGNORECASE)
    return float(match.group(1)) if match else 0.0


def _extract_role(text: str) -> str:
    """First non-empty line is usually the job title in these documents."""
    first_line = next((line.strip() for line in text.splitlines() if line.strip()), "Open Role")
    return first_line[:80]


def _fallback_extract(text: str) -> dict:
    """
    Heuristic fallback used only if the LLM call fails (e.g. no API key
    configured), so /upload-companies still returns usable, non-empty
    required_skills and min_experience instead of blank defaults.
    """
    return {
        "company_name": "Unknown Company",
        "role": _extract_role(text),
        "required_skills": _extract_skills(text),
        "min_experience": _extract_min_experience(text),
        "min_communication": "Average",
        "description": text[:250].replace("\n", " ").strip(),
    }


def extract_company_details(job_text: str) -> dict:
    """Call the LLM to turn raw job-requirement text into structured company fields."""
    prompt = EXTRACTION_TEMPLATE.format(text=job_text[:12000])
    try:
        raw_response = call_llm(prompt, system_prompt=SYSTEM_PROMPT)
        data = _safe_json_parse(raw_response)
    except Exception:
        data = _fallback_extract(job_text)

    defaults = {
        "company_name": "", "role": "", "required_skills": [],
        "min_experience": 0, "min_communication": "Average", "description": "",
    }
    defaults.update(data)
    return defaults
