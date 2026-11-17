from app.ingestion.chunk import chunk_pages


def test_empty_page_not_chunked():
    assert chunk_pages([{"page_number": 1, "text": ""}]) == []
