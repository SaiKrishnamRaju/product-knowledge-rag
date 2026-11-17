import logging
from functools import lru_cache

from app.config import get_settings

logger = logging.getLogger("product_rag")


@lru_cache(maxsize=1)
def _langfuse_client():
    settings = get_settings()
    if not settings.langfuse_public_key or not settings.langfuse_secret_key:
        return None

    from langfuse import Langfuse

    return Langfuse(
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key,
        base_url=settings.langfuse_base_url or None,
        environment=settings.app_env,
    )


def trace_event(name: str, **attributes):
    """Record request metrics without including questions or generated content."""
    logger.info("%s %s", name, attributes)
    try:
        client = _langfuse_client()
        if client is not None:
            client.start_observation(name=name, metadata=attributes).end()
    except Exception:  # noqa: BLE001 — telemetry failures must not break API requests
        logger.warning("Could not record Langfuse event %s", name)
