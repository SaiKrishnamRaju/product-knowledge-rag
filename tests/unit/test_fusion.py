from app.retrieval.fusion import reciprocal_rank_fusion


def test_rrf_rewards_consensus():
    ranked = reciprocal_rank_fusion([["a", "b"], ["b", "c"]])
    assert ranked[0][0] == "b"

def test_rrf_empty():
    assert reciprocal_rank_fusion([]) == []

def test_rrf_no_double_count_in_list():
    assert reciprocal_rank_fusion([["a", "a"]]) == [("a", 1 / 61)]
