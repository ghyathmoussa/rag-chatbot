import requests
from configs.configs import GROQ_API_URL, GROQ_API_KEY, GROQ_MODEL
import openai
from typing import List
from models.embedder import Embedder
from models.qdrant_store import QdrantStore
from utils.document_loader import load_document
class GroqModel:
    def grqo_chat(system_prompt: str, user_question:str, context_chunks: List[str]):
        context = "\n\n".join(context_chunks)
        full_prompt = f"{system_prompt}\n\nContext:\n{context}\n\nUser Question:\n{user_question}"

        response = openai.ChatCompletion.create(
            api_key=GROQ_API_KEY,
            api_base=GROQ_API_URL,
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": full_prompt}
            ],
            temperature=0.3
        )
        return response["choices"][0]["message"]["content"]

    def process_and_store(file_path: str, embedder: Embedder, store: QdrantStore):
        text = load_document(file_path)
        chunks = embedder.chunk_text(text)
        embeddings = embedder.embed_chunks(chunks)
        store.store(chunks, embeddings)