from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from app.agents.qa_agent import ask
from app.services.embeddings import add_documents, get_index_size
from app.models.request_models import QArequest, QAResponse, IngestRequest

router = APIRouter(prefix="/qa", tags=["QA"])



@router.post("/ingest")
async def ingest(req: IngestRequest):
    """
    Ingest documents (e.g., chunks from transcripts or PDF pages) into FAISS.
    """
    docs = []
    for d in req.docs:
        docs.append({"id": d.id, "text": d.text, "source": d.source, "meta": d.meta or {}})
    added = add_documents(docs)
    return {"added": added, "index_size": get_index_size()}

@router.post("/ask", response_model=QAResponse)
async def ask_question(req: QArequest):
    try:
        res = ask(req.query, chat_history=req.chat_history or [], k=req.k or 5)
        if not res["on_topic"]:
            return QAResponse(on_topic=False, answer=None, redirect=res["redirect"], sources=[])
        return QAResponse(on_topic=True, answer=res["answer"], redirect=None, sources=res["sources"], retrievals=res.get("retrievals"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))