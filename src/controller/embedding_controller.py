from src.models.embedding_model import Embedder
from typing import List

class EmbeddingController:
    def __init__(self):
        self.embedder = Embedder()

    def embed_text(self, text: str) -> List[float]:
        return self.embedder.embed_text(text)