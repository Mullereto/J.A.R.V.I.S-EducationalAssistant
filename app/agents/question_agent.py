from typing import List, Dict, Any
from app.services.question_gen import generate_questions_from_text
from app.utils.logger import get_logger

logger = get_logger("question_agent")

def create_QA(text: str, source: str = None, Q_type: str=None, n: int = 3, difficulty: int = 2) -> List[Dict[str, Any]]:
    """
    Generate questions and immediately run self-reflection on each generated question.
    """
    
    questions = generate_questions_from_text(text, source=source, Q_type=Q_type, n=n, difficulty=difficulty)
    return questions