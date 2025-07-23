from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from src.api.schemas import (
    ConversationCreate, 
    ConversationResponse, 
    ConversationUpdate,
    MessageResponse
)
from src.database.conversation_service import conversation_service
from src.utils.logger import logger

router = APIRouter(
    prefix="/api/conversations",
    tags=["conversations"]
)


@router.post("", response_model=ConversationResponse)
async def create_conversation(conversation: ConversationCreate):
    """Create a new conversation"""
    try:
        conv = conversation_service.create_conversation(
            user_id=conversation.user_id,
            title=conversation.title
        )
        return ConversationResponse(
            id=conv.id,
            session_id=conv.session_id,
            title=conv.title,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            message_count=0
        )
    except Exception as e:
        logger.error(f"Error creating conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/{user_id}", response_model=List[ConversationResponse])
async def get_user_conversations(
    user_id: str, 
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Get conversations for a user"""
    try:
        conversations = conversation_service.get_user_conversations(user_id, limit, offset)
        return [
            ConversationResponse(
                id=conv.id,
                session_id=conv.session_id,
                title=conv.title,
                created_at=conv.created_at,
                updated_at=conv.updated_at,
                message_count=len(conv.messages) if conv.messages else 0
            )
            for conv in conversations
        ]
    except Exception as e:
        logger.error(f"Error getting conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(conversation_id: int):
    """Get a specific conversation"""
    try:
        conv = conversation_service.get_conversation(conversation_id)
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return ConversationResponse(
            id=conv.id,
            session_id=conv.session_id,
            title=conv.title,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            message_count=len(conv.messages) if conv.messages else 0
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(conversation_id: int, update: ConversationUpdate):
    """Update conversation title"""
    try:
        conversation_service.update_conversation_title(conversation_id, update.title)
        conv = conversation_service.get_conversation(conversation_id)
        
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return ConversationResponse(
            id=conv.id,
            session_id=conv.session_id,
            title=conv.title,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            message_count=len(conv.messages) if conv.messages else 0
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{conversation_id}")
async def delete_conversation(conversation_id: int):
    """Delete a conversation"""
    try:
        conversation_service.delete_conversation(conversation_id)
        return {"status": "success", "message": "Conversation deleted"}
    except Exception as e:
        logger.error(f"Error deleting conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_conversation_messages(
    conversation_id: int, 
    limit: Optional[int] = Query(None, ge=1, le=1000)
):
    """Get messages from a conversation"""
    try:
        messages = conversation_service.get_conversation_history(conversation_id, limit)
        return [
            MessageResponse(
                id=msg.id,
                role=msg.role,
                content=msg.content,
                created_at=msg.created_at,
                context_used=msg.context_used,
                token_count=msg.token_count,
                processing_time=msg.processing_time
            )
            for msg in messages
        ]
    except Exception as e:
        logger.error(f"Error getting messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))