import hashlib
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.db.models import Chunk, Document
from app.ingestion.chunk import chunk_pages
from app.ingestion.extract import extract_pages
from app.retrieval.embed import embed_texts


def ingest_file(db, path: Path, *, title: str, source_url: str, manufacturer: str = "", product_model: str = ""):
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    existing = db.scalar(select(Document).where(Document.sha256 == digest))
    if existing:
        return existing, False
    pages = extract_pages(path)
    parts = chunk_pages(pages)
    if not parts:
        raise ValueError(f"No extractable text: {path}")
    vectors = embed_texts([part["content"] for part in parts])
    insert_document = (
        insert(Document)
        .values(
            title=title, source_url=source_url, manufacturer=manufacturer,
            product_model=product_model, sha256=digest, page_count=len(pages),
        )
        .on_conflict_do_nothing(index_elements=[Document.sha256])
        .returning(Document)
    )
    document = db.scalar(insert_document)
    if document is None:
        return db.scalar(select(Document).where(Document.sha256 == digest)), False
    for part, vector in zip(parts, vectors, strict=True):
        db.add(Chunk(document_id=document.id, page_number=part["page_number"],
                     chunk_index=part["chunk_index"], content=part["content"],
                     embedding=vector, token_count=part["token_count"],
                     content_hash=hashlib.sha256(part["content"].encode()).hexdigest()))
    db.commit()
    return document, True
