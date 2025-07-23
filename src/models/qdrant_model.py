from qdrant_client import QdrantClient
from configs.configs import QDRANT_COLLECTION_NAME
from typing import List
import uuid
from qdrant_client.models import PointStruct
from models.embedding_model import Embedder

class QDrantModel:
    def __init__(self, host, port, use_grpc: bool = False):
        self.host = host
        self.port = port
        self.use_grpc = use_grpc
        self.client = self._connect()

    def _connect(self):
        self.client = QdrantClient(host=self.host, port=self.port)

    def _disconnect(self):
        self.client.close()
    
    def store(self, chunks: List[str], embeddings: List[List[float]]):
        points = [
            PointStruct(id=str(uuid.uuid4()), vector=vec, payload={"text": chunk})
            for chunk, vec in zip(chunks, embeddings)
        ]
        self.client.upsert(collection_name=QDRANT_COLLECTION_NAME, points=points)
    
    def query(self, query: str, embedder: Embedder, top_k: int = 5) -> List[str]:
        query_vec = embedder.model.encode(query).tolist()
        hits = self.client.search(
            collection_name=QDRANT_COLLECTION_NAME,
            query_vector=query_vec,
            limit=top_k
        )
        return [hit.payload["text"] for hit in hits]