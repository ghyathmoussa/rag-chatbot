from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
from sqlalchemy.orm import Session
from src.database.models import Conversation, Message, ContextChunk
from src.database.connection import db_manager
from src.utils.logger import logger


class ConversationService:
    def __init__(self):
        self.db_manager = db_manager
    
    def create_conversation(
        self, 
        user_id: Optional[str] = None,
        title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new conversation"""
        try:
            with self.db_manager.get_session() as session:
                conversation = Conversation(
                    session_id=str(uuid.uuid4()),
                    user_id=user_id,
                    title=title or "New Conversation",
                    meta_data=metadata or {}
                )
                session.add(conversation)
                session.commit()
                session.refresh(conversation)
                logger.info(f"Created new conversation: {conversation.session_id}")
                
                # Return extracted data
                return {
                    'id': conversation.id,
                    'session_id': conversation.session_id,
                    'title': conversation.title,
                    'created_at': conversation.created_at,
                    'updated_at': conversation.updated_at,
                    'message_count': 0
                }
        except Exception as e:
            logger.error(f"Failed to create conversation: {e}")
            raise
    
    def add_message(
        self,
        conversation_id: int,
        role: str,
        content: str,
        context_used: Optional[List[Dict[str, Any]]] = None,
        token_count: Optional[int] = None,
        model_used: Optional[str] = None,
        processing_time: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Message:
        """Add a message to a conversation"""
        try:
            with self.db_manager.get_session() as session:
                message = Message(
                    conversation_id=conversation_id,
                    role=role,
                    content=content,
                    context_used=context_used,
                    token_count=token_count,
                    model_used=model_used,
                    processing_time=processing_time,
                    meta_data=metadata or {}
                )
                session.add(message)
                
                # Update conversation's updated_at
                conversation = session.query(Conversation).filter_by(id=conversation_id).first()
                if conversation:
                    conversation.updated_at = datetime.utcnow()
                
                session.commit()
                session.refresh(message)
                logger.info(f"Added message to conversation {conversation_id}")
                return message
        except Exception as e:
            logger.error(f"Failed to add message: {e}")
            raise
    
    def save_context_chunks(
        self,
        message_id: int,
        context_chunks: List[Dict[str, Any]]
    ):
        """Save context chunks used for a message"""
        try:
            with self.db_manager.get_session() as session:
                for chunk in context_chunks:
                    context_chunk = ContextChunk(
                        message_id=message_id,
                        chunk_text=chunk.get('text', ''),
                        source_document=chunk.get('source', ''),
                        similarity_score=chunk.get('score', 0.0)
                    )
                    session.add(context_chunk)
                session.commit()
                logger.info(f"Saved {len(context_chunks)} context chunks for message {message_id}")
        except Exception as e:
            logger.error(f"Failed to save context chunks: {e}")
            raise
    
    def get_conversation(self, conversation_id: int) -> Optional[Dict[str, Any]]:
        """Get a conversation by ID"""
        try:
            with self.db_manager.get_session() as session:
                conversation = session.query(Conversation).filter_by(id=conversation_id).first()
                if not conversation:
                    return None
                    
                # Extract data within session context
                return {
                    'id': conversation.id,
                    'session_id': conversation.session_id,
                    'title': conversation.title,
                    'created_at': conversation.created_at,
                    'updated_at': conversation.updated_at,
                    'message_count': len(conversation.messages) if conversation.messages else 0
                }
        except Exception as e:
            logger.error(f"Failed to get conversation: {e}")
            return None
    
    def get_conversation_by_session_id(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get a conversation by session ID"""
        try:
            with self.db_manager.get_session() as session:
                conversation = session.query(Conversation).filter_by(session_id=session_id).first()
                if not conversation:
                    return None
                    
                # Extract data within session context
                return {
                    'id': conversation.id,
                    'session_id': conversation.session_id,
                    'title': conversation.title,
                    'created_at': conversation.created_at,
                    'updated_at': conversation.updated_at,
                    'message_count': len(conversation.messages) if conversation.messages else 0
                }
        except Exception as e:
            logger.error(f"Failed to get conversation by session ID: {e}")
            return None
    
    def get_conversation_history(
        self,
        conversation_id: int,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get messages from a conversation"""
        try:
            with self.db_manager.get_session() as session:
                query = session.query(Message).filter_by(
                    conversation_id=conversation_id
                ).order_by(Message.created_at)
                
                if limit:
                    # Get the latest N messages
                    query = query.order_by(Message.created_at.desc()).limit(limit)
                    messages = query.all()
                    # Reverse to maintain chronological order
                    messages.reverse()
                else:
                    messages = query.all()
                
                # Extract data within session context
                result = []
                for msg in messages:
                    result.append({
                        'id': msg.id,
                        'role': msg.role,
                        'content': msg.content,
                        'created_at': msg.created_at,
                        'context_used': msg.context_used,
                        'token_count': msg.token_count,
                        'processing_time': msg.processing_time,
                        'model_used': msg.model_used,
                        'meta_data': msg.meta_data
                    })
                return result
        except Exception as e:
            logger.error(f"Failed to get conversation history: {e}")
            return []
    
    def get_user_conversations(
        self,
        user_id: str,
        limit: Optional[int] = 10,
        offset: Optional[int] = 0
    ) -> List[Dict[str, Any]]:
        """Get conversations for a user"""
        try:
            with self.db_manager.get_session() as session:
                conversations = session.query(Conversation).filter_by(
                    user_id=user_id
                ).order_by(
                    Conversation.updated_at.desc()
                ).limit(limit).offset(offset).all()
                
                # Extract data within session context
                result = []
                for conv in conversations:
                    result.append({
                        'id': conv.id,
                        'session_id': conv.session_id,
                        'title': conv.title,
                        'created_at': conv.created_at,
                        'updated_at': conv.updated_at,
                        'message_count': len(conv.messages) if conv.messages else 0
                    })
                return result
        except Exception as e:
            logger.error(f"Failed to get user conversations: {e}")
            return []
    
    def update_conversation_title(self, conversation_id: int, title: str):
        """Update conversation title"""
        try:
            with self.db_manager.get_session() as session:
                conversation = session.query(Conversation).filter_by(id=conversation_id).first()
                if conversation:
                    conversation.title = title
                    conversation.updated_at = datetime.utcnow()
                    session.commit()
                    logger.info(f"Updated conversation {conversation_id} title")
        except Exception as e:
            logger.error(f"Failed to update conversation title: {e}")
            raise
    
    def delete_conversation(self, conversation_id: int):
        """Delete a conversation and all its messages"""
        try:
            with self.db_manager.get_session() as session:
                conversation = session.query(Conversation).filter_by(id=conversation_id).first()
                if conversation:
                    session.delete(conversation)
                    session.commit()
                    logger.info(f"Deleted conversation {conversation_id}")
        except Exception as e:
            logger.error(f"Failed to delete conversation: {e}")
            raise


# Global conversation service instance
conversation_service = ConversationService()