"""
ShortlistAI
FastAPI application entry point.

Upload resumes and job descriptions, get AI-ranked shortlists.

Run with:
    uvicorn app:app --reload
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database.db import init_db
from routes import candidates, companies, recommend, upload, shortlist

app = FastAPI(
    title="ShortlistAI",
    description=(
        "Upload candidate resumes and job descriptions, then get an "
        "AI-ranked shortlist of the best-fit candidates for each role."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/", tags=["Health"])
def root():
    return {
        "message": "ShortlistAI API",
        "docs": "/docs",
        "endpoints": [
            "/upload-resumes",
            "/candidates",
            "/candidates/{candidate_id}",
            "/candidates/{candidate_id}/interview-feedback",
            "/upload-companies",
            "/companies",
            "/companies/{company_id}",
            "/recommend/{company_id}",
            "/recommend-all",
            "/recommend-from-prompt",
            "/shortlist",
            "/shortlist/{entry_id}",
            "/shortlist/{entry_id}/status",
        ],
    }


app.include_router(upload.router)
app.include_router(candidates.router)
app.include_router(companies.router)
app.include_router(recommend.router)
app.include_router(shortlist.router)
