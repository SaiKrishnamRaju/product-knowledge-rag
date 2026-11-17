def reciprocal_rank_fusion(ranked_lists: list[list[str]], k: int = 60) -> list[tuple[str, float]]:
    if k <= 0:
        raise ValueError("k must be positive")
    scores: dict[str, float] = {}
    for results in ranked_lists:
        for rank, chunk_id in enumerate(dict.fromkeys(results), start=1):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda item: (-item[1], item[0]))
