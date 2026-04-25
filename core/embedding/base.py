from abc import ABC, abstractmethod
from typing import List, Optional


class EmbeddingProvider(ABC):
    def __init__(self, provider_name: str, model_name: str, dimensions: Optional[int] = None):
        self.provider_name = provider_name
        self.model_name = model_name
        self.dimensions = dimensions

    @abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError

