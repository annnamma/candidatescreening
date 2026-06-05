"""
routes/interview.py
All API endpoints for the candidate screening platform.
"""

import json
import logging
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.database.models import Candidate, InterviewSession, Question, Summary
from app.schemas.schemas import (
    ResumeUploadResponse,
    StartInterviewRequest,
    StartInterviewResponse,
    QuestionResponse,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
    SummaryResponse,
    HealthResponse,
)
from app.services.resume_service import parse_resume
from app.services.rag_service import vectorstore_status
from app.services.interview_service import (
    create_interview_session,
    get_current_question,
    save_answer_and_check_adaptive,
)
from app.services.summary_service import generate_summary, generate_pdf_report

logger = logging.getLogger(__name__)
router = APIRouter()

SUPPORTED_ROLES = ["AI/ML Engineer", "Backend Engineer", "Data Scientist"]


# ──────────────────────────────────────────────────────────────────────────────
# Health Check
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/health", response_model=HealthResponse, tags=["System"])
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(__import__("sqlalchemy").text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "error"

    vs_status = vectorstore_status()

    return HealthResponse(
        status="ok",
        database=db_status,
        vectorstore=vs_status,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Resume Upload
# ──────────────────────────────────────────────────────────────────────────────

@router.post("/upload-resume", response_model=ResumeUploadResponse, tags=["Resume"])
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload a PDF resume. Returns candidate_id and extracted skills.
    """
    # Validate file type
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    # Read bytes
    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    if len(file_bytes) > 10 * 1024 * 1024:  # 10 MB limit
        raise HTTPException(status_code=400, detail="File size exceeds 10 MB limit.")

    # Parse resume
    try:
        parsed = parse_resume(file_bytes)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Resume parsing error: {e}")
        raise HTTPException(status_code=500, detail="Failed to process the resume PDF.")

    if not parsed["text"].strip():
        raise HTTPException(status_code=422, detail="Resume text is empty after extraction.")

    # Persist candidate
    candidate = Candidate(
        name=parsed["name"],
        resume_text=parsed["text"],
        skills=parsed["skills_json"],
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)

    logger.info(f"Candidate {candidate.id} created with {len(parsed['skills'])} skills.")

    return ResumeUploadResponse(
        candidate_id=candidate.id,
        skills=parsed["skills"],
        name=parsed["name"],
    )


# ──────────────────────────────────────────────────────────────────────────────
# Start Interview
# ──────────────────────────────────────────────────────────────────────────────

@router.post("/start-interview", response_model=StartInterviewResponse, tags=["Interview"])
def start_interview(
    body: StartInterviewRequest,
    db: Session = Depends(get_db),
):
    """
    Start a new interview session for a candidate with the selected role.
    Generates and stores 5 personalised questions.
    """
    if body.role not in SUPPORTED_ROLES:
        raise HTTPException(
            status_code=400,
            detail=f"Role must be one of: {', '.join(SUPPORTED_ROLES)}",
        )

    candidate = db.query(Candidate).filter(Candidate.id == body.candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail=f"Candidate {body.candidate_id} not found.")

    try:
        session = create_interview_session(db, body.candidate_id, body.role)
    except Exception as e:
        logger.error(f"Session creation error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start interview: {str(e)}")

    total = db.query(Question).filter(Question.session_id == session.id).count()

    return StartInterviewResponse(
        session_id=session.id,
        role=session.role,
        total_questions=total,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Get Current Question
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/question/{session_id}", response_model=QuestionResponse, tags=["Interview"])
def get_question(
    session_id: int,
    db: Session = Depends(get_db),
):
    """
    Retrieve the next unanswered question for a session.
    """
    session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found.")

    question = get_current_question(db, session_id)
    if not question:
        raise HTTPException(
            status_code=404,
            detail="No more questions. Proceed to /summary/{session_id}.",
        )

    total = db.query(Question).filter(Question.session_id == session_id).count()
    answered = total - db.query(Question).filter(
        Question.session_id == session_id,
        Question.answer == None,  # noqa: E711
    ).count()

    return QuestionResponse(
        question_id=question.id,
        question_text=question.question_text,
        question_number=answered + 1,
        total_questions=total,
        is_last=(answered + 1 == total),
    )


# ──────────────────────────────────────────────────────────────────────────────
# Submit Answer
# ──────────────────────────────────────────────────────────────────────────────

@router.post("/answer", response_model=SubmitAnswerResponse, tags=["Interview"])
def submit_answer(
    body: SubmitAnswerRequest,
    db: Session = Depends(get_db),
):
    """
    Submit a candidate's answer to the current question.
    May inject an adaptive follow-up question.
    """
    if not body.answer_text.strip():
        raise HTTPException(status_code=400, detail="Answer text cannot be empty.")

    session = db.query(InterviewSession).filter(InterviewSession.id == body.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {body.session_id} not found.")

    question = db.query(Question).filter(Question.id == body.question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail=f"Question {body.question_id} not found.")

    if question.answer:
        raise HTTPException(status_code=409, detail="This question has already been answered.")

    try:
        answer, next_available = save_answer_and_check_adaptive(
            db, body.session_id, body.question_id, body.answer_text
        )
    except Exception as e:
        logger.error(f"Answer submission error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    return SubmitAnswerResponse(
        answer_id=answer.id,
        next_question_available=next_available,
        message=(
            "Answer saved. Fetch the next question."
            if next_available
            else "Interview complete. Retrieve your summary."
        ),
    )


# ──────────────────────────────────────────────────────────────────────────────
# Get Summary
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/summary/{session_id}", response_model=SummaryResponse, tags=["Summary"])
def get_summary(
    session_id: int,
    db: Session = Depends(get_db),
):
    """
    Generate (or retrieve cached) evaluation summary for a completed session.
    """
    session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found.")

    try:
        summary = generate_summary(db, session_id)
    except Exception as e:
        logger.error(f"Summary generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate summary: {str(e)}")

    candidate = db.query(Candidate).filter(Candidate.id == session.candidate_id).first()

    return SummaryResponse(
        session_id=session_id,
        role=session.role,
        candidate_name=candidate.name if candidate else None,
        strengths=json.loads(summary.strengths or "[]"),
        weaknesses=json.loads(summary.weaknesses or "[]"),
        recommendations=json.loads(summary.recommendations or "[]"),
        overall_assessment=summary.overall_assessment or "",
        score=summary.score,
        created_at=summary.created_at,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Download PDF Report
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/summary/{session_id}/download", tags=["Summary"])
def download_summary_pdf(
    session_id: int,
    db: Session = Depends(get_db),
):
    """
    Download a PDF evaluation report for a session.
    """
    session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found.")

    try:
        pdf_bytes = generate_pdf_report(db, session_id)
    except Exception as e:
        logger.error(f"PDF generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {str(e)}")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=interview_report_{session_id}.pdf"
        },
    )


# ──────────────────────────────────────────────────────────────────────────────
# Session History
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/sessions/{candidate_id}", tags=["Analytics"])
def get_candidate_sessions(
    candidate_id: int,
    db: Session = Depends(get_db),
):
    """Return all interview sessions for a candidate (history)."""
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found.")

    sessions = (
        db.query(InterviewSession)
        .filter(InterviewSession.candidate_id == candidate_id)
        .all()
    )

    result = []
    for s in sessions:
        result.append({
            "session_id": s.id,
            "role": s.role,
            "status": s.status,
            "score": s.summary.score if s.summary else None,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        })

    return {"candidate_id": candidate_id, "sessions": result}