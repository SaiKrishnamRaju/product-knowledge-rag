from typing import Literal

from pydantic import BaseModel, Field


class QuestionRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)
    product_model: str | None = Field(default=None, max_length=120)
    retrieval_mode: Literal["vector", "hybrid", "hybrid_rerank"] = "hybrid_rerank"
    top_k: int = Field(default=5, ge=1, le=10)

class Citation(BaseModel):
    document_id: str
    chunk_id: str
    page_number: int
    source_url: str

class AnswerResponse(BaseModel):
    status: Literal["answered", "refused"]
    answer: str
    citations: list[Citation]
    retrieval_mode: str
    latency_ms: int
