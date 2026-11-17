import json

from app.config import get_settings
from app.generation.prompts import SYSTEM_PROMPT


def generate(question: str, chunks) -> dict:
    cfg = get_settings()
    import anthropic
    context = "\n\n".join(f"[CHUNK {c.id}]\n{c.content}" for c in chunks)
    client = anthropic.Anthropic(api_key=cfg.anthropic_api_key, timeout=30.0, max_retries=0)
    response = client.messages.create(model=cfg.claude_model, max_tokens=cfg.max_output_tokens,
                                      temperature=0, system=SYSTEM_PROMPT,
                                      messages=[{"role": "user", "content": f"Question: {question}\nEvidence:\n{context}"}])
    if response.stop_reason != "end_turn":
        return {}
    raw = "".join(block.text for block in response.content if block.type == "text")
    try:
        parsed = json.loads(raw.strip().removeprefix("```json").removesuffix("```").strip())
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}
