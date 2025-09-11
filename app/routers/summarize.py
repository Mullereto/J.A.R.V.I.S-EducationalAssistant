from fastapi import APIRouter, HTTPException
from app.models.request_models import SummarizeRequest, SummarizeResponse
from app.agents.summarizer_agent import create_summary, SUMMARY_STORE

router = APIRouter(prefix="/summarize", tags=["Summarization"])

@router.post("/Summary", response_model=SummarizeResponse)
async def summarize(request: SummarizeRequest):
    try:
        payload = create_summary(
            text=request.text,
            summary_id=request.summary_id,
            feedback=request.comments,
            source=request.source,
            toc_level=request.toc_levels,
            extractive_sentance=request.extractive_sentences,
            abstractive_style=request.abstractive_style,
        )
        return SummarizeResponse(
            summary_id=payload["id"],
            source=payload["source"],
            toc=payload["toc"],
            extractive=payload["extractive"],
            abstract_summary=payload["abstract"],
            comments=payload["comments"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
