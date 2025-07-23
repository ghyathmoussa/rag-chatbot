import streamlit as st
import requests
import json
from datetime import datetime
import time
from typing import Dict, List, Optional
import pandas as pd
import os
from pathlib import Path
import uuid
import websocket
import threading
import queue

# API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
WS_BASE_URL = os.getenv("WS_BASE_URL", "ws://localhost:8000")
API_TIMEOUT = 30

# Page Configuration
st.set_page_config(
    page_title="RAG Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/your-repo/rag-chatbot',
        'Report a bug': "https://github.com/your-repo/rag-chatbot/issues",
        'About': "# RAG Chatbot\nA conversational AI with document-based retrieval augmented generation."
    }
)

# Custom CSS
st.markdown("""
<style>
    .stChat {
        height: 600px;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        align-items: flex-start;
    }
    .chat-message.user {
        background-color: #f0f2f6;
    }
    .chat-message.assistant {
        background-color: #e8f4f8;
    }
    .message-content {
        flex: 1;
        padding: 0 1rem;
    }
    .message-timestamp {
        font-size: 0.8rem;
        color: #666;
        margin-top: 0.5rem;
    }
    .context-chunk {
        background-color: #f8f9fa;
        border-left: 3px solid #007bff;
        padding: 0.5rem;
        margin: 0.5rem 0;
        font-size: 0.9rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }
    .typing-indicator {
        display: inline-block;
        animation: typing 1.4s infinite;
    }
    @keyframes typing {
        0%, 60%, 100% {
            opacity: 0.3;
        }
        30% {
            opacity: 1;
        }
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'user_id' not in st.session_state:
    st.session_state.user_id = st.query_params.get('user_id', f'user_{uuid.uuid4().hex[:8]}')

if 'conversations' not in st.session_state:
    st.session_state.conversations = []

if 'current_conversation_id' not in st.session_state:
    st.session_state.current_conversation_id = None

if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'uploaded_files' not in st.session_state:
    st.session_state.uploaded_files = []

if 'ws_connection' not in st.session_state:
    st.session_state.ws_connection = None

if 'ws_queue' not in st.session_state:
    st.session_state.ws_queue = queue.Queue()

if 'is_typing' not in st.session_state:
    st.session_state.is_typing = False

if 'use_websocket' not in st.session_state:
    st.session_state.use_websocket = True

# WebSocket Handler
class WebSocketHandler:
    def __init__(self, conversation_id: str, message_queue: queue.Queue):
        self.conversation_id = conversation_id
        self.message_queue = message_queue
        self.ws = None
        self.is_connected = False
        self.thread = None
        
    def connect(self):
        """Connect to WebSocket"""
        def on_message(ws, message):
            try:
                data = json.loads(message)
                self.message_queue.put(data)
            except json.JSONDecodeError:
                pass
        
        def on_error(ws, error):
            st.error(f"WebSocket error: {error}")
            self.is_connected = False
        
        def on_close(ws, close_status_code, close_msg):
            self.is_connected = False
        
        def on_open(ws):
            self.is_connected = True
        
        ws_url = f"{WS_BASE_URL}/api/chat/ws/{self.conversation_id}"
        self.ws = websocket.WebSocketApp(
            ws_url,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )
        
        self.thread = threading.Thread(target=self.ws.run_forever)
        self.thread.daemon = True
        self.thread.start()
        
        # Wait for connection
        timeout = 5
        start_time = time.time()
        while not self.is_connected and time.time() - start_time < timeout:
            time.sleep(0.1)
        
        return self.is_connected
    
    def send_message(self, message: str):
        """Send message through WebSocket"""
        if self.ws and self.is_connected:
            self.ws.send(json.dumps({
                "type": "message",
                "content": message
            }))
    
    def close(self):
        """Close WebSocket connection"""
        if self.ws:
            self.ws.close()

# API Helper Functions
def api_request(method: str, endpoint: str, **kwargs) -> Optional[Dict]:
    """Make API request with error handling"""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        response = requests.request(method, url, timeout=API_TIMEOUT, **kwargs)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {str(e)}")
        return None

def fetch_conversations():
    """Fetch user conversations from API"""
    data = api_request(
        "GET", 
        f"/api/conversations",
        params={"user_id": st.session_state.user_id, "limit": 50}
    )
    if data:
        st.session_state.conversations = data.get('conversations', [])

def create_conversation(title: str = "New Conversation"):
    """Create a new conversation"""
    data = api_request(
        "POST",
        "/api/conversations",
        json={"user_id": st.session_state.user_id, "title": title}
    )
    if data:
        st.session_state.current_conversation_id = data['id']
        fetch_conversations()
        st.session_state.messages = []
        # Close existing WebSocket
        if st.session_state.ws_connection:
            st.session_state.ws_connection.close()
            st.session_state.ws_connection = None
        return data['id']

def fetch_messages(conversation_id: str):
    """Fetch messages for a conversation"""
    data = api_request(
        "GET",
        f"/api/conversations/{conversation_id}/messages"
    )
    if data:
        st.session_state.messages = data.get('messages', [])

def send_message(conversation_id: str, message: str):
    """Send a message to the chat API"""
    return api_request(
        "POST",
        f"/api/chat/{conversation_id}/message",
        json={"message": message}
    )

def upload_document(conversation_id: str, file):
    """Upload a document to the conversation"""
    files = {'file': (file.name, file.getvalue(), file.type)}
    return api_request(
        "POST",
        f"/api/documents/{conversation_id}/upload",
        files=files
    )

def delete_conversation(conversation_id: str):
    """Delete a conversation"""
    if api_request("DELETE", f"/api/conversations/{conversation_id}"):
        fetch_conversations()
        if st.session_state.current_conversation_id == conversation_id:
            st.session_state.current_conversation_id = None
            st.session_state.messages = []
            # Close WebSocket
            if st.session_state.ws_connection:
                st.session_state.ws_connection.close()
                st.session_state.ws_connection = None

def update_conversation_title(conversation_id: str, title: str):
    """Update conversation title"""
    api_request(
        "PUT",
        f"/api/conversations/{conversation_id}",
        json={"title": title}
    )
    fetch_conversations()

def process_websocket_messages():
    """Process messages from WebSocket queue"""
    while not st.session_state.ws_queue.empty():
        try:
            data = st.session_state.ws_queue.get_nowait()
            
            if data.get('type') == 'typing':
                st.session_state.is_typing = data.get('is_typing', False)
            elif data.get('type') == 'message':
                # Add assistant message
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": data.get('content', ''),
                    "created_at": datetime.now().isoformat(),
                    "context_chunks": data.get('context_chunks', []),
                    "metrics": data.get('metrics', {})
                })
                st.session_state.is_typing = False
            elif data.get('type') == 'stream':
                # Handle streaming responses
                if st.session_state.messages and st.session_state.messages[-1]['role'] == 'assistant':
                    st.session_state.messages[-1]['content'] += data.get('content', '')
                else:
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": data.get('content', ''),
                        "created_at": datetime.now().isoformat()
                    })
        except queue.Empty:
            break

# Sidebar
with st.sidebar:
    st.title("🤖 RAG Chatbot")
    
    # User info
    st.markdown(f"**User ID:** `{st.session_state.user_id}`")
    
    # New conversation button
    if st.button("➕ New Conversation", use_container_width=True):
        create_conversation()
        st.rerun()
    
    # Conversations list
    st.subheader("Conversations")
    
    if not st.session_state.conversations:
        fetch_conversations()
    
    for conv in st.session_state.conversations:
        col1, col2 = st.columns([4, 1])
        
        with col1:
            if st.button(
                f"💬 {conv['title']}", 
                key=f"conv_{conv['id']}", 
                use_container_width=True,
                type="primary" if conv['id'] == st.session_state.current_conversation_id else "secondary"
            ):
                st.session_state.current_conversation_id = conv['id']
                fetch_messages(conv['id'])
                # Setup WebSocket for new conversation
                if st.session_state.ws_connection:
                    st.session_state.ws_connection.close()
                if st.session_state.use_websocket:
                    st.session_state.ws_connection = WebSocketHandler(conv['id'], st.session_state.ws_queue)
                    st.session_state.ws_connection.connect()
                st.rerun()
        
        with col2:
            if st.button("🗑️", key=f"del_{conv['id']}"):
                delete_conversation(conv['id'])
                st.rerun()
    
    # Document upload section
    st.divider()
    st.subheader("📄 Documents")
    
    if st.session_state.current_conversation_id:
        uploaded_file = st.file_uploader(
            "Upload document",
            type=['txt', 'md', 'pdf', 'doc', 'docx'],
            key="doc_uploader"
        )
        
        if uploaded_file:
            with st.spinner("Processing document..."):
                result = upload_document(st.session_state.current_conversation_id, uploaded_file)
                if result:
                    st.success("Document uploaded successfully!")
                    st.session_state.uploaded_files.append(uploaded_file.name)
        
        if st.session_state.uploaded_files:
            st.markdown("**Uploaded files:**")
            for file in st.session_state.uploaded_files:
                st.text(f"📎 {file}")
            
            if st.button("🗑️ Clear all documents"):
                if api_request("DELETE", f"/api/documents/{st.session_state.current_conversation_id}"):
                    st.session_state.uploaded_files = []
                    st.success("Documents cleared!")
                    st.rerun()
    else:
        st.info("Select a conversation to upload documents")
    
    # Settings
    st.divider()
    with st.expander("⚙️ Settings"):
        st.text_input("API URL", value=API_BASE_URL, key="api_url")
        st.checkbox("Use WebSocket", value=st.session_state.use_websocket, key="use_websocket")
        if st.button("Test Connection"):
            health = api_request("GET", "/health")
            if health:
                st.success(f"Connected! Status: {health.get('status', 'unknown')}")

# Main chat area
if st.session_state.current_conversation_id:
    # Process WebSocket messages if connected
    if st.session_state.ws_connection:
        process_websocket_messages()
    
    # Get current conversation
    current_conv = next(
        (c for c in st.session_state.conversations if c['id'] == st.session_state.current_conversation_id),
        None
    )
    
    if current_conv:
        # Title editing
        col1, col2 = st.columns([4, 1])
        with col1:
            new_title = st.text_input(
                "Conversation Title",
                value=current_conv['title'],
                key=f"title_{st.session_state.current_conversation_id}",
                label_visibility="collapsed"
            )
        with col2:
            if st.button("💾 Save"):
                update_conversation_title(st.session_state.current_conversation_id, new_title)
                st.success("Title updated!")
                st.rerun()
    
    # Messages display
    st.divider()
    
    # Create a container for messages
    messages_container = st.container()
    
    with messages_container:
        for message in st.session_state.messages:
            with st.chat_message(message['role']):
                st.write(message['content'])
                
                # Show timestamp
                if 'created_at' in message:
                    timestamp = datetime.fromisoformat(message['created_at'].replace('Z', '+00:00'))
                    st.caption(f"🕒 {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Show context chunks if available
                if message.get('context_chunks'):
                    with st.expander(f"📚 Context ({len(message['context_chunks'])} chunks)"):
                        for i, chunk in enumerate(message['context_chunks']):
                            st.markdown(f"**Chunk {i+1}** (Score: {chunk.get('score', 'N/A')})")
                            st.markdown(f"```\n{chunk['content']}\n```")
                
                # Show metrics if available
                if message.get('metrics'):
                    cols = st.columns(4)
                    metrics = message['metrics']
                    
                    with cols[0]:
                        st.metric("Tokens", metrics.get('total_tokens', 'N/A'))
                    with cols[1]:
                        st.metric("Processing Time", f"{metrics.get('processing_time', 0):.2f}s")
                    with cols[2]:
                        st.metric("Context Chunks", metrics.get('context_chunks_used', 0))
                    with cols[3]:
                        st.metric("Model", metrics.get('model', 'N/A'))
        
        # Show typing indicator
        if st.session_state.is_typing:
            with st.chat_message("assistant"):
                st.markdown(
                    '<div class="typing-indicator">🤖 Assistant is typing...</div>',
                    unsafe_allow_html=True
                )
    
    # Chat input
    if prompt := st.chat_input("Type your message..."):
        # Add user message to display
        st.session_state.messages.append({
            "role": "user",
            "content": prompt,
            "created_at": datetime.now().isoformat()
        })
        
        if st.session_state.use_websocket and st.session_state.ws_connection and st.session_state.ws_connection.is_connected:
            # Send via WebSocket
            st.session_state.ws_connection.send_message(prompt)
            st.session_state.is_typing = True
        else:
            # Send via REST API
            with st.spinner("Thinking..."):
                response = send_message(st.session_state.current_conversation_id, prompt)
                
                if response:
                    # Add assistant response
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response.get('response', ''),
                        "created_at": datetime.now().isoformat(),
                        "context_chunks": response.get('context_chunks', []),
                        "metrics": response.get('metrics', {})
                    })
        
        st.rerun()
else:
    # Welcome screen
    st.markdown(
        """
        <div style='text-align: center; padding: 4rem;'>
            <h1>🤖 Welcome to RAG Chatbot</h1>
            <p style='font-size: 1.2rem; color: #666;'>
                Create a new conversation or select an existing one to start chatting.
            </p>
            <p style='margin-top: 2rem;'>
                Upload documents to enhance the AI's knowledge base for more accurate responses.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Quick stats
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Conversations", len(st.session_state.conversations))
    
    with col2:
        total_messages = sum(len(conv.get('messages', [])) for conv in st.session_state.conversations)
        st.metric("Total Messages", total_messages)
    
    with col3:
        st.metric("Documents Uploaded", len(st.session_state.uploaded_files))

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        RAG Chatbot v1.0 | Powered by Groq & Qdrant | 
        <span style='color: {"green" if st.session_state.ws_connection and st.session_state.ws_connection.is_connected else "red"}'>
            {"🟢 WebSocket Connected" if st.session_state.ws_connection and st.session_state.ws_connection.is_connected else "🔴 WebSocket Disconnected"}
        </span>
    </div>
    """,
    unsafe_allow_html=True
)

# Auto-refresh for WebSocket messages
if st.session_state.ws_connection and st.session_state.ws_connection.is_connected:
    time.sleep(0.1)  # Small delay to check for new messages
    st.rerun()