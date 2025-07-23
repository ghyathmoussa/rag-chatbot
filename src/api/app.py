from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from src.api.routers import conversations, chat, documents
from src.database.connection import db_manager
from src.utils.logger import logger

app = FastAPI(
    title="RAG Chatbot API",
    version="1.0.0",
    description="A Retrieval-Augmented Generation chatbot with conversation history"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(conversations.router)
app.include_router(chat.router)
app.include_router(documents.router)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    db_status = "healthy" if db_manager.test_connection() else "unhealthy"
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
        "version": "1.0.0"
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info("Starting RAG Chatbot API...")
    
    # Test database connection
    if not db_manager.test_connection():
        logger.error("Failed to connect to database")
    else:
        logger.info("Database connection successful")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down RAG Chatbot API...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )