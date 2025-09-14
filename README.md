# J.A.R.V.I.S — Educational Assistant

J.A.R.V.I.S is an AI-powered Agent WorkFlow assistant for educators.  
It allows teachers to upload course materials (PDF, audio, video), automatically generate summaries, create practice questions (MCQ / True-False), and run Q&A sessions grounded in course content.

Built with **FastAPI + Streamlit + HuggingFace + FAISS**

---

## Features

- Upload Materials: PDF, audio, video → automatically converted to clean text.  
- Summarization: Extractive + Abstractive summaries with generated Table of Contents.  
- Question Generation: MCQ & True/False questions with difficulty levels and refinement.  
- Educator Approval Loop: Approve, reject, or refine generated questions.  
- Q&A (RAG): Ask natural language questions with context-aware answers grounded in uploaded materials.  
- Authentication: Demo educator login.  
- Frontend: Streamlit app with tabs for each feature.  
- Backend: FastAPI serving REST APIs.  

---

## Project Structure

```
Study-Assistant/
│── app/
│   ├── agents/              # LLM agents (question gen, QA)
│   ├── models/              # Pydantic request/response models
│   ├── routers/             # FastAPI endpoints (preprocess, summarize, questions, qa)
│   ├── services/            # Core logic (summarizer, question_gen, RAG store)
│   ├── utils/               # File parsing, transcription helpers
│   ├── main.py              # FastAPI entrypoint
│   └── streamlit_app.py     # Educator-facing UI (Streamlit)
│
│── requirements.txt         # Python dependencies
│── README.md                # Documentation
│── LICENSE                  # MIT License
│── .gitignore               # Ignore files
```

---

## Installation

### 1. Clone repo
```bash
git clone https://github.com/Mullereto/Study-Assistant.git
cd Study-Assistant
```

### 2. Create environment
```bash
python -m venv venv
source venv/bin/activate   # on Linux/Mac
venv\Scripts\activate      # on Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

---

## Running Locally

### 1. Start backend (FastAPI)
```bash
uvicorn app.main:app --reload
```
API docs available at: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 2. Start frontend (Streamlit)
```bash
streamlit run streamlit_app.py
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/Preprocess` | POST | Upload PDF/audio/video → get text |
| `/summarize/Summary` | POST | Generate summary + TOC |
| `/questions/generate_QA` | POST | Generate MCQ/TF questions |
| `/questions/refine` | POST | Refine a question with instructions |
| `/questions/approve` | POST | Approve/Reject question |
| `/qa/ingest` | POST | Ingest docs into vector DB |
| `/qa/ask` | POST | Ask a question (RAG) |

---

## Demo Login

- Username: `educator`  
- Password: `password123`  

---

## Demo Video

I will added
