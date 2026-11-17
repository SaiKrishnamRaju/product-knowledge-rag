from app.retrieval.service import MODES


def test_all_retrieval_modes_present():
    assert MODES == {"vector", "hybrid", "hybrid_rerank"}
