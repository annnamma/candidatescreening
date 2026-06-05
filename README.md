AI-Powered Candidate Screening Platform

An intelligent interview system that automates candidate screening using LLMs (Gemini), Retrieval-Augmented Generation (RAG), and adaptive question generation based on candidate responses.

🚀 Features
📄 Resume parsing and skill extraction
🔎 RAG-based knowledge retrieval using FAISS
🤖 AI-generated interview questions (Gemini LLM)
🔄 Adaptive follow-up questions based on answers
🧠 Role-specific interview flows (AI/ML, Backend, Data Science)
📊 Session-based interview tracking
📑 Auto-generated interview summaries
🌐 Full-stack system (FastAPI + React + Vite)
🏗️ Architecture
Resume Upload → Skill Extraction → RAG Retrieval → Gemini LLM
        ↓                                ↓
   Database (SQLAlchemy)        FAISS Vector Store
        ↓
Interview Session → Question Engine → Adaptive Follow-ups
        ↓
   Evaluation & Summary Generator
⚙️ Tech Stack

Backend

FastAPI
SQLAlchemy
FAISS
Google Gemini API
SentenceTransformers
PyPDF

Frontend

React (Vite)
Axios
Tailwind CSS
Lucide Icons

🧠 How It Works
User uploads resume (PDF)
System extracts skills automatically
RAG retrieves domain knowledge (AI/ML, Backend, DS)
Gemini generates personalized questions
Candidate answers questions
System detects keywords → generates adaptive follow-ups
Final session summary is generated


Resume Upload Page
Live Interview UI
Summary Report Page
🧪 API Endpoints
Backend (FastAPI)
Endpoint	Description
/upload-resume	Upload candidate resume
/start-interview	Start interview session
/question/{id}	Get next question
/answer	Submit answer
/summary/{id}	Get evaluation

🔧 Setup Instructions
1. Backend
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

Create .env:

GEMINI_API_KEY=your_key_here
2. Frontend
cd frontend
npm install
npm run dev
