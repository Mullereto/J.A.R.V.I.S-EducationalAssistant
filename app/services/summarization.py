import os
import requests
from typing import List, Dict
from app.utils.logger import get_logger
from time import sleep
import json

logger = get_logger(name="summarization_service")

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")

OLLAMA_API_PATH = f"{OLLAMA_URL}/api/generate"


def call_ollama(prompt:str, retries:int = 2) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
    }
    
    attempt = 0
    while attempt<=retries:
        try:
            logger.info("Calling Ollama model %s (attempt %d)", OLLAMA_MODEL, attempt + 1)
            response = requests.post(OLLAMA_API_PATH, json=payload)
            response.raise_for_status()
            data = response.json()
            
            if isinstance(data, Dict):
                text = data.get("response", "")
            
                return text
            
            return str(data)
        
        except Exception as e:
            logger.warning("Ollama call failed (attempt %d): %s", attempt + 1, e)
            attempt += 1
            sleep(1)
    
    raise RuntimeError("Failed to call Ollama after retries")


def extractive_summary(text:str, n_sentences:int=8) -> List[str]:
    """
    Use the model to extract N key sentences or bullet points.
    """
    prompt = (
        f"Extract the {n_sentences} most important sentences or bullet points from the following lecture/text.\n\n"
        f"Text:\n{text}\n\n"
        "Return the answers as a JSON array of short strings (no extra commentary). "
        "example: [\"Sentence 1\", \"Sentence 2\", ...]"
    )
    
    raw = call_ollama(prompt)
    response = json.loads(raw)
    return [str(s).strip() for s in response][:n_sentences]


def generate_TOC(text:str, max_level:int=3) -> List[Dict[str,str]]:
    """
    Use the model to generate a Table of Contents (TOC) for the given text.
    """
    prompt = (
    f"Produce a table of contents with up to {max_level} levels for the following text.\n\n"
    f"Text:\n{text}\n\n"
    "Must Return output as a JSON array has objects with keys 'title' and 'hint' no extra commentary (hint: 1-2 sentence summary). "
    "The Output must be like this example: [{\"title\": \"Title 1\", \"hint\": \"Summary of title 1\"}]"
    "The Output must be a valid JSON array. No extra commentary."
)
    raw = call_ollama(prompt)

    res = json.loads(raw)
    out = []
    for item in res:
        title = item.get("title")
        hint = item.get("hint", "")
        out.append({"title": str(title), "hint": str(hint)})
    return out

def abstractive_summary(key_points: List[str], Toc:List[Dict], style: str = "concise", comments:str=None) -> str:
    """
    Use the model to generate a summary for the given text.
    """
    kp_text = "\n".join(f"- {s}" for s in key_points)
    toc_text = "\n".join(f"- {s['title']}: {s['hint']}, " for s in Toc)
    print("i alomst finish")
    prompt = (
        f"Using the following key points and table of contents, write a {style} narrative summary suitable for a student study guide. "
        "Include brief examples where helpful, and keep it well-structured with paragraphs using the following table of contents and following the EDITOR NOTE.\n\n"
        f"Key points:\n{kp_text}\n\n"
        f"YOU MUST FOLLOW THE EDITOR NOTE: {comments}\n\n"
        f"Table of Contents:\n{toc_text}\n\n"
        "Provide the final summary only."
    )
    raw = call_ollama(prompt)

    return raw.strip()