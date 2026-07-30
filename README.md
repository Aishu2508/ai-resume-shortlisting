# ShortlistAI

**ShortlistAI** is an AI-assisted recruitment API that ingests candidate resumes and job descriptions, then produces a ranked, explainable shortlist of the best-fit candidates for each role. It also tracks the hiring pipeline — Shortlisted vs. Rejected — per candidate/company pair.

Built with **FastAPI** (see `server: uvicorn` in responses) and **SQLAlchemy** for persistence.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [API Reference](#api-reference)
  - [Uploads](#uploads)
  - [Candidates](#candidates)
  - [Companies](#companies)
  - [Recommendations](#recommendations)
  - [Shortlist](#shortlist)
- [Scoring Model](#scoring-model)
- [Data Models](#data-models)
- [License](#license)

---

## Features

- 📄 **Resume & JD ingestion** — upload PDF/DOCX resumes and job descriptions in bulk via multipart requests; skills, experience, and role are auto-extracted.
- 🧠 **AI-ranked recommendations** — candidates are scored against a job's required skills, experience, and semantic similarity of resume-to-JD text.
- 🗣️ **Free-text job requests** — describe a role in plain English (`/recommend-from-prompt`) and get a ranked shortlist without creating a formal company record first.
- 🎤 **Interview feedback loop** — attach structured interview scorecards to a candidate; feedback is folded into the final ranking score.
- ✅ **Shortlist tracking** — persist Shortlisted/Rejected decisions per candidate-company pair, with notes and timestamps, independent of the scoring engine.
- 🧹 **Demo-friendly resets** — `DELETE` endpoints to clear candidates, companies, or the shortlist for repeatable demos/testing.

---

## Tech Stack

| Layer          | Technology                          |
|----------------|--------------------------------------|
| API framework  | FastAPI + Uvicorn                    |
| Data validation| Pydantic (`models/schemas.py`)       |
| Persistence    | SQLAlchemy ORM (`database/db.py`, `database/models.py`) |
| Document parsing | PDF/DOCX resume & JD extraction    |

---

## Project Structure

```
.
├── data/
│   ├── candidate_store.py      # persistence layer for candidates
│   └── companies.py            # persistence layer for companies
├── database/
│   ├── db.py                   # SessionLocal / engine setup
│   └── models.py               # SQLAlchemy ORM models (incl. ShortlistModel)
├── models/
│   └── schemas.py              # Pydantic schemas (ShortlistEntry, ShortlistCreate, etc.)
├── shortlist_AI.py             # Persistent shortlist store (CRUD for Shortlisted/Rejected entries)
└── main.py                     # FastAPI app & route definitions (not included here)
```

> `shortlist_AI.py` follows the same pattern as `data/candidate_store.py` and `data/companies.py`, so it can be dropped into an existing project with those modules already present.

---

## Getting Started

```bash
# 1. Clone the repo
git clone https://github.com/<your-username>/shortlist-ai.git
cd shortlist-ai

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the API
uvicorn main:app --reload
```

The interactive API docs (Swagger UI) will be available at:

```
http://127.0.0.1:8000/docs
```

and the raw OpenAPI schema at:

```
http://127.0.0.1:8000/openapi.json
```

---

## API Reference

Base URL: `http://127.0.0.1:8000`

### Uploads

| Method | Endpoint            | Description                                              |
|--------|----------------------|------------------------------------------------------------|
| POST   | `/upload-resumes`    | Upload one or more candidate resumes (PDF/DOCX)            |
| POST   | `/upload-companies`  | Upload one or more job-requirement documents (PDF/DOCX)    |

**Example — `POST /upload-resumes`**
```bash
curl -X POST 'http://127.0.0.1:8000/upload-resumes' \
  -H 'accept: application/json' \
  -F 'files=@Alice_Johnson_Resume.docx' \
  -F 'files=@David_Wilson_Resume.docx'
```
Response includes auto-extracted `skills`, `experience_years`, and a generated `resume_summary` per candidate, plus a `failed` list for any files that couldn't be parsed.

### Candidates

| Method | Endpoint                                       | Description                       |
|--------|-------------------------------------------------|------------------------------------|
| GET    | `/candidates`                                   | List all candidates                |
| GET    | `/candidates/{candidate_id}`                    | Get a single candidate's detail    |
| POST   | `/candidates/{candidate_id}/interview-feedback` | Attach/update interview feedback   |
| DELETE | `/candidates`                                   | Reset (clear) all candidates       |

**Interview feedback payload:**
```json
{
  "communication": "Good",
  "problem_solving": "Good",
  "coding": "Excellent",
  "leadership": "Average",
  "overall_rating": 8
}
```

### Companies

| Method | Endpoint                    | Description                          |
|--------|-------------------------------|----------------------------------------|
| GET    | `/companies`                 | List all companies/roles              |
| GET    | `/companies/{company_id}`    | Get a single company/role's detail    |
| DELETE | `/companies`                 | Reset (clear) all companies           |

### Recommendations

| Method | Endpoint                        | Description                                                        |
|--------|-----------------------------------|----------------------------------------------------------------------|
| GET    | `/recommend/{company_id}?top_n=N` | Ranked candidate recommendations for one company/role                |
| GET    | `/recommend-all?top_n=N`          | Ranked recommendations for every company on file                     |
| POST   | `/recommend-from-prompt`          | Describe a role in free text and get ranked recommendations back     |

**Example — `POST /recommend-from-prompt`**
```json
{
  "prompt": "Looking for a Python Developer with 3+ years of experience in Python, FastAPI, REST APIs, SQL, Docker, and Git. Strong communication and problem-solving skills are required.",
  "top_n": 3
}
```

Each recommendation includes:
- `eligible` flag + `eligibility_reasons` (min experience / min communication met)
- `scores` breakdown (`skill_match`, `semantic_similarity`, `interview_score`, `final_score`)
- a human-readable `explanation` of the match (skills matched, experience, interview rating, and gaps)

### Shortlist

Persisted separately from the scoring engine — represents actual hiring decisions.

| Method | Endpoint                        | Description                                   |
|--------|-----------------------------------|-------------------------------------------------|
| POST   | `/shortlist`                     | Create a shortlist entry (defaults to `Shortlisted`) |
| GET    | `/shortlist`                     | List entries, filterable by `status`, `company_id`, `candidate_id` |
| GET    | `/shortlist/{entry_id}`          | Get a single shortlist entry                   |
| PATCH  | `/shortlist/{entry_id}/status`   | Update status (`Shortlisted` / `Rejected`) and/or notes |
| DELETE | `/shortlist`                     | Reset (clear) the shortlist                     |

**Create entry:**
```json
{
  "candidate_id": "C010",
  "company_id": "CO_B",
  "notes": "Selected for Technical Interview"
}
```

**Update status:**
```json
{
  "status": "Shortlisted",
  "notes": "Candidate cleared resume screening and moved to the technical interview round."
}
```

Entry IDs are auto-generated sequentially as `SL0001`, `SL0002`, ... (see `_next_id` in `shortlist_AI.py`).

---

## Scoring Model

The final recommendation score is a weighted blend of:

| Component            | What it measures                                              |
|-----------------------|-----------------------------------------------------------------|
| `skill_match`         | Fraction of required skills present on the candidate's resume  |
| `semantic_similarity` | Embedding/text similarity between resume and job description   |
| `interview_score`     | Normalized score derived from recorded interview feedback (defaults to a neutral value if no feedback exists yet) |

`final_score` is used to rank candidates within `/recommend/{company_id}`, `/recommend-all`, and `/recommend-from-prompt`. Candidates who don't meet `min_experience` or `min_communication` are flagged via `eligible: false` but may still be returned for visibility.

---

## Data Models

Key Pydantic/ORM entities (see `models/schemas.py` and `database/models.py`):

- **Candidate** — `id`, `name`, `skills[]`, `experience_years`, `projects[]`, `resume_summary`, `source_filename`, `interview_feedback`
- **Company** — `id`, `name`, `role`, `required_skills[]`, `min_experience`, `min_communication`, `description`
- **InterviewFeedback** — `communication`, `problem_solving`, `coding`, `leadership`, `overall_rating`
- **ShortlistEntry** (`shortlist_AI.py`) — `id`, `candidate_id`, `company_id`, `status` (`Shortlisted` / `Rejected`), `notes`, `created_date`, `last_updated`

---


