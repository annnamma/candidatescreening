from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# ──────────────────────────────────────────
# Resume / Candidate
# ──────────────────────────────────────────

class ResumeUploadResponse(BaseModel):
    candidate_id: int
    skills: List[str]
    name: Optional[str] = None
    message: str = "Resume uploaded and parsed successfully."


# ──────────────────────────────────────────
# Interview Session
# ──────────────────────────────────────────

class StartInterviewRequest(BaseModel):
    candidate_id: int
    role: str = Field(..., description="AI/ML Engineer | Backend Engineer | Data Scientist")


class StartInterviewResponse(BaseModel):
    session_id: int
    role: str
    total_questions: int
    message: str = "Interview started. Retrieve your first question."


# ──────────────────────────────────────────
# Question
# ──────────────────────────────────────────

class QuestionResponse(BaseModel):
    question_id: int
    question_text: str
    question_number: int
    total_questions: int
    is_last: bool


# ──────────────────────────────────────────
# Answer
# ──────────────────────────────────────────

class SubmitAnswerRequest(BaseModel):
    session_id: int
    question_id: int
    answer_text: str


class SubmitAnswerResponse(BaseModel):
    answer_id: int
    next_question_available: bool
    message: str


# ──────────────────────────────────────────
# Summary
# ──────────────────────────────────────────

class SummaryResponse(BaseModel):
    session_id: int
    role: str
    candidate_name: Optional[str]
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]
    overall_assessment: str
    score: Optional[int]
    created_at: Optional[datetime]


# ──────────────────────────────────────────
# Health
# ──────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    database: str
    vectorstore: str
    version: str = "1.0.0"