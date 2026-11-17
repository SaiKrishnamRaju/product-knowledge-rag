from functools import lru_cache

from app.config import get_settings


@lru_cache(maxsize=1)
def reranker():
    from sentence_transformers import CrossEncoder
    return CrossEncoder(get_settings().reranker_model)

def rerank(question, chunks, limit=5):
    if not chunks:
        return []
    pairs = [(question, chunk.content) for chunk in chunks]
    directory = get_settings().onnx_model_dir
    if directory is not None:
        from app.retrieval.onnx_inference import score

        scores = score(directory / "reranker", pairs)
    else:
        scores = reranker().predict(pairs, batch_size=4)
    return [chunk for _, chunk in sorted(zip(scores, chunks), key=lambda pair: -float(pair[0]))[:limit]]
