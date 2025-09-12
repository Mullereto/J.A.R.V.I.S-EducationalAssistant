from typing import List, Dict, Any
from app.services.embeddings import search
from app.utils.logger import get_logger
from app.services.summarization import call_ollama
import textwrap

logger = get_logger("qa_service")

SIMILARITY_THRESHOLD = 0.55
MAX_CONTEXT_CHUNKS = 5

def is_on_topic(query: str, k: int = 5) -> tuple[bool, List[Dict[str, Any]]]:
    """
    Check if the query is on topic.
    Returns (is_on_topic, list of relevant documents)
    """
    results = search(query, k)
    if len(results) == 0:
        return False, []
    
    top_score = results[0][0]
    
    return float(top_score) > SIMILARITY_THRESHOLD, results

def build_context(results: List[tuple], max_chunks: int = MAX_CONTEXT_CHUNKS) -> str:
    """
    Combine the top retrievals into a single context string for the LLM.
    """
    context = []
    for i ,(score, md) in enumerate(results[:max_chunks]):
        snippet = md.get("text", "")[:4000]
        context.append(f"[Doc{md.get('doc_id')}](score={score:.3f})\n{snippet}\n")
    return "\n---\n".join(context)

def assemble_prompt(query: str, context: str, chat_history: List[Dict[str, str]] = None) -> str:
    """
    Build a prompt that includes chat history and retrieved context.
    chat_history: list of {"role":"user"/"assistant", "content":"..."}
    """
    header = "You are an expert teaching assistant. Use the provided RETRIEVED CONTEXT and CHAT HISTORY to answer the QUESTION objectively and concisely YOU MUST FOLLOW THE INSTRUCTIONS."
    history_text = ""
    if chat_history:
        for msg in chat_history[-6:]:  # keep last 6 turns
            role = msg.get("role", "user")
            content = msg.get("content", "")
            history_text += f"{role.upper()}: {content}\n"
    prompt = textwrap.dedent(
        f"""{header}

    RETRIEVED CONTEXT:
    {context}

    CHAT HISTORY:
    {history_text}

    QUESTION:
    {query}

    INSTRUCTIONS:
    - Answer using only the information in the retrieved context when possible. If the answer is not present, say you don't know and optionally provide guidance on where to find it.
    - Be concise (1-3 paragraphs) and include citations to docs like [Doc <id>] where relevant.
    - Provide a short confidence estimate (low/medium/high) at the end.
    """
        )
    return prompt

def answer_query(query: str, chat_history: List[Dict[str,str]] = None, k:int = 5) -> Dict[str, Any]:
    """
    Top-level function: topic check -> retrieval -> LLM answer or polite redirect.
    Returns dict with keys: on_topic(bool), answer(str)/redirect(str), sources(list)
    """
    on_topic, results = is_on_topic(query, k=k)
    if not on_topic:
        return {
            "on_topic": False,
            "answer": None,
            "redirect": "I couldn't find relevant material in the provided course content. Please check the course materials or ask a more specific question about the covered topics.",
            "sources": []
        }
    context = build_context(results)
    prompt = assemble_prompt(query, context, chat_history)
    response = call_ollama(prompt)
    top_sources = [md.get("doc_id") for (score, md) in results[:MAX_CONTEXT_CHUNKS]]
    return {
        "on_topic": True,
        "answer": response.strip(),
        "sources": top_sources,
        "retrievals": [{"score": s, "doc_id": md["doc_id"], "source": md["source"]} for (s, md) in results[:k]]
    }