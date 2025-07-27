from dotenv import load_dotenv
import os
from src.utils.logger import get_logger

# Only load .env if it exists, don't override existing env vars
load_dotenv(override=False)
logger = get_logger()


logger.info("Loading environment variables")

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "rag_collection")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-mpnet-base-v2")
GROQ_API_BASE = os.getenv("GROQ_API_BASE")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

logger.info(f"Environment variables loaded - QDRANT_COLLECTION_NAME: {QDRANT_COLLECTION_NAME}")