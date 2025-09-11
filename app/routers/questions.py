# app/routers/questions.py
from fastapi import APIRouter, HTTPException
from typing import List
from app.models.request_models import QuestionItem, QGenRequest
from app.agents.question_agent import create_QA
from app.services.question_gen import QUESTIONS


router = APIRouter(prefix="/questions", tags=["Questions"])

@router.post("/generate_QA", response_model=List[QuestionItem])
async def generate_questions(request: QGenRequest):
    try:
        questions = create_QA(request.text, request.source, request.Q_type, request.n_questions, request.difficulty)
        return [QuestionItem(
            id=q["question_id"],
            source=q["source"],
            type=q["type"],
            question=q["question"],
            options=q["options"],
            answer=q["answer"],
            difficulty=q["difficulty"],
            rationale=q["rationale"],
        ) for q in questions]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))