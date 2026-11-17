from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_env: str = "development"
    database_url: str = "postgresql+psycopg://app:app@localhost:5432/product_rag"
    anthropic_api_key: str = ""
    claude_model: str = "claude-sonnet-4-5"
    max_output_tokens: int = 700
    max_daily_llm_requests: int = 20
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    onnx_model_dir: Path | None = None
    vector_top_k: int = 20
    lexical_top_k: int = 20
    fusion_top_k: int = 20
    final_top_k: int = 5
    rrf_k: int = 60
    enable_live_generation: bool = False
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_base_url: str = ""

@lru_cache
def get_settings() -> Settings:
    return Settings()
