from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class ConversationCreate(BaseModel):
    user_id: Optional[str] = None
    title: Optional[str] = None


class ConversationUpdate(BaseModel):
    title: str


class MessageRequest(BaseModel):
    message: str


class ConversationResponse(BaseModel):
    id: int
    session_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: Optional[int] = 0
    
    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime
    context_used: Optional[List[Dict[str, Any]]] = None
    token_count: Optional[int] = None
    processing_time: Optional[float] = None
    
    class Config:
        from_attributes = True


class DocumentUploadResponse(BaseModel):
    status: str
    message: str
    chunks_processed: Optional[int] = None


class ChatMessage(BaseModel):
    type: str
    message: Optional[str] = None
    typing: Optional[bool] = None
    role: Optional[str] = None
    content: Optional[str] = None
    timestamp: Optional[str] = None


class ErrorResponse(BaseModel):
    detail: str
    status_code: int