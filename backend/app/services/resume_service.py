"""
resume_service.py
Handles PDF text extraction and skill / technology identification.
"""

import re
import json
import logging
from typing import List, Dict, Optional, Tuple
from pathlib import Path

import pdfplumber
import PyPDF2

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Comprehensive technology dictionary
# ──────────────────────────────────────────────────────────────────────────────

SKILL_DICTIONARY: Dict[str, List[str]] = {
    # Programming Languages
    "languages": [
        "Python", "Java", "JavaScript", "TypeScript", "C\\+\\+", "C#", "Go",
        "Rust", "Kotlin", "Swift", "Ruby", "PHP", "Scala", "R", "MATLAB",
        "Bash", "Shell", "Perl", "Haskell", "Lua",
    ],
    # ML / AI
    "ml_ai": [
        "Machine Learning", "Deep Learning", "Neural Network", "NLP",
        "Natural Language Processing", "Computer Vision", "Reinforcement Learning",
        "Supervised Learning", "Unsupervised Learning", "Transfer Learning",
        "Feature Engineering", "Model Deployment", "MLOps", "AutoML",
        "Generative AI", "LLM", "Large Language Model", "Transformer",
        "BERT", "GPT", "Diffusion Model", "GANs", "Attention Mechanism",
        "Bias-Variance", "Overfitting", "Regularisation", "Regularization",
        "Hyperparameter", "Cross-Validation", "Ensemble", "Gradient Boosting",
        "Random Forest", "Decision Tree", "SVM", "Support Vector",
        "Logistic Regression", "Linear Regression", "K-Means", "Clustering",
        "Dimensionality Reduction", "PCA", "t-SNE", "UMAP",
    ],
    # ML Frameworks
    "ml_frameworks": [
        "TensorFlow", "PyTorch", "Keras", "Scikit-learn", "XGBoost",
        "LightGBM", "CatBoost", "Hugging Face", "Transformers", "SpaCy",
        "NLTK", "OpenCV", "Detectron", "JAX", "Flax", "MXNet",
    ],
    # Data
    "data": [
        "SQL", "MySQL", "PostgreSQL", "SQLite", "MongoDB", "Redis",
        "Cassandra", "DynamoDB", "Elasticsearch", "Spark", "Hadoop",
        "Kafka", "Airflow", "dbt", "Pandas", "NumPy", "Polars",
        "Data Warehouse", "ETL", "Data Pipeline", "Feature Store",
        "BigQuery", "Snowflake", "Redshift", "Databricks",
    ],
    # Backend / Web
    "backend": [
        "FastAPI", "Flask", "Django", "Express", "Spring Boot", "Rails",
        "Node.js", "NodeJS", "REST", "GraphQL", "gRPC", "WebSocket",
        "Microservices", "API Gateway", "Celery", "RabbitMQ",
        "Authentication", "JWT", "OAuth", "Async", "Concurrency",
    ],
    # Frontend
    "frontend": [
        "React", "Vue", "Angular", "Next.js", "Svelte", "HTML", "CSS",
        "Tailwind", "Bootstrap", "TypeScript", "Redux", "Zustand",
        "GraphQL", "REST API", "Axios", "Webpack", "Vite",
    ],
    # DevOps / Cloud
    "devops_cloud": [
        "Docker", "Kubernetes", "AWS", "GCP", "Azure", "Terraform",
        "Ansible", "Jenkins", "GitHub Actions", "CI/CD", "Linux",
        "Nginx", "Load Balancer", "Monitoring", "Prometheus", "Grafana",
        "ECS", "ECR", "Lambda", "S3", "EC2", "GKE", "EKS",
    ],
    # Version Control / Tools
    "tools": [
        "Git", "GitHub", "GitLab", "Bitbucket", "Jira", "Confluence",
        "Postman", "VS Code", "IntelliJ", "Jupyter", "Colab",
        "MLflow", "Weights & Biases", "WandB", "DVC", "Vertex AI",
    ],
}

# Flatten into a single list for quick matching
ALL_SKILLS: List[str] = [s for skills in SKILL_DICTIONARY.values() for s in skills]


# ──────────────────────────────────────────────────────────────────────────────
# PDF Text Extraction
# ──────────────────────────────────────────────────────────────────────────────

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extract raw text from a PDF using pdfplumber (primary) with
    PyPDF2 as fallback.
    """
    text = ""

    # Primary: pdfplumber (better layout handling)
    try:
        import io
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            pages_text = []
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    pages_text.append(page_text)
            text = "\n".join(pages_text)
    except Exception as e:
        logger.warning(f"pdfplumber failed: {e}. Trying PyPDF2...")

    # Fallback: PyPDF2
    if not text.strip():
        try:
            import io
            reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
            pages_text = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    pages_text.append(page_text)
            text = "\n".join(pages_text)
        except Exception as e:
            logger.error(f"PyPDF2 also failed: {e}")
            raise ValueError("Could not extract text from PDF. Ensure the file is a valid, text-based PDF.")

    if not text.strip():
        raise ValueError("Extracted text is empty. The PDF may be image-based or password-protected.")

    return text.strip()


# ──────────────────────────────────────────────────────────────────────────────
# Skill Extraction
# ──────────────────────────────────────────────────────────────────────────────

def extract_skills(text: str) -> List[str]:
    """
    Extract skills and technologies from resume text using keyword matching
    and regex against the technology dictionary.
    """
    found_skills = set()
    text_lower = text.lower()

    for skill in ALL_SKILLS:
        # Build case-insensitive word-boundary pattern
        # Escape special regex chars in skill name
        pattern = r"\b" + re.escape(skill) + r"\b"
        try:
            if re.search(pattern, text, re.IGNORECASE):
                found_skills.add(skill)
        except re.error:
            # Fallback: simple substring search
            if skill.lower() in text_lower:
                found_skills.add(skill)

    return sorted(list(found_skills))


# ──────────────────────────────────────────────────────────────────────────────
# Name Extraction (simple heuristic)
# ──────────────────────────────────────────────────────────────────────────────

def extract_name(text: str) -> Optional[str]:
    """
    Attempt to extract the candidate's name from the first few lines
    of the resume text.
    """
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    for line in lines[:5]:
        # Name lines are usually short (2-5 words), no special chars
        words = line.split()
        if 2 <= len(words) <= 5 and all(w[0].isupper() for w in words if w):
            # Exclude lines that look like headings
            headings = {"resume", "curriculum", "vitae", "cv", "profile", "summary"}
            if not any(h in line.lower() for h in headings):
                return line
    return None


# ──────────────────────────────────────────────────────────────────────────────
# Full Resume Parser
# ──────────────────────────────────────────────────────────────────────────────

def parse_resume(file_bytes: bytes) -> Dict:
    """
    Full pipeline: extract text → extract name → extract skills.
    Returns a dict with text, name, and skills.
    """
    text = extract_text_from_pdf(file_bytes)
    name = extract_name(text)
    skills = extract_skills(text)

    return {
        "text": text,
        "name": name,
        "skills": skills,
        "skills_json": json.dumps(skills),
    }