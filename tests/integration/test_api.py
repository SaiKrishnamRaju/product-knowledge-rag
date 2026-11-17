from fastapi.testclient import TestClient

from app.main import app


def test_health():
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_invalid_question():
    response = TestClient(app).post("/api/v1/ask", json={"question": "x"})
    assert response.status_code == 422


def test_ask_telemetry_is_metadata_only(monkeypatch):
    from unittest.mock import Mock

    from app.observability import tracing

    client = Mock()
    monkeypatch.setattr(tracing, "_langfuse_client", lambda: client)
    monkeypatch.setattr("app.api.routes.retrieve", lambda *_: [])
    response = TestClient(app).post("/api/v1/ask", json={"question": "Private user question"})
    assert response.status_code == 200
    observation = client.start_observation.call_args.kwargs
    assert observation["name"] == "rag.ask"
    assert observation["metadata"]["status"] == "refused"
    assert set(observation["metadata"]) == {
        "status", "chunk_count", "citation_count", "retrieval_mode", "latency_ms",
    }
    client.start_observation.return_value.end.assert_called_once()
    client.start_observation.side_effect = RuntimeError("offline")
    assert TestClient(app).post(
        "/api/v1/ask", json={"question": "Private user question"}
    ).status_code == 200
