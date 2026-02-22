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
        
        if not words:  # Handle empty text
            return chunks
            
        while i < len(words):
            # Take a chunk of words
            chunk_words = words[i:i + max_tokens]
            
            # If this is the last chunk and we've already processed it, break
            if not chunk_words:
                break
                
            chunk_text = " ".join(chunk_words)
            
            # Check token count and trim if necessary
            tokens = self.tokenizer.encode(chunk_text)
            if len(tokens) > max_tokens:
                # Decode only the allowed number of tokens
                chunk_text = self.tokenizer.decode(tokens[:max_tokens])
            
            chunks.append(chunk_text)
            
            # Move forward by (max_tokens - overlap)
            step = max_tokens - overlap
            if step <= 0:  # Prevent infinite loop if overlap >= max_tokens
                step = 1
                
            i += step
            
            # If we're at the end, break to avoid duplicate chunks
            if i >= len(words) - overlap:
                break
                
        return chunks
    
    def embed_chunks(self, chunks: List[str]) -> List[List[float]]:
        return self.model.encode(chunks, convert_to_tensor=False)