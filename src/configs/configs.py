from dotenv import load_dotenv
import os
from utils.logger import get_logger

load_dotenv()
logger = get_logger()


logger.info("Loading environment variables")

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
GROQ_API_BASE = os.getenv("GROQ_API_BASE")
GROQ_MODEL = os.getenv("GROQ_MODEL")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

logger.info("Environment variables loaded")