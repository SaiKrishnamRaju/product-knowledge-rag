"""Exercise the HTTP answer path with a simulated Anthropic SDK."""
from types import SimpleNamespace
from unittest.mock import Mock

import anthropic
import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import app


@pytest.mark.parametrize(
    ("provider_text", "stop_reason", "expected_status"),
    [
        ('{"status":"answered","answer":"26 GPIO pins.","citations":["chunk-1"]}', "end_turn", "answered"),
        ('{"status":"refused","answer":"No supporting passage.","citations":[]}', "end_turn", "refused"),
        ('{"status":"answered","answer":"26 pins.","citations":["invented"]}', "end_turn", "refused"),
        ('{"status":"answered","answer":"26 pins.","citations":["chunk-1"]}', "max_tokens", "refused"),
        ('{"status":', "end_turn", "refused"),
        ('["unexpected"]', "end_turn", "refused"),
    ],
)
def test_ask_validates_provider_response(monkeypatch, provider_text, stop_reason, expected_status):
    settings = Settings(enable_live_generation=True, anthropic_api_key="fixture")
    monkeypatch.setattr("app.generation.service.get_settings", lambda: settings)
    monkeypatch.setattr("app.generation.claude.get_settings", lambda: settings)
    chunk = SimpleNamespace(
        id="chunk-1", document_id="pico", page_number=4,
        content="The board exposes 26 GPIO pins.",
        document=SimpleNamespace(source_url="https://example.org/pico.pdf"),
    )
    monkeypatch.setattr("app.api.routes.retrieve", lambda *_: [chunk])
    sdk = Mock()
    sdk.messages.create.return_value = SimpleNamespace(
        stop_reason=stop_reason, content=[SimpleNamespace(type="text", text=provider_text)],
    )
    monkeypatch.setattr(anthropic, "Anthropic", Mock(return_value=sdk))
    question = "How many GPIO pins does the Pico expose?"
    response = TestClient(app).post("/api/v1/ask", json={"question": question})
    assert response.status_code == 200
    result = response.json()
    assert result["status"] == expected_status
    sdk.messages.create.assert_called_once()
    prompt = sdk.messages.create.call_args.kwargs["messages"][0]["content"]
    assert question in prompt
    assert f"[CHUNK {chunk.id}]\n{chunk.content}" in prompt
    if expected_status == "answered":
        assert result["citations"] == [{
            "chunk_id": "chunk-1", "document_id": "pico",
            "page_number": 4, "source_url": "https://example.org/pico.pdf",
        }]
    else:
        assert result["citations"] == []
