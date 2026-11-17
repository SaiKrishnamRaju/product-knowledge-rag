from app.config import get_settings
from app.generation.citations import validate_citations
from app.generation.claude import generate


def answer_question(question, chunks):
    if not chunks:
        return {"status": "refused", "answer": "I couldn't find sufficient evidence in the indexed manuals.", "citations": []}
    settings = get_settings()
    if not settings.enable_live_generation or not settings.anthropic_api_key:
        return {"status": "refused", "answer": "Live generation is disabled. Configure Claude to answer questions.", "citations": []}
    result = generate(question, chunks)
    answer = result.get("answer") if isinstance(result, dict) else None
    if isinstance(result, dict) and result.get("status") == "refused":
        return {"status": "refused", "answer": "Insufficient evidence in the indexed manuals.", "citations": []}
    if not isinstance(answer, str) or not answer.strip() or result.get("status") != "answered":
        return {"status": "refused", "answer": "The generation provider returned an invalid answer.", "citations": []}
    citations = validate_citations(result.get("citations", []), chunks)
    if not citations:
        return {"status": "refused", "answer": "The generated answer lacked valid source citations.", "citations": []}
    return {"status": "answered", "answer": answer, "citations": citations}
