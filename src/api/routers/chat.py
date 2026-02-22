from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from typing import Dict
import json
import asyncio
from datetime import datetime

from src.models.groq_model import GroqModel
from src.api.schemas import MessageRequest, MessageResponse
from src.database.conversation_service import conversation_service
from src.utils.logger import logger

router = APIRouter(
    prefix="/api/chat",
    tags=["chat"]
)


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, conversation_id: int):
        await websocket.accept()
        self.active_connections[conversation_id] = websocket
        logger.info(f"WebSocket connected for conversation {conversation_id}")
    
    def disconnect(self, conversation_id: int):
        if conversation_id in self.active_connections:
            del self.active_connections[conversation_id]
            logger.info(f"WebSocket disconnected for conversation {conversation_id}")
    
    async def send_message(self, message: str, conversation_id: int):
        if conversation_id in self.active_connections:
            await self.active_connections[conversation_id].send_text(message)
    
    async def send_json(self, data: dict, conversation_id: int):
        if conversation_id in self.active_connections:
            await self.active_connections[conversation_id].send_json(data)


manager = ConnectionManager()


@router.post("/{conversation_id}/message", response_model=MessageResponse)
async def send_message(conversation_id: int, request: MessageRequest):
    """Send a message and get response (REST endpoint)"""
    try:
        # Initialize model with conversation
        groq_model = GroqModel(conversation_id=conversation_id)
        
        # Get response
        response = await asyncio.to_thread(
            groq_model.query_with_context,
            request.message
        )
        
        # Get the saved assistant message
        logger.info("Getting conversation history...")
        # Get more messages to ensure we get the new one
        messages = conversation_service.get_conversation_history(conversation_id, limit=10)
        logger.info(f"Retrieved {len(messages)} messages")

        if messages:
            # Find the most recent assistant message (the one we just created)
            # Iterate in normal order (newest first)
            assistant_msg = None
            for msg in messages:
                if msg.get('role') == 'assistant':
                    assistant_msg = msg
                    # Get the first (most recent) assistant message and stop
                    break
            
            if assistant_msg:
                logger.info(f"Returning message: role={assistant_msg.get('role')}, id={assistant_msg.get('id')}")
                return MessageResponse(
                    id=assistant_msg['id'],
                    role=assistant_msg['role'],
                    content=assistant_msg['content'],
                    created_at=assistant_msg['created_at'],
                    context_used=assistant_msg['context_used'],
                    token_count=assistant_msg['token_count'],
                    processing_time=assistant_msg['processing_time']
                )
            else:
                raise HTTPException(status_code=500, detail="Failed to retrieve assistant message")
        else:
            raise HTTPException(status_code=500, detail="Failed to retrieve message")
            
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/ws/{conversation_id}")
async def websocket_endpoint(websocket: WebSocket, conversation_id: int):
    """WebSocket endpoint for real-time chat"""
    await manager.connect(websocket, conversation_id)
    groq_model = GroqModel(conversation_id=conversation_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            if message_data["type"] == "chat":
                user_message = message_data["message"]
                
                # Send typing indicator
                await manager.send_json({
                    "type": "typing",
                    "typing": True
                }, conversation_id)
                
                try:
                    # Get response from model (run in thread to avoid blocking)
                    response = await asyncio.to_thread(
                        groq_model.query_with_context,
                        user_message
                    )
                    
                    # Send response
                    await manager.send_json({
                        "type": "message",
                        "role": "assistant",
                        "content": response,
                        "timestamp": datetime.utcnow().isoformat()
                    }, conversation_id)
                    
                except Exception as e:
                    logger.error(f"Error generating response: {e}")
                    await manager.send_json({
                        "type": "error",
                        "message": "Failed to generate response"
                    }, conversation_id)
                
                finally:
                    # Stop typing indicator
                    await manager.send_json({
                        "type": "typing",
                        "typing": False
                    }, conversation_id)
            
            elif message_data["type"] == "ping":
                # Handle ping to keep connection alive
                await manager.send_json({
                    "type": "pong"
                }, conversation_id)
                
    except WebSocketDisconnect:
        manager.disconnect(conversation_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(conversation_id)