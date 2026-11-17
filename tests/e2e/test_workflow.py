from app.generation.service import answer_question


def test_no_evidence_refusal():
    assert answer_question("unknown", [])["status"] == "refused"
