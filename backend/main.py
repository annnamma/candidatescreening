"""
main.py — FastAPI application entry point.
"""

import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Lifespan (startup / shutdown)
# ──────────────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting Candidate Screening Platform API...")
    from app.database.db import init_db
    init_db()
    logger.info("✅ Database ready.")
    yield
    logger.info("🛑 Shutting down.")


# ──────────────────────────────────────────────────────────────────────────────
# App creation
# ──────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="AI-Powered Candidate Screening Platform",
    description=(
        "An intelligent interview platform that parses resumes, retrieves role-specific knowledge "
        "via RAG, generates personalised interview questions, conducts adaptive interviews, "
        "and produces structured evaluation reports."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS — allow React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite default
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
from app.api.routes.interview import router  # noqa: E402
app.include_router(router, prefix="/api/v1")


# ──────────────────────────────────────────────────────────────────────────────
# Root
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/", tags=["Root"])
def root():
    return {
        "message": "AI Candidate Screening Platform",
        "docs": "/docs",
        "health": "/api/v1/health",
        "version": "1.0.0",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)