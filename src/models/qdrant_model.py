from qdrant_client import QdrantClient
from src.configs.configs import QDRANT_COLLECTION_NAME, QDRANT_URL
from typing import List, Optional, Dict, Any
import uuid
from qdrant_client.models import PointStruct
from src.models.embedding_model import Embedder

class QDrantModel:
    def __init__(self, host: Optional[str] = None, port: Optional[int] = None, url: Optional[str] = None, use_grpc: bool = False):
        self.url = url or QDRANT_URL
        self.host = host
        self.port = port
        self.use_grpc = use_grpc
        self.client = self._connect()

    def _connect(self):
        if self.url:
            self.client = QdrantClient(url=self.url)
        else:
            self.client = QdrantClient(host=self.host, port=self.port)
        return self.client

    def _disconnect(self):
        self.client.close()
    
    def store(self, chunks: List[str], embeddings: List[List[float]]):
        collection_name = QDRANT_COLLECTION_NAME or "rag_collection"
        points = [
            PointStruct(id=str(uuid.uuid4()), vector=vec, payload={"text": chunk})
            for chunk, vec in zip(chunks, embeddings)
        ]
        self.client.upsert(collection_name=collection_name, points=points)
    
    def query(self, query_vec: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        from typing import Dict, Any
        collection_name = QDRANT_COLLECTION_NAME or "rag_collection"
        hits = self.client.search(
            collection_name=collection_name,
            query_vector=query_vec,
            limit=top_k
        )
        return [{"text": hit.payload["text"], "score": hit.score} for hit in hits]