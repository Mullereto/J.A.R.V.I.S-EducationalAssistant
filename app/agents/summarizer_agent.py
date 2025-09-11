from typing import Dict, Any
from app.utils.logger import get_logger
from app.services.summarization import extractive_summary, abstractive_summary, generate_TOC
import uuid

logger = get_logger(name="summarizer_agent")

SUMMARY_STORE: Dict[str, Dict[str, Any]] = {}
def create_summary(text:str, summary_id:str=None, feedback:str=None, source:str=None, toc_level:int=3,
                   extractive_sentance:int=8,
                   abstractive_style:str="concise",) -> Dict[str, Any]:
    
    """
    Create a summary of the text using extractive and abstractive methods.
    """
    if summary_id is None:
        summary_id = str(uuid.uuid4())
    
    logger.info("Creating summary %s for source %s", summary_id, source)
    key_points = extractive_summary(text, extractive_sentance)
    enhanced_kp = key_points + [f"EDITOR NOTE: {feedback}"]
    toc = generate_TOC(text, toc_level)
    
    abstract = abstractive_summary(enhanced_kp, toc, abstractive_style)
    
    payload = {
        "id": summary_id,
        "source": source,
        "toc": toc,
        "extractive": key_points,
        "abstract": abstract,
        "comments": feedback
    }
    SUMMARY_STORE[summary_id] = payload    
    return SUMMARY_STORE[summary_id]

    

