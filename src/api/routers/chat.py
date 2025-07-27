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


@router.post("/{conversation_id}/message")
async def send_message(conversation_id: int, request: MessageRequest):
    """Send a message and get response (REST endpoint)"""
    try:
        # Initialize model with conversation
        groq_model = GroqModel(conversation_id=conversation_id)
        
        # Store the context used for the response
        context_used = []
        
        # Get response - this will save both user and assistant messages to DB
        response_data = await asyncio.to_thread(
            groq_model.query_with_context,
            request.message
        )
        
        logger.info(f"Generated response: {response_data['content'][:100]}...")
        
        # Return the response directly
        return {
            "content": response_data["content"],
            "context_used": response_data.get("context_used", []),
            "token_count": response_data.get("token_count", 0),
            "processing_time": response_data.get("processing_time", 0)
        }
            
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
                    response_data = await asyncio.to_thread(
                        groq_model.query_with_context,
                        user_message
                    )
                    
                    # Send response
                    await manager.send_json({
                        "type": "message",
                        "role": "assistant",
                        "content": response_data["content"],
                        "timestamp": datetime.utcnow().isoformat(),
                        "context_used": response_data.get("context_used", []),
                        "token_count": response_data.get("token_count", 0),
                        "processing_time": response_data.get("processing_time", 0)
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