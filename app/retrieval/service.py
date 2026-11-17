from app.config import get_settings
from app.retrieval.embed import embed_texts
from app.retrieval.fusion import reciprocal_rank_fusion
from app.retrieval.lexical import lexical_search
from app.retrieval.rerank import rerank
from app.retrieval.vector import vector_search

MODES = {"vector", "hybrid", "hybrid_rerank"}

def retrieve(db, question: str, mode="hybrid_rerank", top_k=5, product_model=None):
    if mode not in MODES:
        raise ValueError(f"Unknown retrieval mode: {mode}")
    cfg = get_settings()
    vector = embed_texts([question])[0]
    semantic = vector_search(db, vector, cfg.vector_top_k, product_model)
    if mode == "vector":
        return semantic[:top_k]
    lexical = lexical_search(db, question, cfg.lexical_top_k, product_model)
    by_id = {str(chunk.id): chunk for chunk in semantic + lexical}
    ranked = reciprocal_rank_fusion([[str(c.id) for c in semantic],
                                      [str(c.id) for c in lexical]], cfg.rrf_k)
    fused = [by_id[key] for key, _ in ranked[:cfg.fusion_top_k]]
    return rerank(question, fused, top_k) if mode == "hybrid_rerank" else fused[:top_k]
