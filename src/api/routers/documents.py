from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional
import os
import aiofiles
from pathlib import Path

from src.models.groq_model import GroqModel
from src.api.schemas import DocumentUploadResponse
from src.utils.logger import logger

router = APIRouter(
    prefix="/api/documents",
    tags=["documents"]
)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'.txt', '.md', '.pdf', '.docx', '.csv', '.json'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    conversation_id: int = Form(...),
    file: UploadFile = File(...)
):
    """Upload and process a document for RAG"""
    try:
        # Validate file extension
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400, 
                detail=f"File type {file_ext} not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # Check file size
        file_size = 0
        temp_file_path = f"/tmp/{conversation_id}_{file.filename}"
        
        # Save uploaded file
        async with aiofiles.open(temp_file_path, 'wb') as f:
            while chunk := await file.read(1024 * 1024):  # Read in 1MB chunks
                file_size += len(chunk)
                if file_size > MAX_FILE_SIZE:
                    os.remove(temp_file_path)
                    raise HTTPException(
                        status_code=413,
                        detail=f"File too large. Maximum size: {MAX_FILE_SIZE / 1024 / 1024}MB"
                    )
                await f.write(chunk)
        
        # Process document
        groq_model = GroqModel(conversation_id=conversation_id)

        # Process document - now supports all allowed file types
        groq_model.process_and_store(temp_file_path)
        chunks_processed = "Document processed"  # You can get actual count from process_and_store
        
        # Clean up
        os.remove(temp_file_path)
        
        logger.info(f"Document {file.filename} processed for conversation {conversation_id}")
        
        return DocumentUploadResponse(
            status="success",
            message=f"Document {file.filename} processed successfully",
            chunks_processed=None  # Update this when we have chunk count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing document: {e}")
        # Clean up temp file if it exists
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload-url", response_model=DocumentUploadResponse)
async def upload_document_from_url(
    conversation_id: int,
    url: str
):
    """Process a document from URL (for web scraping)"""
    try:
        # This would be implemented to fetch and process web content
        # For now, return not implemented
        raise HTTPException(
            status_code=501,
            detail="URL document processing not yet implemented"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing URL: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{conversation_id}/clear")
async def clear_conversation_documents(conversation_id: int):
    """Clear all documents from a conversation's vector store"""
    try:
        from src.models.qdrant_model import QDrantModel
        qdrant_model = QDrantModel()
        qdrant_model.delete_conversation_points(conversation_id)

        return {
            "status": "success",
            "message": f"Documents cleared from conversation {conversation_id}"
        }
    except Exception as e:
        logger.error(f"Error clearing documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))