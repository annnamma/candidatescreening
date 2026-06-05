#!/usr/bin/env python3
"""
ingest_documents.py

Run this script after placing PDFs inside:
  knowledge_base/ai_ml/
  knowledge_base/backend/
  knowledge_base/data_science/

It will:
  1. Load all PDFs from each folder.
  2. Split them into overlapping text chunks.
  3. Generate embeddings using all-MiniLM-L6-v2.
  4. Build and persist a FAISS index per role.

Usage:
    cd backend
    python ingest_documents.py
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
)
logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
KNOWLEDGE_BASE_PATH = Path(os.getenv("KNOWLEDGE_BASE_PATH", "./knowledge_base"))
VECTORSTORE_PATH = Path(os.getenv("VECTORSTORE_PATH", "./vectorstore"))
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))

ROLE_FOLDERS = {
    "ai_ml": "AI/ML Engineer",
    "backend": "Backend Engineer",
    "data_science": "Data Scientist",
}


def load_pdfs_from_folder(folder: Path) -> list:
    """Load all PDFs from a folder using LangChain's PyPDFLoader."""
    from langchain_community.document_loaders import PyPDFLoader

    documents = []
    pdf_files = list(folder.glob("*.pdf"))

    if not pdf_files:
        logger.warning(f"  No PDF files found in {folder}. Skipping.")
        return []

    for pdf_path in pdf_files:
        logger.info(f"  Loading: {pdf_path.name}")
        try:
            loader = PyPDFLoader(str(pdf_path))
            docs = loader.load()
            for doc in docs:
                doc.metadata["source"] = pdf_path.name
                doc.metadata["role_folder"] = folder.name
            documents.extend(docs)
            logger.info(f"    → {len(docs)} pages loaded.")
        except Exception as e:
            logger.error(f"  Failed to load {pdf_path.name}: {e}")

    return documents


def split_documents(documents: list) -> list:
    """Split documents into overlapping chunks."""
    from langchain.text_splitter import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ".", " ", ""],
    )
    chunks = splitter.split_documents(documents)
    logger.info(f"  Split into {len(chunks)} chunks (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP}).")
    return chunks


def build_vectorstore(chunks: list, output_path: Path):
    """Generate embeddings and build FAISS index."""
    from langchain_community.vectorstores import FAISS
    from langchain_community.embeddings import HuggingFaceEmbeddings

    logger.info(f"  Loading embedding model: {EMBEDDING_MODEL}")
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

    logger.info(f"  Building FAISS index for {len(chunks)} chunks...")
    vectorstore = FAISS.from_documents(chunks, embeddings)

    output_path.mkdir(parents=True, exist_ok=True)
    vectorstore.save_local(str(output_path))
    logger.info(f"  ✅ FAISS index saved to: {output_path}")


def ingest_role(folder_key: str, role_name: str):
    """Full ingestion pipeline for one role."""
    folder = KNOWLEDGE_BASE_PATH / folder_key
    output = VECTORSTORE_PATH / folder_key

    logger.info(f"\n{'─'*60}")
    logger.info(f"📚 Processing role: {role_name}")
    logger.info(f"   Source folder : {folder}")
    logger.info(f"   Output path   : {output}")

    if not folder.exists():
        logger.warning(f"  Folder does not exist: {folder}. Creating empty folder.")
        folder.mkdir(parents=True, exist_ok=True)
        logger.warning(f"  Place PDFs in {folder} and re-run this script.")
        return

    documents = load_pdfs_from_folder(folder)
    if not documents:
        logger.warning(f"  No documents loaded for {role_name}. Skipping index creation.")
        return

    chunks = split_documents(documents)
    build_vectorstore(chunks, output)


def main():
    logger.info("=" * 60)
    logger.info("🔧 Knowledge Base Ingestion Pipeline")
    logger.info("=" * 60)
    logger.info(f"Knowledge base: {KNOWLEDGE_BASE_PATH.resolve()}")
    logger.info(f"Vectorstore   : {VECTORSTORE_PATH.resolve()}")

    VECTORSTORE_PATH.mkdir(parents=True, exist_ok=True)

    for folder_key, role_name in ROLE_FOLDERS.items():
        ingest_role(folder_key, role_name)

    logger.info("\n" + "=" * 60)
    logger.info("✅ Ingestion complete!")
    logger.info("   The backend will now use the FAISS indices for RAG retrieval.")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()