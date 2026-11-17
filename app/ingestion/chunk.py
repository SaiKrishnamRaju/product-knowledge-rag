import re


def chunk_pages(pages: list[dict], size: int = 500, overlap: int = 75) -> list[dict]:
    """Whitespace-token MVP; preserve page boundaries and stable chunk positions."""
    if size <= 0 or not 0 <= overlap < size:
        raise ValueError("Require size > 0 and 0 <= overlap < size")
    output = []
    for page in pages:
        tokens = re.findall(r"\S+", page["text"])
        for idx, start in enumerate(range(0, len(tokens), size - overlap)):
            part = tokens[start:start + size]
            if not part:
                break
            output.append({"page_number": page["page_number"], "chunk_index": idx,
                           "content": " ".join(part), "token_count": len(part)})
            if start + size >= len(tokens):
                break
    return output
