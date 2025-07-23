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

# API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
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

def update_conversation_title(conversation_id: str, title: str):
    """Update conversation title"""
    api_request(
        "PUT",
        f"/api/conversations/{conversation_id}",
        json={"title": title}
    )
    fetch_conversations()

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
        if st.button("Test Connection"):
            health = api_request("GET", "/health")
            if health:
                st.success(f"Connected! Status: {health.get('status', 'unknown')}")

# Main chat area
if st.session_state.current_conversation_id:
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
    
    # Chat input
    if prompt := st.chat_input("Type your message..."):
        # Add user message to display
        st.session_state.messages.append({
            "role": "user",
            "content": prompt,
            "created_at": datetime.now().isoformat()
        })
        
        # Send message to API
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
        RAG Chatbot v1.0 | Powered by Groq & Qdrant
    </div>
    """,
    unsafe_allow_html=True
)