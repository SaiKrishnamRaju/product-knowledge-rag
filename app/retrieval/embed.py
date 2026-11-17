from functools import lru_cache

from app.config import get_settings


@lru_cache(maxsize=1)
def embedding_model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(get_settings().embedding_model)

def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    directory = get_settings().onnx_model_dir
    if directory is not None:
        from app.retrieval.onnx_inference import embed

        return embed(directory / "embedder", texts)
    return embedding_model().encode(texts, normalize_embeddings=True).tolist()
