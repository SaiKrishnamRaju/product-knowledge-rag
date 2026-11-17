from time import perf_counter
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.api.schemas import AnswerResponse, QuestionRequest
from app.db.models import Chunk, Document
from app.db.session import get_db
from app.generation.service import answer_question
from app.observability.tracing import trace_event
from app.retrieval.service import retrieve

router = APIRouter()
DatabaseSession = Annotated[Session, Depends(get_db)]

@router.get("/health")
def health():
    return {"status": "ok"}

@router.get("/ready")
def ready(db: DatabaseSession):
    db.execute(text("SELECT 1"))
    return {"status": "ready"}

@router.get("/api/v1/stats")
def stats(db: DatabaseSession):
    return {"documents": db.scalar(select(func.count()).select_from(Document)),
            "chunks": db.scalar(select(func.count()).select_from(Chunk))}

@router.get("/api/v1/documents")
def documents(db: DatabaseSession):
    rows = db.scalars(select(Document).order_by(Document.title).limit(300)).all()
    return [{"id": str(d.id), "title": d.title, "product_model": d.product_model,
             "source_url": d.source_url, "page_count": d.page_count} for d in rows]

@router.post("/api/v1/search")
def search(payload: QuestionRequest, db: DatabaseSession):
    start = perf_counter()
    chunks = retrieve(db, payload.question, payload.retrieval_mode, payload.top_k, payload.product_model)
    trace_event(
        "rag.search", retrieval_mode=payload.retrieval_mode, chunk_count=len(chunks),
        latency_ms=round((perf_counter() - start) * 1000),
    )
    return [{"chunk_id": str(c.id), "content": c.content, "page_number": c.page_number,
             "document_id": str(c.document_id), "source_url": c.document.source_url} for c in chunks]

@router.post("/api/v1/ask", response_model=AnswerResponse)
def ask(payload: QuestionRequest, db: DatabaseSession):
    start = perf_counter()
    chunks = retrieve(db, payload.question, payload.retrieval_mode, payload.top_k, payload.product_model)
    try:
        result = answer_question(payload.question, chunks)
    except Exception as exc:
        trace_event(
            "rag.ask", retrieval_mode=payload.retrieval_mode, chunk_count=len(chunks),
            status="provider_error", latency_ms=round((perf_counter() - start) * 1000),
        )
        raise HTTPException(status_code=502, detail="Generation provider unavailable") from exc
    latency_ms = round((perf_counter() - start) * 1000)
    trace_event(
        "rag.ask", retrieval_mode=payload.retrieval_mode, chunk_count=len(chunks),
        status=result["status"], citation_count=len(result["citations"]), latency_ms=latency_ms,
    )
    return {**result, "retrieval_mode": payload.retrieval_mode, "latency_ms": latency_ms}
