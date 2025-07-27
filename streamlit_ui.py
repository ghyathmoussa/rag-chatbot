import streamlit as st
import requests
import json
from datetime import datetime
import time
from typing import Dict, List, Optional, Tuple
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
    initial_sidebar_state="expanded"
)

# Minimal custom CSS - let Streamlit handle most styling
st.markdown("""
<style>
    /* Only essential styling */
    .stButton > button {
        width: 100%;
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

if 'uploaded_docs' not in st.session_state:
    st.session_state.uploaded_docs = {}

# API Helper Functions
def api_request(method: str, endpoint: str, **kwargs) -> Optional[Dict]:
    """Make API request with error handling"""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        response = requests.request(method, url, timeout=API_TIMEOUT, **kwargs)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to API server. Please ensure the server is running.")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {str(e)}")
        return None

def fetch_conversations():
    """Fetch user conversations"""
    data = api_request(
        "GET", 
        f"/api/conversations/user/{st.session_state.user_id}",
        params={"limit": 50}
    )
    if data:
        st.session_state.conversations = data

def create_conversation(title: str = None):
    """Create a new conversation"""
    if not title:
        title = f"Conversation {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    data = api_request(
        "POST",
        "/api/conversations",
        json={"user_id": st.session_state.user_id, "title": title}
    )
    if data:
        st.session_state.current_conversation_id = data['id']
        fetch_conversations()
        st.session_state.messages = []
        st.session_state.uploaded_docs[data['id']] = []
        return data['id']

def fetch_messages(conversation_id: str):
    """Fetch messages for a conversation"""
    data = api_request(
        "GET",
        f"/api/conversations/{conversation_id}/messages"
    )
    if data:
        # The API returns a list of messages directly
        st.session_state.messages = data if isinstance(data, list) else []
        # Debug: log what we received
        if st.session_state.messages:
            print(f"Fetched {len(st.session_state.messages)} messages for conversation {conversation_id}")
            for i, msg in enumerate(st.session_state.messages[:3]):  # Show first 3
                print(f"  Message {i}: {msg.get('role')} - {msg.get('content', '')[:50]}...")

def send_message(conversation_id: str, message: str):
    """Send a message and get response"""
    return api_request(
        "POST",
        f"/api/chat/{conversation_id}/message",
        json={"message": message}
    )

def upload_document(conversation_id: str, file):
    """Upload a document"""
    files = {'file': (file.name, file.getvalue(), file.type)}
    # Convert conversation_id to int if it's a string integer
    try:
        conv_id = int(conversation_id) if isinstance(conversation_id, str) else conversation_id
    except ValueError:
        st.error("Invalid conversation ID format")
        return None
    data = {'conversation_id': str(conv_id)}  # Form data needs string
    return api_request(
        "POST",
        "/api/documents/upload",
        files=files,
        data=data
    )

def delete_conversation(conversation_id: str):
    """Delete a conversation"""
    if api_request("DELETE", f"/api/conversations/{conversation_id}"):
        fetch_conversations()
        if st.session_state.current_conversation_id == conversation_id:
            st.session_state.current_conversation_id = None
            st.session_state.messages = []

# Sidebar
with st.sidebar:
    st.title("🤖 RAG Chatbot")
    st.caption(f"User: {st.session_state.user_id}")
    
    # New conversation button
    if st.button("➕ New Conversation", type="primary"):
        create_conversation()
        st.rerun()
    
    # Conversations list
    st.divider()
    st.subheader("Conversations")
    
    if not st.session_state.conversations:
        fetch_conversations()
    
    # Display conversations
    for conv in sorted(st.session_state.conversations, key=lambda x: x.get('updated_at', x.get('created_at', '')), reverse=True):
        col1, col2 = st.columns([5, 1])
        
        with col1:
            is_current = conv['id'] == st.session_state.current_conversation_id
            if st.button(
                f"{'▶ ' if is_current else '  '}{conv['title'][:30]}{'...' if len(conv['title']) > 30 else ''}", 
                key=f"conv_{conv['id']}",
                disabled=is_current
            ):
                st.session_state.current_conversation_id = conv['id']
                fetch_messages(conv['id'])
                st.rerun()
        
        with col2:
            if st.button("🗑", key=f"del_{conv['id']}", help="Delete conversation"):
                delete_conversation(conv['id'])
                st.rerun()
    
    # Document management
    if st.session_state.current_conversation_id:
        st.divider()
        st.subheader("📄 Documents")
        
        uploaded_file = st.file_uploader(
            "Upload document",
            type=['txt', 'md', 'pdf'],  # Text, markdown, and PDF files
            key="doc_upload",
            help="Supported formats: .txt, .md, .pdf"
        )
        
        if uploaded_file:
            # Create a unique key for this upload to prevent re-uploads
            upload_key = f"{uploaded_file.name}_{uploaded_file.size}"
            if 'last_uploaded' not in st.session_state:
                st.session_state.last_uploaded = set()
            
            # Only upload if we haven't just uploaded this file
            if upload_key not in st.session_state.last_uploaded:
                with st.spinner("Uploading..."):
                    if upload_document(st.session_state.current_conversation_id, uploaded_file):
                        if st.session_state.current_conversation_id not in st.session_state.uploaded_docs:
                            st.session_state.uploaded_docs[st.session_state.current_conversation_id] = []
                        st.session_state.uploaded_docs[st.session_state.current_conversation_id].append(uploaded_file.name)
                        st.session_state.last_uploaded.add(upload_key)
                        st.success("Document uploaded!")
                        # Don't rerun immediately - let the user see the success message
        
        # Clear last uploaded when switching conversations
        if 'prev_conversation_id' not in st.session_state:
            st.session_state.prev_conversation_id = None
        if st.session_state.prev_conversation_id != st.session_state.current_conversation_id:
            st.session_state.last_uploaded = set()
            st.session_state.prev_conversation_id = st.session_state.current_conversation_id
        
        # Show uploaded documents
        if st.session_state.current_conversation_id in st.session_state.uploaded_docs:
            docs = st.session_state.uploaded_docs[st.session_state.current_conversation_id]
            if docs:
                st.caption("Uploaded documents:")
                for doc in docs:
                    st.text(f"📎 {doc}")

# Main chat interface
if st.session_state.current_conversation_id:
    # Get current conversation
    current_conv = next(
        (c for c in st.session_state.conversations if c['id'] == st.session_state.current_conversation_id),
        None
    )
    
    if current_conv:
        st.title(f"💬 {current_conv['title']}")
        
        # Display messages
        for message in st.session_state.messages:
            with st.chat_message(message['role']):
                st.write(message['content'])
                
                # Show metadata in expander
                if message['role'] == 'assistant' and (message.get('context_chunks') or message.get('metrics')):
                    with st.expander("View details"):
                        # Metrics
                        if message.get('metrics'):
                            metrics = message['metrics']
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Tokens", metrics.get('total_tokens', 'N/A'))
                            with col2:
                                st.metric("Time", f"{metrics.get('processing_time', 0):.1f}s")
                            with col3:
                                st.metric("Model", metrics.get('model', 'N/A'))
                        
                        # Context
                        if message.get('context_chunks'):
                            st.caption(f"Used {len(message['context_chunks'])} context chunks:")
                            for i, chunk in enumerate(message['context_chunks'][:3]):  # Show first 3
                                st.markdown(f"**Chunk {i+1}** (relevance: {chunk.get('score', 0):.2f})")
                                with st.container():
                                    content = chunk.get('content', chunk.get('text', ''))
                                    if content:
                                        st.text(content[:200] + "..." if len(content) > 200 else content)
        
        # Chat input
        if prompt := st.chat_input("Type your message..."):
            # Add user message
            st.session_state.messages.append({
                "role": "user",
                "content": prompt
            })
            
            # Get response
            with st.chat_message("user"):
                st.write(prompt)
            
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = send_message(st.session_state.current_conversation_id, prompt)
                    
                    if response:
                        # Extract the content from the MessageResponse
                        assistant_msg = response.get('content', 'Sorry, I encountered an error.')
                        st.write(assistant_msg)
                        
                        # Prepare metrics
                        metrics = {
                            'total_tokens': response.get('token_count', 0),
                            'processing_time': response.get('processing_time', 0),
                            'model': 'groq'  # You might want to get this from the response
                        }
                        
                        # Add to messages
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": assistant_msg,
                            "context_chunks": response.get('context_used', []),
                            "metrics": metrics
                        })
            
            st.rerun()
else:
    # Welcome screen
    st.title("🤖 Welcome to RAG Chatbot")
    st.markdown("""
    This is an intelligent chatbot that uses Retrieval-Augmented Generation (RAG) to provide accurate, 
    context-aware responses based on your uploaded documents.
    
    ### Getting Started:
    1. Click **"➕ New Conversation"** in the sidebar to begin
    2. Upload relevant documents to enhance the AI's knowledge
    3. Start chatting!
    
    ### Features:
    - 📄 Document-based responses
    - 💬 Conversation history
    - 📊 Performance metrics
    - 🔍 Source attribution
    """)
    
    # Quick stats
    if st.session_state.conversations:
        st.divider()
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Conversations", len(st.session_state.conversations))
        
        with col2:
            total_messages = sum(len(conv.get('messages', [])) for conv in st.session_state.conversations)
            st.metric("Total Messages", total_messages)
        
        with col3:
            total_docs = sum(len(docs) for docs in st.session_state.uploaded_docs.values())
            st.metric("Documents Uploaded", total_docs)

# API connection status
with st.sidebar:
    st.divider()
    if st.button("🔄 Check API Connection"):
        with st.spinner("Checking..."):
            health = api_request("GET", "/health")
            if health:
                st.success(f"✅ Connected (v{health.get('version', 'unknown')})")
            else:
                st.error("❌ Connection failed")