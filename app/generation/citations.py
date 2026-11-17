def validate_citations(citation_ids: list[str], chunks) -> list[dict]:
    by_id = {str(c.id): c for c in chunks}
    if not isinstance(citation_ids, list) or not citation_ids or any(
        not isinstance(key, str) or key not in by_id for key in citation_ids
    ):
        return []
    citations = []
    for key in dict.fromkeys(citation_ids):
        chunk = by_id[key]
        citations.append({"chunk_id": key, "document_id": str(chunk.document_id),
                          "page_number": chunk.page_number,
                          "source_url": chunk.document.source_url})
    return citations
