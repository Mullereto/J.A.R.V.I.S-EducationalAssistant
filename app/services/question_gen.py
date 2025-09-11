import os
import json
import uuid
from typing import List, Dict, Any
from fastapi.encoders import jsonable_encoder
from app.utils.logger import get_logger
from app.services.summarization import call_ollama
from app.models.request_models import Option

logger = get_logger("question_service")

STORE_FILE = "data/processed/questions_store.json"
QUESTIONS: Dict[str, Dict[str, Any]] = {}

def _persist_store(): # to store the question
    try:
        os.makedirs(os.path.dirname(STORE_FILE), exist_ok=True)
        with open(STORE_FILE, "w", encoding="utf-8") as f:
            json.dump(jsonable_encoder(QUESTIONS), f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning("Could not persist question store: %s", e)
        
def load_store():
    try:
        if os.path.exists(STORE_FILE):
            with open(STORE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                QUESTIONS.update(data)
    except Exception as e:
        logger.warning("Could not load question store: %s", e)
        

load_store()

def generate_questions_from_text(text: str, source: str = None, Q_type: str=None, n: int = 3, difficulty: int = 2) -> List[Dict[str, Any]]:
    """
    Use LLM to generate MCQs and TF questions. Return list of question dicts (not yet approved).
    """
    # Build prompt: ask for JSON output to facilitate parsing
    MCQ_prompt = (
        "You are an educational question generator. From the provided text, create:\n"
        f"- {n} multiple-choice questions (4 options each), with one correct option and a short rationale.\n"
        "Return the result as a JSON object: {\"Question\": [{\"question\":...,\"options\":[...],\"answer_index\":0,\"rationale\":...}, ...]}\n\n"
        "Text:\n"
        f"{text}\n\n"
        "Keep questions at difficulty level roughly matching the requested following difficulty level (1-5).\n"
        "Difficulty level 1: Basic concepts, definitions, and explanations.\n"
        "Difficulty level 2: Intermediate concepts, applications, and examples.\n"
        "Difficulty level 3: Advanced concepts, theorems, and proofs.\n"
        "Difficulty level 4: Highly specialized concepts, theories, and applications.\n"
        "Difficulty level 5: Expert-level concepts, research-level topics, and complex problems.\n"
        f"Difficulty level: {difficulty}\n"
        "Do not include any explanations, markdown, or text outside the JSON."
    )
    TF_prompt = (
        "You are an educational question generator. From the provided text, create:\n"
        f"- {n} True/False questions with the correct boolean and a short rationale.\n"
        "Return the result as a JSON object: {\"Question\": [{\"question\":...,\"answer\":true,\"rationale\":...}, ...]}\n\n"
        "Text:\n"
        f"{text}\n\n"
        "Keep questions at difficulty level roughly matching the requested following difficulty level (1-5).\n"
        "Difficulty level 1: Basic concepts, definitions, and explanations.\n"
        "Difficulty level 2: Intermediate concepts, applications, and examples.\n"
        "Difficulty level 3: Advanced concepts, theorems, and proofs.\n"
        "Difficulty level 4: Highly specialized concepts, theories, and applications.\n"
        "Difficulty level 5: Expert-level concepts, research-level topics, and complex problems.\n"
        f"Difficulty level: {difficulty}\n"
        "Do not include any explanations, markdown, or text outside the JSON."
    )
    if Q_type == "mcq":
        prompt = MCQ_prompt
    elif Q_type == "tf":
        prompt = TF_prompt
        
    raw = call_ollama(prompt)
    parsed = json.loads(raw)
    out = []
    for item in parsed.get("Question", []):
        qid = str(uuid.uuid4())
        if Q_type == "mcq":
            options = [Option(id=i, option=opt) for i, opt in enumerate(item["options"])]
        else:
            options = None
            
        if Q_type == "mcq":
            ans_index = item.get("answer_index", 0)
        else:
            ans_index = item.get("answer", False)
        qdict = {
            "question_id": qid,
            "source": source,
            "type": Q_type,
            "question": item.get("question", ""),
            "options": options,
            "answer": options[ans_index] if Q_type == "mcq" else ans_index,
            "difficulty": difficulty,
            "rationale": item.get("rationale", ""),
        }
        QUESTIONS[qid] = qdict
        out.append(qdict)
    _persist_store()
    return out

# def self_reflect_and_score(question: Dict[str, Any]) -> Dict[str, Any]:
#     """
#     Ask the LLM to review the question, rate clarity and difficulty, and suggest improvements.
#     Returns the original question dict augmented with 'reflection' key containing suggestions and a score.
#     """
#     qtext = question["question"]

#     payload = jsonable_encoder({
#         "type": question["type"],
#         "question": qtext,
#         "options": question.get("options"),
#         "answer": question["answer"],
#         "rationale": question.get("rationale", "")
#     })
#     prompt = (
#         "You are an expert pedagogy assistant. Evaluate the following question for clarity, correctness, and difficulty (1-5).\n"
#         "If there are issues, suggest an improved version of the question and better options (if MCQ), and propose a new difficulty rating.\n\n"
#         f"Question JSON:\n{json.dumps(payload, ensure_ascii=False)}\n\n"
#         "Return a JSON object: {\"clarity\":<0-1 float> , \"difficulty\":<1-5 int>, \"issues\":[...], \"suggestion\":{...}}"
#         "Do not include any explanations, markdown, or text outside the JSON"
#     )
#     raw = call_ollama(prompt)
#     print("I am RAW", raw)
#     parsed = json.loads(raw)
#     question["meta"] = question.get("meta", {})
#     question["meta"]["reflection"] = parsed
#     QUESTIONS[question["question_id"]] = question
#     _persist_store()
#     return question