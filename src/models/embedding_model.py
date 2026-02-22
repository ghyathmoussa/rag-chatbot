from sentence_transformers import SentenceTransformer
import tiktoken
from typing import List
from dotenv import load_dotenv
import os
from src.utils.logger import get_logger
load_dotenv(override=False)
logger = get_logger()

class Embedder:
    def __init__(self, model_name: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")):
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