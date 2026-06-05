"""
interview_service.py
Handles question generation (initial + adaptive), session logic, and answer storage.
"""

import json
import logging
import re
from typing import List, Dict, Optional, Tuple

import google.generativeai as genai
from sqlalchemy.orm import Session

from app.database.models import Candidate, InterviewSession, Question, Answer
from app.services.rag_service import retrieve_context
from app.prompts.templates import QUESTION_GENERATION_PROMPT, ADAPTIVE_QUESTION_PROMPT
MAX_TOTAL_QUESTIONS = 8
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Adaptive trigger map
# ──────────────────────────────────────────────────────────────────────────────

ADAPTIVE_TRIGGERS: Dict[str, List[str]] = {
    "tensorflow": ["CNN", "Transfer Learning", "Model Deployment", "TensorFlow Serving"],
    "pytorch": ["Autograd", "DataLoader", "Distributed Training", "ONNX export"],
    "fastapi": ["Async Programming", "API Security", "Scalability", "Dependency Injection"],
    "docker": ["Container Orchestration", "Kubernetes", "Docker Compose", "Image Layers"],
    "kubernetes": ["Pod scheduling", "Service mesh", "Helm charts", "Auto-scaling"],
    "react": ["State management", "Component lifecycle", "React Hooks", "Performance optimisation"],
    "sql": ["Query optimisation", "Indexing strategies", "ACID properties", "Window functions"],
    "spark": ["RDD vs DataFrame", "Partitioning", "Lazy evaluation", "Spark Streaming"],
    "transformer": ["Attention mechanism", "BERT fine-tuning", "Token embeddings", "Positional encoding"],
    "lstm": ["Vanishing gradients", "Gated units", "Sequence modelling", "Bidirectional LSTM"],
    "mlops": ["CI/CD for ML", "Model monitoring", "Data drift", "Feature store"],
    "aws": ["IAM roles", "Auto Scaling", "S3 lifecycle", "Lambda cold starts"],
    "redis": ["Cache eviction policies", "Pub/Sub", "Redis cluster", "Data persistence"],
}


# ──────────────────────────────────────────────────────────────────────────────
# LLM Caller
# ──────────────────────────────────────────────────────────────────────────────

def _call_gemini(prompt: str) -> str:
    """Send a prompt to Gemini and return the text response."""
    import os
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError("GEMINI_API_KEY is not set in environment variables.")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(prompt)
    return response.text.strip()


def _parse_json_response(raw: str) -> any:
    """Strip markdown fences and parse JSON from LLM response."""
    clean = re.sub(r"```(?:json)?", "", raw).replace("```", "").strip()
    return json.loads(clean)


# ──────────────────────────────────────────────────────────────────────────────
# Question Generation
# ──────────────────────────────────────────────────────────────────────────────

def generate_questions(
    role: str,
    skills: List[str],
    context: str,
) -> List[str]:
    """
    Use Gemini to generate 5 personalised interview questions.
    Falls back to role-specific default questions if LLM fails.
    """
    skills_str = ", ".join(skills) if skills else "general programming"

    prompt = QUESTION_GENERATION_PROMPT.format(
        role=role,
        skills=skills_str,
        context=context,
    )

    try:
        raw = _call_gemini(prompt)
        data = _parse_json_response(raw)

        if isinstance(data, list):
            questions = [item["question"] for item in data if "question" in item]
            if questions:
                logger.info(f"Generated {len(questions)} questions for role: {role}")
                return questions[:5]

    except Exception as e:
        logger.error(f"Question generation failed: {e}. Using fallback questions.")

    return _fallback_questions(role, skills)


def _fallback_questions(role: str, skills: List[str]) -> List[str]:
    """Hard-coded fallback questions per role."""
    fallbacks = {
        "AI/ML Engineer": [
            "Explain the bias-variance tradeoff and how you manage it in practice.",
            "Walk me through how you would design an end-to-end ML pipeline for a production system.",
            "How do you handle class imbalance in a classification problem?",
            "Explain the attention mechanism in Transformers and why it replaced RNNs.",
            "You trained a model with 99% accuracy, but it fails in production. What would you investigate?",
        ],
        "Backend Engineer": [
            "Explain the difference between synchronous and asynchronous programming. When do you use each?",
            "How would you design a rate limiter for a high-traffic REST API?",
            "What strategies do you use to optimise slow database queries?",
            "Explain the CAP theorem and how it affects your database choice.",
            "Walk me through how you would design a scalable microservices architecture.",
        ],
        "Data Scientist": [
            "Explain the difference between correlation and causation with a practical example.",
            "How do you approach exploratory data analysis on a new dataset?",
            "Walk me through your process for selecting and validating a machine learning model.",
            "How would you design an A/B test to evaluate a new product feature?",
            "Explain how you would communicate a complex statistical finding to a non-technical stakeholder.",
        ],
    }
    DEFAULT_FALLBACK_QUESTIONS = [
    "Tell me about your most challenging technical project.",
    "How do you approach debugging a system you are unfamiliar with?",
    "Explain a complex concept from your domain to a non-technical audience.",
    "Describe your approach to code review and quality assurance.",
    "How do you stay current with developments in your field?",
]
    return fallbacks.get(role, DEFAULT_FALLBACK_QUESTIONS)[:MAX_TOTAL_QUESTIONS]


# ──────────────────────────────────────────────────────────────────────────────
# Adaptive Follow-up
# ──────────────────────────────────────────────────────────────────────────────

def detect_keywords(answer_text: str) -> Tuple[List[str], List[str]]:
    """
    Detect trigger keywords in a candidate's answer.
    Returns (matched_keywords, followup_topics).
    """
    answer_lower = answer_text.lower()
    matched_keywords = []
    followup_topics = []

    for keyword, topics in ADAPTIVE_TRIGGERS.items():
        if keyword in answer_lower:
            matched_keywords.append(keyword)
            followup_topics.extend(topics[:2])  # Take top 2 topics per keyword

    return matched_keywords, list(set(followup_topics))


def generate_adaptive_question(
    role: str,
    previous_question: str,
    previous_answer: str,
) -> Optional[str]:
    """
    Analyse the candidate's answer and optionally generate an adaptive
    follow-up question. Returns None if no trigger keywords detected.
    """
    keywords, followup_topics = detect_keywords(previous_answer)
    if not keywords:
        return None

    prompt = ADAPTIVE_QUESTION_PROMPT.format(
        role=role,
        previous_question=previous_question,
        previous_answer=previous_answer,
        keywords=", ".join(keywords),
        followup_topics=", ".join(followup_topics),
    )

    try:
        raw = _call_gemini(prompt)
        data = _parse_json_response(raw)
        if isinstance(data, dict) and "question" in data:
            logger.info(f"Generated adaptive question for keywords: {keywords}")
            return data["question"]
    except Exception as e:
        logger.error(f"Adaptive question generation failed: {e}")

    return None


# ──────────────────────────────────────────────────────────────────────────────
# Session Helpers
# ──────────────────────────────────────────────────────────────────────────────

def create_interview_session(
    db: Session,
    candidate_id: int,
    role: str,
) -> InterviewSession:
    """Create a new interview session and persist questions to the database."""

    candidate: Optional[Candidate] = db.query(Candidate).filter(
        Candidate.id == candidate_id
    ).first()
    if not candidate:
        raise ValueError(f"Candidate {candidate_id} not found.")

    skills = json.loads(candidate.skills or "[]")

    # Retrieve RAG context
    context = retrieve_context(role, skills)

    # Generate questions
    question_texts = generate_questions(role, skills, context)
    question_texts = question_texts[:MAX_TOTAL_QUESTIONS]

    # Persist session
    session = InterviewSession(candidate_id=candidate_id, role=role, status="active")
    db.add(session)
    db.flush()  # get session.id

    # Persist questions
    for idx, q_text in enumerate(question_texts):
        question = Question(
            session_id=session.id,
            question_text=q_text,
            retrieved_context=context[:500] if idx == 0 else None,  # store for first Q only
            order_index=idx,
            question_type="standard",
        )
        db.add(question)

    db.commit()
    db.refresh(session)
    logger.info(f"Created session {session.id} with {len(question_texts)} questions.")
    return session


def get_current_question(db: Session, session_id: int) -> Optional[Question]:
    """Return the next unanswered question in a session."""
    session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
    if not session:
        raise ValueError(f"Session {session_id} not found.")

    questions = (
        db.query(Question)
        .filter(Question.session_id == session_id)
        .order_by(Question.order_index)
        .all()
    )

    for question in questions:
        if question.answer is None:
            return question

    return None  # All questions answered


def save_answer_and_check_adaptive(
    db: Session,
    session_id: int,
    question_id: int,
    answer_text: str,
) -> Tuple[Answer, bool]:

    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id
    ).first()

    if not session:
        raise ValueError(f"Session {session_id} not found.")

    question = db.query(Question).filter(
        Question.id == question_id
    ).first()

    if not question:
        raise ValueError(f"Question {question_id} not found.")

    # Save answer
    answer = Answer(question_id=question_id, answer_text=answer_text)
    db.add(answer)
    db.flush()

    # Count BEFORE adding adaptive question
    existing_count = (
        db.query(Question)
        .filter(Question.session_id == session_id)
        .count()
    )

    # HARD LIMIT CHECK (IMPORTANT)
    if existing_count >= MAX_TOTAL_QUESTIONS:
        db.commit()
        db.refresh(answer)
        next_q = get_current_question(db, session_id)
        return answer, next_q is not None

    # Generate adaptive question
    adaptive_q = generate_adaptive_question(
        role=session.role,
        previous_question=question.question_text,
        previous_answer=answer_text,
    )

    # Inject adaptive question only if allowed
    if adaptive_q and existing_count < MAX_TOTAL_QUESTIONS:
        follow_up = Question(
            session_id=session_id,
            order_index=existing_count,
            question_text=adaptive_q,
            question_type="adaptive",
        )
        db.add(follow_up)
        logger.info(
            f"Injected adaptive follow-up question into session {session_id}."
        )

    db.commit()
    db.refresh(answer)

    next_q = get_current_question(db, session_id)
    return answer, next_q is not None


def get_session_transcript(db: Session, session_id: int) -> str:
    """Build a Q&A transcript string for summary generation."""
    questions = (
        db.query(Question)
        .filter(Question.session_id == session_id)
        .order_by(Question.order_index)
        .all()
    )

    lines = []
    for i, q in enumerate(questions, 1):
        lines.append(f"Q{i}: {q.question_text}")
        if q.answer:
            lines.append(f"A{i}: {q.answer.answer_text}")
        else:
            lines.append(f"A{i}: [No answer provided]")
        lines.append("")

    return "\n".join(lines)