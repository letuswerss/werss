import os
from typing import Optional

from .base import EmbeddingProvider
from .bigmodel import BigModelEmbeddingProvider
from .doubao import DoubaoEmbeddingProvider


def _get_dimensions() -> Optional[int]:
    raw = os.getenv("TAG_CLUSTER_EMBEDDING_DIMENSIONS", "").strip()
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def _get_int_env(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return max(1, value)


def get_embedding_provider() -> EmbeddingProvider:
    provider = os.getenv("TAG_CLUSTER_EMBEDDING_PROVIDER", "bigmodel").strip().lower()
    dimensions = _get_dimensions()

    if provider == "bigmodel":
        api_key = os.getenv("BIGMODEL_API_KEY", "").strip()
        base_url = os.getenv("BIGMODEL_BASE_URL", "https://open.bigmodel.cn/api/paas/v4").strip()
        model = os.getenv("BIGMODEL_EMBEDDING_MODEL", "embedding-3").strip()
        if not api_key:
            raise ValueError("BIGMODEL_API_KEY 未配置")
        return BigModelEmbeddingProvider(api_key=api_key, base_url=base_url, model_name=model, dimensions=dimensions)

    if provider == "doubao":
        api_key = os.getenv("DOUBAO_API_KEY", "").strip()
        base_url = os.getenv("DOUBAO_BASE_URL", "").strip()
        model = os.getenv("DOUBAO_EMBEDDING_MODEL", "").strip()
        max_concurrency = _get_int_env("DOUBAO_EMBEDDING_MAX_CONCURRENCY", 4)
        if not api_key:
            raise ValueError("DOUBAO_API_KEY 未配置")
        if not base_url:
            raise ValueError("DOUBAO_BASE_URL 未配置")
        if not model:
            raise ValueError("DOUBAO_EMBEDDING_MODEL 未配置")
        return DoubaoEmbeddingProvider(
            api_key=api_key,
            base_url=base_url,
            model_name=model,
            dimensions=dimensions,
            max_concurrency=max_concurrency,
        )

    raise ValueError(f"不支持的 embedding provider: {provider}")
