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
import plotly.express as px
import plotly.graph_objects as go
from streamlit_extras.metric_cards import style_metric_cards
from streamlit_extras.colored_header import colored_header
import asyncio
import websockets
import threading

# API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
WS_BASE_URL = os.getenv("WS_BASE_URL", "ws://localhost:8000")
API_TIMEOUT = 30

# Page Configuration
st.set_page_config(
    page_title="RAG Chatbot Pro",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/your-repo/rag-chatbot',
        'Report a bug': "https://github.com/your-repo/rag-chatbot/issues",
        'About': "# RAG Chatbot Pro\nAn advanced conversational AI with document-based retrieval augmented generation."
    }
)

# Color Theme Configuration
THEME = {
    "primary": "#ff4b4b",  # Streamlit's default red
    "primary_dark": "#ff2b2b",
    "secondary": "#0066cc",  # Streamlit's default blue
    "secondary_dark": "#0052a3",
    "background": "#ffffff",
    "surface": "#ffffff",
    "text_primary": "#262730",
    "text_secondary": "#8e8ea0",
    "user_message_bg": "#f0f2f6",
    "user_message_border": "#d4d4d4",
    "user_message_text": "#262730",
    "assistant_message_bg": "#ffffff",
    "assistant_message_border": "#d4d4d4",
    "assistant_message_text": "#262730",
    "success": "#00d4aa",  # Streamlit's default success
    "error": "#ff4b4b",   # Streamlit's default error
    "warning": "#ffa421", # Streamlit's default warning
    "info": "#0066cc"     # Streamlit's default info
}

# Enhanced Custom CSS
st.markdown("""
<style>
    
    /* Main theme styling */
    .main {
        background-color: #fafbfc;
    }
    
    /* Override Streamlit's default primary color */
    .css-1y4p8pa {
        background-color: #ffffff;
    }
    
    /* Tab content background */
    .css-1v0mbdj > div {
        background-color: #ffffff;
        border-radius: 0.5rem;
        padding: 1rem;
    }
    
    
    /* Enhanced chat message styling */
    .chat-message {
        padding: 1.5rem;
        border-radius: 0.75rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        transition: all 0.3s ease;
    }
    
    .chat-message:hover {
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    .chat-message.user {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        color: #1565c0;
        margin-left: 20%;
        border: 1px solid #90caf9;
    }
    
    .chat-message.assistant {
        background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
        color: #374151;
        margin-right: 20%;
        border: 1px solid #d1d5db;
    }
    
    /* Context chunk styling */
    .context-chunk {
        background-color: #f0f2f6;
        border-left: 4px solid #ff4b4b;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0.5rem;
        font-size: 0.9rem;
        position: relative;
        overflow: hidden;
    }
    
    .context-chunk::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        width: 4px;
        height: 100%;
        background: linear-gradient(to bottom, #ff4b4b, #ff2b2b);
    }
    
    /* Metric card styling */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 0.75rem;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #f8fafb;
    }
    
    /* Button enhancements */
    .stButton > button {
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    /* Status indicator */
    .status-indicator {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 5px;
        animation: pulse 2s infinite;
    }
    
    .status-indicator.online {
        background-color: #28a745;
    }
    
    .status-indicator.offline {
        background-color: #dc3545;
    }
    
    @keyframes pulse {
        0% {
            box-shadow: 0 0 0 0 rgba(40, 167, 69, 0.4);
        }
        70% {
            box-shadow: 0 0 0 10px rgba(40, 167, 69, 0);
        }
        100% {
            box-shadow: 0 0 0 0 rgba(40, 167, 69, 0);
        }
    }
    
    /* Loading animation */
    .loading-dots {
        display: inline-block;
        width: 80px;
        height: 24px;
    }
    
    .loading-dots:after {
        content: ' .';
        animation: dots 1.5s steps(5, end) infinite;
    }
    
    @keyframes dots {
        0%, 20% {
            content: ' .';
        }
        40% {
            content: ' ..';
        }
        60% {
            content: ' ...';
        }
        80%, 100% {
            content: ' ';
        }
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        background-color: #f0f2f6;
        padding: 0.5rem;
        border-radius: 0.5rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 0.5rem;
        padding: 0.75rem 1.5rem;
        background-color: white;
        transition: all 0.3s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #e9ecef;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #007bff;
        color: white;
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

if 'api_status' not in st.session_state:
    st.session_state.api_status = 'checking'

if 'conversation_stats' not in st.session_state:
    st.session_state.conversation_stats = {}

if 'is_typing' not in st.session_state:
    st.session_state.is_typing = False

# Enhanced API Helper Functions
def check_api_status():
    """Check API connection status"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        st.session_state.api_status = 'online' if response.status_code == 200 else 'offline'
    except:
        st.session_state.api_status = 'offline'

def api_request(method: str, endpoint: str, **kwargs) -> Optional[Dict]:
    """Make API request with enhanced error handling"""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        response = requests.request(method, url, timeout=API_TIMEOUT, **kwargs)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to API server. Please check if the server is running.")
        return None
    except requests.exceptions.Timeout:
        st.error("⏱️ Request timed out. Please try again.")
        return None
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            st.error("🔍 Endpoint not found. Please check API configuration.")
        elif e.response.status_code == 500:
            st.error("💥 Server error. Please try again later.")
        else:
            st.error(f"❌ HTTP Error: {e.response.status_code}")
        return None
    except Exception as e:
        st.error(f"❌ Unexpected error: {str(e)}")
        return None

def fetch_conversations():
    """Fetch user conversations with enhanced stats"""
    data = api_request(
        "GET", 
        f"/api/conversations/user/{st.session_state.user_id}",
        params={"limit": 50}
    )
    if data:
        st.session_state.conversations = data
        # Calculate stats
        calculate_conversation_stats()

def calculate_conversation_stats():
    """Calculate conversation statistics"""
    total_messages = 0
    total_tokens = 0
    avg_response_time = 0
    response_times = []
    
    for conv in st.session_state.conversations:
        messages = conv.get('messages', [])
        total_messages += len(messages)
        
        for msg in messages:
            if msg.get('metrics'):
                metrics = msg['metrics']
                total_tokens += metrics.get('total_tokens', 0)
                if metrics.get('processing_time'):
                    response_times.append(metrics['processing_time'])
    
    if response_times:
        avg_response_time = sum(response_times) / len(response_times)
    
    st.session_state.conversation_stats = {
        'total_conversations': len(st.session_state.conversations),
        'total_messages': total_messages,
        'total_tokens': total_tokens,
        'avg_response_time': avg_response_time
    }

def create_conversation(title: str = "New Conversation"):
    """Create a new conversation with enhanced feedback"""
    with st.spinner("Creating new conversation..."):
        data = api_request(
            "POST",
            "/api/conversations",
            json={"user_id": st.session_state.user_id, "title": title}
        )
        if data:
            st.session_state.current_conversation_id = data['id']
            fetch_conversations()
            st.session_state.messages = []
            st.success("✅ New conversation created!")
            return data['id']

def fetch_messages(conversation_id: str):
    """Fetch messages with loading indicator"""
    with st.spinner("Loading messages..."):
        data = api_request(
            "GET",
            f"/api/conversations/{conversation_id}/messages"
        )
        if data:
            st.session_state.messages = data.get('messages', [])

def send_message(conversation_id: str, message: str):
    """Send a message with typing indicator"""
    st.session_state.is_typing = True
    response = api_request(
        "POST",
        f"/api/chat/{conversation_id}/message",
        json={"message": message}
    )
    st.session_state.is_typing = False
    return response

def upload_document(conversation_id: str, file):
    """Upload a document with progress"""
    progress_bar = st.progress(0)
    
    try:
        # Simulate progress (since we can't track actual upload progress)
        for i in range(0, 100, 20):
            progress_bar.progress(i)
            time.sleep(0.1)
        
        files = {'file': (file.name, file.getvalue(), file.type)}
        result = api_request(
            "POST",
            f"/api/documents/{conversation_id}/upload",
            files=files
        )
        
        progress_bar.progress(100)
        time.sleep(0.5)
        progress_bar.empty()
        
        return result
    except Exception as e:
        progress_bar.empty()
        raise e

def delete_conversation(conversation_id: str):
    """Delete a conversation with confirmation"""
    if api_request("DELETE", f"/api/conversations/{conversation_id}"):
        fetch_conversations()
        if st.session_state.current_conversation_id == conversation_id:
            st.session_state.current_conversation_id = None
            st.session_state.messages = []
        st.success("🗑️ Conversation deleted")

def update_conversation_title(conversation_id: str, title: str):
    """Update conversation title"""
    api_request(
        "PUT",
        f"/api/conversations/{conversation_id}",
        json={"title": title}
    )
    fetch_conversations()

def format_timestamp(timestamp_str: str) -> str:
    """Format timestamp for display"""
    try:
        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        now = datetime.now(timestamp.tzinfo)
        diff = now - timestamp
        
        if diff.days > 7:
            return timestamp.strftime('%Y-%m-%d')
        elif diff.days > 0:
            return f"{diff.days}d ago"
        elif diff.seconds > 3600:
            return f"{diff.seconds // 3600}h ago"
        elif diff.seconds > 60:
            return f"{diff.seconds // 60}m ago"
        else:
            return "just now"
    except:
        return timestamp_str

# Sidebar with enhanced features
with st.sidebar:
    # Header with status indicator
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("🤖 RAG Chatbot Pro")
    with col2:
        check_api_status()
        status_color = "green" if st.session_state.api_status == 'online' else "red"
        st.markdown(
            f'<span class="status-indicator {st.session_state.api_status}"></span>',
            unsafe_allow_html=True
        )
    
    # User info with avatar
    st.markdown(f"""
    <div style='background-color: white; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem;'>
        <div style='display: flex; align-items: center;'>
            <div style='width: 40px; height: 40px; background: linear-gradient(135deg, #ff4b4b 0%, #ff2b2b 100%); 
                        border-radius: 50%; margin-right: 1rem;'></div>
            <div>
                <strong>User ID</strong><br/>
                <code>{st.session_state.user_id}</code>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Quick actions
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ New Chat", use_container_width=True, type="primary"):
            create_conversation()
            st.rerun()
    with col2:
        if st.button("🔄 Refresh", use_container_width=True):
            fetch_conversations()
            st.rerun()
    
    # Conversations list with tabs
    tab1, tab2 = st.tabs(["💬 Active", "📊 Analytics"])
    
    with tab1:
        # Search conversations
        search_query = st.text_input("🔍 Search conversations", placeholder="Type to search...")
        
        if not st.session_state.conversations:
            fetch_conversations()
        
        # Filter conversations
        filtered_convs = st.session_state.conversations
        if search_query:
            filtered_convs = [c for c in filtered_convs if search_query.lower() in c['title'].lower()]
        
        # Display conversations
        for conv in filtered_convs:
            # Calculate message count for this conversation
            msg_count = len(conv.get('messages', []))
            last_updated = format_timestamp(conv.get('updated_at', conv.get('created_at', '')))
            
            # Conversation card
            with st.container():
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    is_active = conv['id'] == st.session_state.current_conversation_id
                    button_type = "primary" if is_active else "secondary"
                    
                    if st.button(
                        f"💬 {conv['title']}\n{msg_count} messages • {last_updated}", 
                        key=f"conv_{conv['id']}", 
                        use_container_width=True,
                        type=button_type
                    ):
                        st.session_state.current_conversation_id = conv['id']
                        fetch_messages(conv['id'])
                        st.rerun()
                
                with col2:
                    if st.button("🗑️", key=f"del_{conv['id']}", help="Delete conversation"):
                        if st.checkbox(f"Confirm delete", key=f"confirm_del_{conv['id']}"):
                            delete_conversation(conv['id'])
                            st.rerun()
                            
                st.markdown("---")
    
    with tab2:
        # Analytics dashboard
        if st.session_state.conversation_stats:
            stats = st.session_state.conversation_stats
            
            # Metrics
            st.metric("Total Conversations", stats['total_conversations'])
            st.metric("Total Messages", stats['total_messages'])
            st.metric("Total Tokens Used", f"{stats['total_tokens']:,}")
            st.metric("Avg Response Time", f"{stats['avg_response_time']:.2f}s")
            
            # Charts
            if st.session_state.conversations:
                # Messages over time
                dates = []
                for conv in st.session_state.conversations:
                    for msg in conv.get('messages', []):
                        if 'created_at' in msg:
                            dates.append(datetime.fromisoformat(msg['created_at'].replace('Z', '+00:00')).date())
                
                if dates:
                    df = pd.DataFrame(dates, columns=['date'])
                    daily_counts = df.groupby('date').size().reset_index(name='count')
                    
                    fig = px.line(daily_counts, x='date', y='count', 
                                  title='Messages per Day',
                                  labels={'count': 'Messages', 'date': 'Date'})
                    fig.update_layout(height=300)
                    st.plotly_chart(fig, use_container_width=True)
    
    # Document management section
    st.divider()
    with st.expander("📄 Document Management", expanded=False):
        if st.session_state.current_conversation_id:
            # Upload section
            st.subheader("Upload Documents")
            
            uploaded_files = st.file_uploader(
                "Choose files",
                type=['txt', 'md', 'pdf', 'doc', 'docx', 'csv', 'json'],
                accept_multiple_files=True,
                key="doc_uploader"
            )
            
            if uploaded_files:
                for uploaded_file in uploaded_files:
                    if uploaded_file.name not in st.session_state.uploaded_files:
                        result = upload_document(st.session_state.current_conversation_id, uploaded_file)
                        if result:
                            st.session_state.uploaded_files.append(uploaded_file.name)
                            st.success(f"✅ {uploaded_file.name} uploaded!")
            
            # List uploaded files
            if st.session_state.uploaded_files:
                st.subheader("Uploaded Files")
                for file in st.session_state.uploaded_files:
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.text(f"📎 {file}")
                    with col2:
                        if st.button("❌", key=f"remove_{file}", help="Remove file"):
                            st.session_state.uploaded_files.remove(file)
                            st.rerun()
                
                if st.button("🗑️ Clear All Documents", type="secondary", use_container_width=True):
                    if api_request("DELETE", f"/api/documents/{st.session_state.current_conversation_id}"):
                        st.session_state.uploaded_files = []
                        st.success("All documents cleared!")
                        st.rerun()
        else:
            st.info("Select a conversation to manage documents")
    
    # Settings section
    st.divider()
    with st.expander("⚙️ Settings", expanded=False):
        # API Configuration
        st.subheader("API Configuration")
        new_api_url = st.text_input("API URL", value=API_BASE_URL)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Test Connection", use_container_width=True):
                with st.spinner("Testing..."):
                    health = api_request("GET", "/health")
                    if health:
                        st.success(f"✅ Connected! v{health.get('version', 'unknown')}")
                    else:
                        st.error("❌ Connection failed")
        
        with col2:
            if st.button("Save Settings", use_container_width=True):
                os.environ["API_BASE_URL"] = new_api_url
                st.success("Settings saved!")
                st.rerun()
        
        # Theme settings
        st.subheader("Appearance")
        theme = st.selectbox("Theme", ["Light", "Dark", "Auto"])
        
        # Export/Import
        st.subheader("Data Management")
        if st.button("📥 Export Conversations", use_container_width=True):
            # Create export data
            export_data = {
                'user_id': st.session_state.user_id,
                'conversations': st.session_state.conversations,
                'exported_at': datetime.now().isoformat()
            }
            st.download_button(
                label="Download JSON",
                data=json.dumps(export_data, indent=2),
                file_name=f"rag_chatbot_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

# Main chat area
if st.session_state.current_conversation_id:
    # Get current conversation
    current_conv = next(
        (c for c in st.session_state.conversations if c['id'] == st.session_state.current_conversation_id),
        None
    )
    
    if current_conv:
        # Enhanced header
        colored_header(
            label=current_conv['title'],
            description=f"Created {format_timestamp(current_conv.get('created_at', ''))}",
            color_name="blue-70"
        )
        
        # Title editing with inline save
        with st.expander("✏️ Edit Title", expanded=False):
            col1, col2 = st.columns([4, 1])
            with col1:
                new_title = st.text_input(
                    "Conversation Title",
                    value=current_conv['title'],
                    key=f"title_{st.session_state.current_conversation_id}",
                    label_visibility="collapsed"
                )
            with col2:
                if st.button("💾 Save", use_container_width=True):
                    update_conversation_title(st.session_state.current_conversation_id, new_title)
                    st.success("Title updated!")
                    st.rerun()
    
    # Messages display with enhanced styling
    messages_container = st.container()
    
    with messages_container:
        for i, message in enumerate(st.session_state.messages):
            with st.chat_message(message['role'], avatar="🧑" if message['role'] == 'user' else "🤖"):
                # Message content
                st.markdown(message['content'])
                
                # Message metadata
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    if 'created_at' in message:
                        st.caption(f"⏰ {format_timestamp(message['created_at'])}")
                
                with col2:
                    if message.get('metrics', {}).get('model'):
                        st.caption(f"🧠 {message['metrics']['model']}")
                
                with col3:
                    if message.get('metrics', {}).get('total_tokens'):
                        st.caption(f"🎫 {message['metrics']['total_tokens']} tokens")
                
                # Context chunks with enhanced display
                if message.get('context_chunks'):
                    with st.expander(f"📚 View Context ({len(message['context_chunks'])} chunks used)"):
                        for j, chunk in enumerate(message['context_chunks']):
                            # Chunk header
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.markdown(f"**Source {j+1}**")
                            with col2:
                                score = chunk.get('score', 0)
                                score_color = "green" if score > 0.8 else "orange" if score > 0.6 else "red"
                                st.markdown(f"**Score:** :{score_color}[{score:.3f}]")
                            
                            # Chunk content
                            st.markdown(f"""
                            <div class="context-chunk">
                                {chunk['content'][:500]}{'...' if len(chunk['content']) > 500 else ''}
                            </div>
                            """, unsafe_allow_html=True)
                
                # Performance metrics
                if message.get('metrics') and message['role'] == 'assistant':
                    with st.expander("📊 Performance Metrics"):
                        metrics = message['metrics']
                        
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("Total Tokens", metrics.get('total_tokens', 'N/A'))
                        with col2:
                            st.metric("Response Time", f"{metrics.get('processing_time', 0):.2f}s")
                        with col3:
                            st.metric("Context Used", metrics.get('context_chunks_used', 0))
                        with col4:
                            st.metric("Prompt Tokens", metrics.get('prompt_tokens', 'N/A'))
    
    # Typing indicator
    if st.session_state.is_typing:
        with st.chat_message("assistant", avatar="🤖"):
            st.markdown('<div class="loading-dots">Thinking</div>', unsafe_allow_html=True)
    
    # Enhanced chat input
    col1, col2 = st.columns([6, 1])
    
    with col1:
        prompt = st.chat_input(
            "Type your message...",
            key="chat_input",
            disabled=st.session_state.is_typing
        )
    
    with col2:
        # Quick actions
        if st.button("🎙️", help="Voice input (coming soon)", disabled=True):
            pass
    
    if prompt:
        # Add user message
        user_message = {
            "role": "user",
            "content": prompt,
            "created_at": datetime.now().isoformat()
        }
        st.session_state.messages.append(user_message)
        
        # Send message
        with st.spinner("🤔 Thinking..."):
            response = send_message(st.session_state.current_conversation_id, prompt)
            
            if response:
                # Add assistant response
                assistant_message = {
                    "role": "assistant",
                    "content": response.get('response', ''),
                    "created_at": datetime.now().isoformat(),
                    "context_chunks": response.get('context_chunks', []),
                    "metrics": response.get('metrics', {})
                }
                st.session_state.messages.append(assistant_message)
                
                # Play notification sound (optional)
                st.balloons()
        
        st.rerun()
else:
    # Enhanced welcome screen
    st.markdown(
        """
        <div style='text-align: center; padding: 2rem;'>
            <h1 style='font-size: 3rem; background: linear-gradient(135deg, #ff4b4b 0%, #0066cc 100%); 
                       -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>
                🤖 Welcome to RAG Chatbot Pro
            </h1>
            <p style='font-size: 1.3rem; color: #666; margin-top: 1rem;'>
                Your intelligent assistant powered by advanced retrieval-augmented generation
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Feature cards
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3>🚀 Smart Conversations</h3>
            <p>Engage in context-aware discussions with advanced AI</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h3>📄 Document Intelligence</h3>
            <p>Upload documents to enhance AI knowledge and accuracy</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h3>📊 Real-time Analytics</h3>
            <p>Track performance metrics and conversation insights</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Quick stats dashboard
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    if st.session_state.conversation_stats:
        stats = st.session_state.conversation_stats
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Conversations", 
                stats['total_conversations'],
                delta=f"+{len([c for c in st.session_state.conversations if 'created_at' in c and datetime.fromisoformat(c['created_at'].replace('Z', '+00:00')).date() == datetime.now().date()])}"
            )
        
        with col2:
            st.metric(
                "Total Messages", 
                stats['total_messages']
            )
        
        with col3:
            st.metric(
                "Tokens Used", 
                f"{stats['total_tokens']:,}"
            )
        
        with col4:
            st.metric(
                "Avg Response Time", 
                f"{stats['avg_response_time']:.2f}s",
                delta="-0.1s" if stats['avg_response_time'] < 2 else "+0.1s"
            )
    
    # Call to action
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Start New Conversation", type="primary", use_container_width=True):
            create_conversation()
            st.rerun()

# Footer with enhanced styling
st.markdown("---")
st.markdown(
    f"""
    <div style='text-align: center; color: #666; padding: 2rem;'>
        <p>RAG Chatbot Pro v2.0 | Powered by Groq & Qdrant</p>
        <p style='font-size: 0.8rem; margin-top: 0.5rem;'>
            API Status: <span class="status-indicator {st.session_state.api_status}"></span> 
            {st.session_state.api_status.capitalize()}
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# JavaScript for enhanced interactivity
st.markdown("""
<script>
    // Auto-scroll to bottom of chat
    const scrollToBottom = () => {
        const messages = document.querySelector('[data-testid="stVerticalBlock"]');
        if (messages) {
            messages.scrollTop = messages.scrollHeight;
        }
    };
    
    // Call on load and after updates
    setTimeout(scrollToBottom, 100);
    
    // Enhanced keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        // Ctrl/Cmd + K for new conversation
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            // Trigger new conversation
        }
    });
</script>
""", unsafe_allow_html=True)