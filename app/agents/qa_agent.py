# app/agents/qa_agent.py
from typing import Dict, Any, List
from app.services.qa_agent import answer_query
from app.utils.logger import get_logger

logger = get_logger("qa_agent_orchestrator")

def ask(query: str, chat_history: List[Dict[str, str]] = None, k:int=5) -> Dict[str,Any]:
    """
    Single entrypoint for Q&A use by router. Wraps answer_query and logs.
    """
    logger.info("Received QA request: %s", query)
    res = answer_query(query, chat_history=chat_history, k=k)
    logger.info("QA response: on_topic=%s", res.get("on_topic"))
    return res
