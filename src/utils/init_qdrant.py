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
            # all-mpnet-base-v2 produces 768-dimensional vectors
            client.create_collection(
                collection_name=QDRANT_COLLECTION_NAME,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),
            )
            logger.info(f"Created Qdrant collection: {QDRANT_COLLECTION_NAME}")

            # Create payload index for conversation_id for efficient filtering
            from qdrant_client.models import PayloadIndexParams, PayloadSchemaType
            client.create_payload_index(
                collection_name=QDRANT_COLLECTION_NAME,
                field_name="conversation_id",
                field_schema=PayloadSchemaType.INTEGER
            )
            logger.info(f"Created payload index for conversation_id in {QDRANT_COLLECTION_NAME}")
        else:
            logger.info(f"Qdrant collection already exists: {QDRANT_COLLECTION_NAME}")
            # Try to create payload index if it doesn't exist
            try:
                from qdrant_client.models import PayloadIndexParams, PayloadSchemaType
                client.create_payload_index(
                    collection_name=QDRANT_COLLECTION_NAME,
                    field_name="conversation_id",
                    field_schema=PayloadSchemaType.INTEGER
                )
                logger.info(f"Created payload index for conversation_id in {QDRANT_COLLECTION_NAME}")
            except Exception as e:
                # Index might already exist, that's fine
                logger.info(f"Payload index for conversation_id may already exist: {e}")

    except Exception as e:
        logger.error(f"Failed to initialize Qdrant collection: {e}")
        raise


if __name__ == "__main__":
    init_qdrant_collection()