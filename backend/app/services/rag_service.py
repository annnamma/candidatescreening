"""
rag_service.py
Handles FAISS vector store loading and context retrieval for the RAG pipeline.
"""

import os
import logging
from typing import List, Optional
from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Role → Vectorstore path mapping
# ──────────────────────────────────────────────────────────────────────────────

ROLE_TO_INDEX: dict = {
    "AI/ML Engineer": "ai_ml",
    "Backend Engineer": "backend",
    "Data Scientist": "data_science",
}

VECTORSTORE_BASE = Path(os.getenv("VECTORSTORE_PATH", "./vectorstore"))
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
TOP_K = int(os.getenv("TOP_K_RETRIEVAL", "5"))

# Cached embedding model (loaded once)
_embedding_model: Optional[HuggingFaceEmbeddings] = None


def _get_embeddings() -> HuggingFaceEmbeddings:
    global _embedding_model
    if _embedding_model is None:
        logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
        _embedding_model = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
    return _embedding_model


# ──────────────────────────────────────────────────────────────────────────────
# Query Builder
# ──────────────────────────────────────────────────────────────────────────────

def build_retrieval_query(role: str, skills: List[str]) -> str:
    """
    Build a rich natural-language query from the role and candidate skills.
    This is used to search the FAISS vector store.
    """
    role_concepts = {
        "AI/ML Engineer": [
            "machine learning algorithms", "neural networks", "model training",
            "deep learning", "model evaluation", "feature engineering",
        ],
        "Backend Engineer": [
            "REST API design", "database optimisation", "system design",
            "scalability", "microservices", "async programming", "API security",
        ],
        "Data Scientist": [
            "statistical analysis", "data visualisation", "hypothesis testing",
            "exploratory data analysis", "predictive modelling", "data cleaning",
        ],
    }

    base_concepts = role_concepts.get(role, [])
    all_terms = skills[:6] + base_concepts[:4]  # Limit to avoid noise
    query = ", ".join(all_terms)
    logger.info(f"Built retrieval query: {query[:120]}...")
    return query


# ──────────────────────────────────────────────────────────────────────────────
# Context Retrieval
# ──────────────────────────────────────────────────────────────────────────────

def retrieve_context(role: str, skills: List[str]) -> str:
    """
    Retrieve the top-K most relevant text chunks from the role-specific
    FAISS vector store for a given candidate.

    Returns a formatted string of retrieved chunks, or a fallback string
    if the vector store does not exist yet.
    """
    role_key = ROLE_TO_INDEX.get(role)
    if not role_key:
        logger.warning(f"Unknown role: {role}. Using generic context.")
        return _generic_context(role, skills)

    index_path = VECTORSTORE_BASE / role_key

    if not index_path.exists():
        logger.warning(
            f"Vector store not found at {index_path}. "
            "Run `python ingest_documents.py` after placing PDFs in knowledge_base/."
        )
        return _generic_context(role, skills)

    try:
        embeddings = _get_embeddings()
        vectorstore = FAISS.load_local(
            str(index_path),
            embeddings,
            allow_dangerous_deserialization=True,
        )

        query = build_retrieval_query(role, skills)
        docs = vectorstore.similarity_search(query, k=TOP_K)

        if not docs:
            return _generic_context(role, skills)

        chunks = []
        for i, doc in enumerate(docs, 1):
            source = doc.metadata.get("source", "knowledge base")
            chunks.append(f"[Context {i} | Source: {source}]\n{doc.page_content.strip()}")

        return "\n\n".join(chunks)

    except Exception as e:
        logger.error(f"FAISS retrieval error: {e}")
        return _generic_context(role, skills)


# ──────────────────────────────────────────────────────────────────────────────
# Generic fallback context (used when vectorstore is unavailable)
# ──────────────────────────────────────────────────────────────────────────────

def _generic_context(role: str, skills: List[str]) -> str:
    """
    Minimal fallback context based on role and skills when the
    knowledge base has not been ingested yet.
    """
    skills_str = ", ".join(skills[:8]) if skills else "general programming"

    fallbacks = {
        "AI/ML Engineer": f"""
Key concepts for AI/ML Engineers:
- Bias-variance tradeoff: balancing model complexity to minimise both underfitting and overfitting.
- Gradient descent variants: SGD, Adam, RMSProp and their impact on convergence.
- Neural network architectures: CNNs for image tasks, RNNs/LSTMs for sequences, Transformers for NLP.
- Regularisation techniques: L1/L2, dropout, batch normalisation to prevent overfitting.
- Model evaluation: precision, recall, F1, ROC-AUC, confusion matrix interpretation.
- Feature engineering: encoding, scaling, imputation, and selection strategies.
- MLOps: model versioning, experiment tracking (MLflow, W&B), CI/CD for ML pipelines.
Candidate skills: {skills_str}.
""",
        "Backend Engineer": f"""
Key concepts for Backend Engineers:
- REST API design: HTTP verbs, status codes, idempotency, pagination, versioning.
- Database design: normalisation, indexing strategies, query optimisation, transactions (ACID).
- Asynchronous programming: event loops, coroutines, message queues (Kafka, RabbitMQ).
- System design: load balancing, caching (Redis), horizontal vs vertical scaling.
- Security: JWT authentication, OAuth 2.0, SQL injection prevention, rate limiting.
- Microservices: service discovery, API gateway, circuit breaker pattern.
- Containerisation: Docker, Kubernetes deployments, health checks.
Candidate skills: {skills_str}.
""",
        "Data Scientist": f"""
Key concepts for Data Scientists:
- Statistical inference: hypothesis testing, p-values, confidence intervals, A/B testing.
- EDA: distribution analysis, correlation, outlier detection, missing value treatment.
- Supervised learning: regression, classification algorithms and their assumptions.
- Model selection: cross-validation, grid/random search, bias-variance tradeoff.
- Feature engineering: encoding categorical variables, scaling, dimensionality reduction (PCA).
- Data storytelling: translating findings into actionable business insights.
- Big data tools: Spark, distributed computing concepts, data pipeline design.
Candidate skills: {skills_str}.
""",
    }

    return fallbacks.get(role, f"Role: {role}. Candidate skills: {skills_str}.").strip()


# ──────────────────────────────────────────────────────────────────────────────
# Health check
# ──────────────────────────────────────────────────────────────────────────────

def vectorstore_status() -> str:
    """Return a status string for the health endpoint."""
    any_found = any(
        (VECTORSTORE_BASE / key).exists()
        for key in ROLE_TO_INDEX.values()
    )
    return "available" if any_found else "not_ingested"