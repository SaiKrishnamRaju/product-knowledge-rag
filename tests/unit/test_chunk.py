import pytest

from app.ingestion.chunk import chunk_pages


def test_chunks_preserve_pages_and_overlap():
    chunks = chunk_pages([{"page_number": 7, "text": "a b c d e f g"}], size=4, overlap=2)
    assert [c["content"] for c in chunks] == ["a b c d", "c d e f", "e f g"]
    assert all(c["page_number"] == 7 for c in chunks)

def test_bad_overlap():
    with pytest.raises(ValueError):
        chunk_pages([], size=5, overlap=5)
