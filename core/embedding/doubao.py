from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional
import requests

from .base import EmbeddingProvider


class DoubaoEmbeddingProvider(EmbeddingProvider):
    # 目前 API 文档里只确认了 1024 / 2048 这两种稠密向量维度。
    ALLOWED_DIMENSIONS = {1024, 2048}

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model_name: str,
        dimensions: Optional[int] = None,
        max_concurrency: int = 4,
    ):
        super().__init__("doubao", model_name, dimensions)
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.max_concurrency = max(1, max_concurrency)

    def _get_request_url(self) -> str:
        # 兼容两种配置方式：
        # - 直接给完整接口地址，例如 /api/v3/embeddings/multimodal
        # - 只给服务根地址，由代码补 /embeddings
        if self.base_url.endswith("/embeddings") or self.base_url.endswith("/multimodal"):
            return self.base_url
        return f"{self.base_url}/embeddings"

    def _is_multimodal_endpoint(self) -> bool:
        return self._get_request_url().endswith("/multimodal")

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        if self.dimensions and self.dimensions not in self.ALLOWED_DIMENSIONS:
            raise ValueError(
                f"DOUBAO_EMBEDDING_DIMENSIONS 仅支持 {sorted(self.ALLOWED_DIMENSIONS)}，当前值: {self.dimensions}"
            )

        if self._is_multimodal_endpoint():
            max_workers = min(self.max_concurrency, len(texts))
            if max_workers == 1:
                return [self._embed_multimodal_text(text) for text in texts]
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                return list(executor.map(self._embed_multimodal_text, texts))

        payload = {
            "model": self.model_name,
            "input": texts,
            "encoding_format": "float",
        }
        if self.dimensions:
            payload["dimensions"] = self.dimensions

        response = requests.post(
            self._get_request_url(),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=60,
        )
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise ValueError(
                f"Doubao embedding 请求失败: status={response.status_code}, body={response.text}"
            ) from e
        data = response.json().get("data", [])
        return [item["embedding"] for item in data]

    def _embed_multimodal_text(self, text: str) -> List[float]:
        payload = {
            "model": self.model_name,
            "input": [
                {
                    "type": "text",
                    "text": text,
                }
            ],
        }

        response = requests.post(
            self._get_request_url(),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=60,
        )
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise ValueError(
                f"Doubao embedding 请求失败: status={response.status_code}, body={response.text}"
            ) from e

        data = response.json().get("data", {})
        embedding = data.get("embedding")
        if not embedding:
            raise ValueError(f"Doubao embedding 响应缺少 embedding: {response.text}")
        return embedding
