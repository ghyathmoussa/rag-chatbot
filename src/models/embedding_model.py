from sentence_transformers import SentenceTransformer
import tiktoken
from typing import List

class Embedder:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.tokenizer = tiktoken.get_encoding("cl100k_base")

    def chunk_text(self, text: str, max_tokens: int = 300, overlap: int = 50) -> List[str]:
        words = text.split()
        chunks = []
        i = 0
        while i < len(words):
            chunk = words[i:i + max_tokens]
            token_count = len(self.tokenizer.encode(" ".join(chunk)))
            if token_count > max_tokens:
                chunk = self.tokenizer.decode(self.tokenizer.encode(" ".join(chunk))[:max_tokens])
            chunks.append(" ".join(chunk))
            i += max_tokens - overlap
        return chunks
    
    def embed_chunks(self, chunks: List[str]) -> List[List[float]]:
        return self.model.encode(chunks, convert_to_tensor=False)