"""Opt in with TEST_DATABASE_URL pointing to a disposable pgvector database."""
import os
from types import SimpleNamespace

import fitz
import pytest
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from alembic import command
from app.config import get_settings
from app.generation import service as generation
from app.ingestion.pipeline import ingest_file
from app.retrieval.lexical import lexical_search
from app.retrieval.service import retrieve


def test_pdf_to_cited_answer(tmp_path, monkeypatch):
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set TEST_DATABASE_URL to a disposable PostgreSQL database")

    monkeypatch.setenv("DATABASE_URL", url)
    get_settings.cache_clear()
    engine = create_engine(url)
    try:
        command.upgrade(Config("alembic.ini"), "head")
        pdf_path = tmp_path / "device.pdf"
        with fitz.open() as pdf:
            pdf.new_page().insert_text((50, 50), "The device operates on 24 volts.")
            pdf.new_page()
            pdf.save(pdf_path)

        vector = [1.0] + [0.0] * 383

        def embed(texts):
            return [vector for _ in texts]

        if os.getenv("TEST_REAL_MODELS") != "1":
            monkeypatch.setattr("app.ingestion.pipeline.embed_texts", embed)
            monkeypatch.setattr("app.retrieval.service.embed_texts", embed)
            monkeypatch.setattr(
                "app.retrieval.service.rerank", lambda question, chunks, limit: chunks[:limit]
            )
        with Session(engine) as db:
            metadata = {
                "title": "Device",
                "source_url": "https://example.org/device.pdf",
                "product_model": "Device-24",
            }
            doc, created = ingest_file(db, pdf_path, **metadata)
            assert created and doc.page_count == 2
            assert not ingest_file(db, pdf_path, **metadata)[1]
            question = "What voltage is required for this device?"
            for mode in ("vector", "hybrid", "hybrid_rerank"):
                assert retrieve(db, question, mode, product_model="missing") == []
                chunks = retrieve(db, question, mode, product_model="Device-24")
                assert [c.page_number for c in chunks] == [1]
            assert lexical_search(db, question, product_model="Device-24")[0].id == chunks[0].id

            monkeypatch.setattr(generation, "get_settings", lambda: SimpleNamespace(
                enable_live_generation=True, anthropic_api_key="test"
            ))
            monkeypatch.setattr(generation, "generate", lambda *_: {
                "status": "answered", "answer": "24 volts.", "citations": [str(chunks[0].id)]
            })
            result = generation.answer_question(question, chunks)
            assert result["status"] == "answered"
            assert result["citations"][0]["page_number"] == 1
            assert result["citations"][0]["source_url"] == metadata["source_url"]
            assert generation.answer_question(question, [])["status"] == "refused"
            monkeypatch.setattr(generation, "generate", lambda *_: {
                "status": "answered", "answer": "24 volts.", "citations": [{}]
            })
            assert generation.answer_question(question, chunks)["status"] == "refused"
            db.delete(doc)
            db.commit()
    finally:
        engine.dispose()
        get_settings.cache_clear()
