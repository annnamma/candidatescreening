"""
summary_service.py
Generates a structured evaluation report for a completed interview session.
Also supports PDF report export.
"""

import json
import logging
import os
import re
from typing import Dict, List, Optional
from datetime import datetime

import google.generativeai as genai
from sqlalchemy.orm import Session

from app.database.models import InterviewSession, Candidate, Summary
from app.services.interview_service import get_session_transcript
from app.prompts.templates import SUMMARY_GENERATION_PROMPT

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# LLM helper
# ──────────────────────────────────────────────────────────────────────────────

def _call_gemini(prompt: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError("GEMINI_API_KEY is not set.")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    return response.text.strip()


def _parse_json(raw: str) -> dict:
    clean = re.sub(r"```(?:json)?", "", raw).replace("```", "").strip()
    return json.loads(clean)


# ──────────────────────────────────────────────────────────────────────────────
# Summary Generation
# ──────────────────────────────────────────────────────────────────────────────

def generate_summary(db: Session, session_id: int) -> Summary:
    """
    Generate an evaluation summary for the completed interview session
    and persist it to the database.
    """
    # Load session + candidate
    session: Optional[InterviewSession] = (
        db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
    )
    if not session:
        raise ValueError(f"Session {session_id} not found.")

    # Return cached summary if already generated
    if session.summary:
        return session.summary

    candidate: Optional[Candidate] = (
        db.query(Candidate).filter(Candidate.id == session.candidate_id).first()
    )
    skills = json.loads(candidate.skills or "[]") if candidate else []
    skills_str = ", ".join(skills) if skills else "General"

    transcript = get_session_transcript(db, session_id)

    prompt = SUMMARY_GENERATION_PROMPT.format(
        role=session.role,
        skills=skills_str,
        transcript=transcript,
    )

    evaluation: Dict = {}
    try:
        raw = _call_gemini(prompt)
        evaluation = _parse_json(raw)
        logger.info(f"Generated evaluation for session {session_id}.")
    except Exception as e:
        logger.error(f"Evaluation generation failed: {e}. Using fallback.")
        evaluation = _fallback_evaluation(session.role)

    # Persist summary
    summary = Summary(
        session_id=session_id,
        strengths=json.dumps(evaluation.get("strengths", [])),
        weaknesses=json.dumps(evaluation.get("weaknesses", [])),
        recommendations=json.dumps(evaluation.get("recommendations", [])),
        overall_assessment=evaluation.get("overall_assessment", "Assessment not available."),
        score=int(evaluation.get("score", 50)),
    )
    db.add(summary)

    # Mark session as completed
    session.status = "completed"
    db.commit()
    db.refresh(summary)
    return summary


def _fallback_evaluation(role: str) -> Dict:
    return {
        "strengths": [
            "Participated in the interview process.",
            "Demonstrated basic familiarity with the domain.",
        ],
        "weaknesses": [
            "Could not fully evaluate technical depth due to processing limitations.",
        ],
        "recommendations": [
            "Review core concepts for the selected role.",
            "Practice explaining technical concepts clearly.",
            "Work on hands-on projects to build practical experience.",
        ],
        "overall_assessment": (
            f"The candidate attempted an interview for the role of {role}. "
            "A full automated evaluation could not be completed at this time. "
            "Manual review is recommended."
        ),
        "score": 50,
    }


# ──────────────────────────────────────────────────────────────────────────────
# PDF Report Export
# ──────────────────────────────────────────────────────────────────────────────

def generate_pdf_report(db: Session, session_id: int) -> bytes:
    """
    Generate a downloadable PDF report for a session summary.
    Returns raw PDF bytes.
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    import io

    session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
    if not session:
        raise ValueError(f"Session {session_id} not found.")

    summary = session.summary
    if not summary:
        summary = generate_summary(db, session_id)

    candidate = db.query(Candidate).filter(Candidate.id == session.candidate_id).first()

    strengths = json.loads(summary.strengths or "[]")
    weaknesses = json.loads(summary.weaknesses or "[]")
    recommendations = json.loads(summary.recommendations or "[]")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=20*mm, bottomMargin=20*mm)
    styles = getSampleStyleSheet()
    story = []

    # Title
    title_style = ParagraphStyle("Title", parent=styles["Title"], fontSize=22, textColor=colors.HexColor("#1e3a5f"))
    story.append(Paragraph("AI Interview Evaluation Report", title_style))
    story.append(Spacer(1, 6*mm))

    # Meta table
    meta = [
        ["Candidate", candidate.name or "N/A"],
        ["Role", session.role],
        ["Date", summary.created_at.strftime("%Y-%m-%d %H:%M") if summary.created_at else "N/A"],
        ["Score", f"{summary.score}/100" if summary.score is not None else "N/A"],
    ]
    meta_table = Table(meta, colWidths=[50*mm, 120*mm])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#1e3a5f")),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.white),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 11),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (1, 0), (-1, -1), [colors.whitesmoke, colors.white]),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 8*mm))

    h2 = ParagraphStyle("H2", parent=styles["Heading2"], textColor=colors.HexColor("#1e3a5f"))
    body = styles["BodyText"]

    # Overall Assessment
    story.append(Paragraph("Overall Assessment", h2))
    story.append(Paragraph(summary.overall_assessment or "N/A", body))
    story.append(Spacer(1, 6*mm))

    # Strengths
    story.append(Paragraph("Strengths", h2))
    for s in strengths:
        story.append(Paragraph(f"• {s}", body))
    story.append(Spacer(1, 6*mm))

    # Weaknesses
    story.append(Paragraph("Areas for Improvement", h2))
    for w in weaknesses:
        story.append(Paragraph(f"• {w}", body))
    story.append(Spacer(1, 6*mm))

    # Recommendations
    story.append(Paragraph("Recommendations", h2))
    for r in recommendations:
        story.append(Paragraph(f"• {r}", body))
    story.append(Spacer(1, 6*mm))

    # Transcript
    story.append(Paragraph("Interview Transcript", h2))
    transcript = get_session_transcript(db, session_id)
    for line in transcript.split("\n"):
        if line.strip():
            story.append(Paragraph(line, body))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()