#!/usr/bin/env python3
"""Initialize Qdrant collection"""

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from src.configs.configs import QDRANT_URL, QDRANT_COLLECTION_NAME, EMBEDDING_MODEL
from src.utils.logger import logger


def init_qdrant_collection():
    """Create Qdrant collection if it doesn't exist"""
    try:
        client = QdrantClient(url=QDRANT_URL)
        
        # Check if collection exists
        collections = client.get_collections().collections
        collection_names = [c.name for c in collections]
        
        if QDRANT_COLLECTION_NAME not in collection_names:
            # Create collection with appropriate vector size
            # all-MiniLM-L6-v2 produces 384-dimensional vectors
            client.create_collection(
                collection_name=QDRANT_COLLECTION_NAME,
                vectors_config=VectorParams(size=768, distance=Distance.COSINE),
            )
            logger.info(f"Created Qdrant collection: {QDRANT_COLLECTION_NAME}")
        else:
            logger.info(f"Qdrant collection already exists: {QDRANT_COLLECTION_NAME}")
            
    except Exception as e:
        logger.error(f"Failed to initialize Qdrant collection: {e}")
        raise


if __name__ == "__main__":
    init_qdrant_collection()