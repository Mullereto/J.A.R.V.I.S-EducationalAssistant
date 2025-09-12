from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any

class preprocessResponse(BaseModel):
    source: str
    text: str
    
    
class SummarizeRequest(BaseModel):
    summary_id: Optional[str] = Field(None, description="Optional summary identifier")
    source: Optional[str] = Field(None, description="Optional source identifier (filename/url)")
    text: str = Field(..., description="Full text to summarize")
    toc_levels: int = Field(2, description="Max depth for generated TOC")
    extractive_sentences: int = Field(8, description="How many key sentences for extractive step")
    abstractive_style: Optional[str] = Field("concise", description="Tone for abstractive summary (e.g., concise, detailed)")
    comments: Optional[str] = None
    
class SummarizeResponse(BaseModel):
    summary_id: str
    source: Optional[str]
    toc: List[Dict[str, str]]
    extractive: List[str]
    abstract_summary: str
    comments: Optional[str] = None


class Option(BaseModel):
    id: int
    option: str

class QuestionItem(BaseModel):
    id: str
    source: Optional[str] = None
    type: str = Field(..., description="mcq or tf(TRUE/FALSE)")
    question: str
    options: Optional[List[Option]] = None  # for MCQ
    answer: Any  # option id for MCQ, bool for TF
    difficulty: int = Field(1, ge=1, le=5)
    rationale: Optional[str] = None  # explanation for the answer
    
class QGenRequest(BaseModel):
    question_id: str
    text: str
    source: str = None
    n_questions: int = 3
    difficulty: int = 2
    Q_type: str = None

class docIn(BaseModel):
    id: str
    text: str
    source: Optional[str] = None
    meta: Optional[Dict[str,Any]] = None

class IngestRequest(BaseModel):
    docs: List[docIn]

class QArequest(BaseModel):
    query: str
    chat_history: Optional[List[Dict[str,str]]] = None
    k: Optional[int] = 5
    
class QAResponse(BaseModel):
    on_topic: bool
    answer: Optional[str] = None
    redirect: Optional[str] = None
    sources: List[str]
    retrievals: Optional[List[Dict[str,Any]]] = None