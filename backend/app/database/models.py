from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .db import Base


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=True)
    resume_text = Column(Text, nullable=False)
    skills = Column(Text, nullable=True)          # JSON string: ["Python", "ML", ...]
    created_at = Column(DateTime, default=datetime.utcnow)

    sessions = relationship("InterviewSession", back_populates="candidate")


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    role = Column(String(100), nullable=False)
    status = Column(String(50), default="active")   # active | completed
    current_question_index = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    candidate = relationship("Candidate", back_populates="sessions")
    questions = relationship("Question", back_populates="session")
    summary = relationship("Summary", back_populates="session", uselist=False)


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("interview_sessions.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    retrieved_context = Column(Text, nullable=True)
    order_index = Column(Integer, default=0)
    question_type = Column(String(50), default="standard")  # standard | adaptive
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("InterviewSession", back_populates="questions")
    answer = relationship("Answer", back_populates="question", uselist=False)


class Answer(Base):
    __tablename__ = "answers"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    answer_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    question = relationship("Question", back_populates="answer")


class Summary(Base):
    __tablename__ = "summaries"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("interview_sessions.id"), nullable=False)
    strengths = Column(Text, nullable=True)           # JSON string
    weaknesses = Column(Text, nullable=True)          # JSON string
    recommendations = Column(Text, nullable=True)     # JSON string
    overall_assessment = Column(Text, nullable=True)
    score = Column(Integer, nullable=True)            # 0-100
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("InterviewSession", back_populates="summary")