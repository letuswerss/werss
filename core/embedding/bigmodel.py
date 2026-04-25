from typing import List, Optional
import requests

from .base import EmbeddingProvider


class BigModelEmbeddingProvider(EmbeddingProvider):
    # BigModel API 限制每次最多 64 条输入
    MAX_BATCH_SIZE = 64

    def __init__(self, api_key: str, base_url: str, model_name: str, dimensions: Optional[int] = None):
        super().__init__("bigmodel", model_name, dimensions)
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        all_embeddings = []
        # 分批处理以满足 API 限制
        for i in range(0, len(texts), self.MAX_BATCH_SIZE):
            batch = texts[i:i + self.MAX_BATCH_SIZE]
            batch_embeddings = self._embed_batch(batch)
            all_embeddings.extend(batch_embeddings)

        return all_embeddings

    def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        """处理单批次请求"""
        payload = {
            "model": self.model_name,
            "input": texts,
        }

        try:
            response = requests.post(
                f"{self.base_url}/embeddings",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=60,
            )
            response.raise_for_status()
            data = response.json().get("data", [])
            return [item["embedding"] for item in data]
        except requests.exceptions.HTTPError as e:
            print(f"BigModel API Error: {e}")
            print(f"Request payload: {payload}")
            print(f"Response status: {e.response.status_code}")
            print(f"Response body: {e.response.text}")
            raise
