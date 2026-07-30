# ShortlistAI — API Example Requests & Responses

This file captures real example requests/responses from the running API (via Swagger UI at `/docs`), organized by resource. Use it alongside the main [README.md](../README.md) as a quick reference for expected payload shapes.

---

## Uploads

### `POST /upload-resumes`

```bash
curl -X 'POST' \
  'http://127.0.0.1:8000/upload-resumes' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'files=@Alice_Johnson_Resume.docx' \
  -F 'files=@David_Wilson_Resume.docx' \
  -F 'files=@Grace_Hall_Resume.docx'
```

```json
{
  "message": "Processed 3 file(s): 3 added, 0 failed.",
  "added_candidates": [
    {
      "id": "C009",
      "name": "Alice Johnson",
      "skills": ["Python", "FastAPI", "REST APIs", "SQL", "Docker", "Git"],
      "experience_years": 3,
      "projects": [],
      "resume_summary": "Alice Johnson Role: Python Developer Experience: 3 Years Skills Python FastAPI REST APIs SQL Docker Git",
      "source_filename": "Alice_Johnson_Resume.docx",
      "interview_feedback": null
    }
  ],
  "failed": []
}
```

### `POST /upload-companies`

```bash
curl -X 'POST' \
  'http://127.0.0.1:8000/upload-companies' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'files=@AI_ML_Engineer_JD.docx' \
  -F 'files=@Data_Scientist_JD.docx' \
  -F 'files=@Full_Stack_Developer_JD.docx'
```

```json
{
  "message": "Processed 3 file(s): 3 added, 0 failed.",
  "added_companies": [
    {
      "id": "CO_G",
      "name": "Unknown Company",
      "role": "Alice Johnson",
      "required_skills": ["Python", "FastAPI", "REST APIs", "SQL", "Docker", "Git"],
      "min_experience": 3,
      "min_communication": "Average",
      "description": "Alice Johnson Role: Python Developer Experience: 3 Years Skills Python FastAPI REST APIs SQL Docker Git"
    }
  ],
  "failed": []
}
```

### `DELETE /candidates` / `DELETE /companies`
Clears all uploaded candidates or companies (demo/testing reset).

---

## Candidates

### `GET /candidates`
Returns the full candidate list. Example item:
```json
{
  "id": "C010",
  "name": "David Wilson",
  "skills": ["Python", "SQL", "Machine Learning", "Pandas", "NumPy", "Power BI"],
  "experience_years": 3,
  "projects": [],
  "resume_summary": "David Wilson Role: Data Scientist Experience: 3 Years Skills Python Pandas NumPy SQL Machine Learning Power BI",
  "source_filename": "David_Wilson_Resume.docx",
  "interview_feedback": null
}
```

### `GET /candidates/{candidate_id}`
```bash
curl 'http://127.0.0.1:8000/candidates/C010'
```
Returns a single candidate record (same shape as above).

### `POST /candidates/{candidate_id}/interview-feedback`
```bash
curl -X 'POST' \
  'http://127.0.0.1:8000/candidates/C010/interview-feedback' \
  -H 'Content-Type: application/json' \
  -d '{
    "communication": "Good",
    "problem_solving": "Good",
    "coding": "Excellent",
    "leadership": "Average",
    "overall_rating": 8
  }'
```
Returns the candidate record with `interview_feedback` populated.

---

## Companies

### `GET /companies`
Returns the full company/role list (same shape as `POST /upload-companies` items).

### `GET /companies/{company_id}`
```bash
curl 'http://127.0.0.1:8000/companies/CO_B'
```

### `DELETE /companies`
Clears all companies.

---

## Recommendations

### `GET /recommend/{company_id}?top_n=3`

```bash
curl 'http://127.0.0.1:8000/recommend/CO_B?top_n=3'
```

```json
{
  "company": { "id": "CO_B", "role": "Data Scientist Job Description", "...": "..." },
  "recommendations": [
    {
      "candidate_id": "C010",
      "name": "David Wilson",
      "eligible": true,
      "eligibility_reasons": { "min_experience_met": true, "min_communication_met": true },
      "scores": {
        "skill_match": 1,
        "semantic_similarity": 0.829,
        "interview_score": 0.76,
        "final_score": 0.8938
      },
      "explanation": "David Wilson matches 6/6 required skills (Python, SQL, Machine Learning, Pandas, NumPy, Power BI); meets the 3.0+ year experience requirement (3.0 yrs); rated Excellent in coding during interview (overall 8/10)."
    }
  ]
}
```

### `GET /recommend-all?top_n=3`
Same shape as above, but returns an array — one entry per company on file, each with its own ranked `recommendations`.

### `POST /recommend-from-prompt`

```bash
curl -X 'POST' \
  'http://127.0.0.1:8000/recommend-from-prompt' \
  -H 'Content-Type: application/json' \
  -d '{
    "prompt": "Looking for a Python Developer with 3+ years of experience in Python, FastAPI, REST APIs, SQL, Docker, and Git. Strong communication and problem-solving skills are required.",
    "top_n": 3
  }'
```

Returns `extracted_requirements` (parsed role/skills/experience/communication from the prompt) plus a ranked `recommendations` list, same shape as the other recommend endpoints.

> **Note:** In the sample response, `extracted_requirements.skills` came back empty and `skill_match` was `0` for every candidate — the prompt parser didn't pick up the skills mentioned in free text. Worth checking the extraction logic in `main.py` if this endpoint needs to weigh explicit skill mentions.

---

## Shortlist

### `POST /shortlist`
```bash
curl -X 'POST' \
  'http://127.0.0.1:8000/shortlist' \
  -H 'Content-Type: application/json' \
  -d '{
    "candidate_id": "C010",
    "company_id": "CO_B",
    "notes": "Selected for Technical Interview"
  }'
```
```json
{
  "id": "SL0002",
  "candidate_id": "C010",
  "company_id": "CO_B",
  "status": "Shortlisted",
  "notes": "Selected for Technical Interview",
  "created_date": "2026-07-30T13:18:16.836072",
  "last_updated": "2026-07-30T13:18:16.836072"
}
```

### `GET /shortlist`
Supports optional `status`, `company_id`, `candidate_id` query filters. Returns entries newest-first.

### `GET /shortlist/{entry_id}`
```bash
curl 'http://127.0.0.1:8000/shortlist/SL0002'
```

### `PATCH /shortlist/{entry_id}/status`
```bash
curl -X 'PATCH' \
  'http://127.0.0.1:8000/shortlist/SL0002/status' \
  -H 'Content-Type: application/json' \
  -d '{
    "status": "Shortlisted",
    "notes": "Candidate cleared resume screening and moved to the technical interview round."
  }'
```

### `DELETE /shortlist`
Clears all shortlist entries.

---

## Schemas Reference

The OpenAPI schema (`/openapi.json`) defines these models:

- `Company`, `CompanyRecommendations`
- `Recommendation`, `Scores`, `EligibilityReasons`
- `InterviewFeedback`, `InterviewFeedbackUpdate`
- `PromptRequest`
- `ShortlistCreate`, `ShortlistStatusUpdate`, `ApplicationStatus`
- `HTTPValidationError`, `ValidationError` (standard FastAPI 422 error shape)

See `models/schemas.py` in the source for full field definitions.
