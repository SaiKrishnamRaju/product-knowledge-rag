from types import SimpleNamespace

from app.generation.citations import validate_citations


def test_rejects_unknown_citation():
    c = SimpleNamespace(id="one", document_id="doc", page_number=3,
                        document=SimpleNamespace(source_url="https://example.com/manual.pdf"))
    assert validate_citations(["unknown"], [c]) == []
    assert validate_citations(["one"], [c])[0]["page_number"] == 3
