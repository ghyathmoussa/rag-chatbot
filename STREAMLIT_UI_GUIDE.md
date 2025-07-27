# RAG Chatbot Streamlit UI Guide

## Overview

This RAG Chatbot comes with multiple Streamlit UI options:

1. **streamlit_app.py** - Original UI with all features
2. **streamlit_app_v2.py** - Simplified, cleaner UI 
3. **streamlit_app_enhanced.py** - Advanced UI with analytics and enhanced features
4. **streamlit_app_ws.py** - WebSocket-enabled UI for real-time chat

## Running the Streamlit UI

### Option 1: Using Docker Compose (Recommended)

The Streamlit app is already configured in `docker-compose.yml`:

```bash
# Start all services including Streamlit
docker-compose up -d

# The Streamlit UI will be available at http://localhost:8501
```

### Option 2: Running Locally

1. First ensure the backend API is running:
```bash
# Start the backend services
docker-compose up -d qdrant postgres app
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run your preferred Streamlit app:
```bash
# Original version
streamlit run streamlit_app.py

# Simplified version
streamlit run streamlit_app_v2.py

# Enhanced version with analytics
streamlit run streamlit_app_enhanced.py

# WebSocket version
streamlit run streamlit_app_ws.py
```

## Features Comparison

### streamlit_app.py (Original)
- ✅ Conversation management
- ✅ Document upload
- ✅ Message history
- ✅ Context chunks display
- ✅ Basic metrics
- ✅ Settings panel

### streamlit_app_v2.py (Simplified)
- ✅ Clean, minimal interface
- ✅ Core chat functionality
- ✅ Document upload
- ✅ Conversation management
- ✅ Expandable details
- ✅ Better mobile experience

### streamlit_app_enhanced.py (Advanced)
- ✅ All original features
- ✅ Real-time status indicators
- ✅ Analytics dashboard
- ✅ Performance metrics
- ✅ Message search
- ✅ Export/Import conversations
- ✅ Enhanced UI with animations
- ✅ Plotly charts
- ✅ Theme customization

### streamlit_app_ws.py (WebSocket)
- ✅ Real-time messaging
- ✅ Live typing indicators
- ✅ Instant updates
- ✅ Better performance for long conversations

## Configuration

### Environment Variables

Create a `.env` file or set these environment variables:

```bash
# API Configuration
API_BASE_URL=http://localhost:8000
WS_BASE_URL=ws://localhost:8000  # For WebSocket version

# Optional: Override default settings
GROQ_API_KEY=your_groq_api_key
QDRANT_URL=http://localhost:6333
```

### Customization

Each UI version can be customized by editing the respective file:

1. **Styling**: Modify the CSS in the `st.markdown()` section
2. **Layout**: Adjust column widths and component placement
3. **Features**: Enable/disable features by commenting out sections

## Usage Guide

### Getting Started

1. **Create a Conversation**: Click "➕ New Conversation" in the sidebar
2. **Upload Documents**: Use the document upload section to add context
3. **Start Chatting**: Type your message in the chat input

### Managing Conversations

- **Switch Conversations**: Click on any conversation in the sidebar
- **Delete Conversations**: Click the 🗑️ button next to a conversation
- **Rename Conversations**: Edit the title in the main chat area (varies by version)

### Document Management

1. **Supported Formats**: txt, md, pdf, doc, docx, csv, json
2. **Upload Process**: 
   - Select a conversation first
   - Click "Browse files" in the sidebar
   - Select your document
3. **View Uploaded Docs**: Listed below the upload button

### Viewing Response Details

- **Context Chunks**: Shows which document sections were used
- **Metrics**: Token usage, response time, model info
- **Relevance Scores**: How relevant each chunk was to your query

## Troubleshooting

### Common Issues

1. **"Cannot connect to API server"**
   - Ensure the backend is running: `docker-compose ps`
   - Check API_BASE_URL is correct
   - Verify port 8000 is not blocked

2. **Document upload fails**
   - Check file size (default limit: 10MB)
   - Ensure file format is supported
   - Verify conversation is selected

3. **Slow responses**
   - Check if Groq API key is valid
   - Monitor Docker container logs
   - Ensure adequate system resources

### Debugging

View logs for troubleshooting:

```bash
# Streamlit logs
docker-compose logs -f streamlit

# Backend API logs
docker-compose logs -f app

# All services
docker-compose logs -f
```

## Performance Tips

1. **Use streamlit_app_v2.py** for better performance on slower connections
2. **Use streamlit_app_ws.py** for real-time chat experience
3. **Limit conversation history** to improve load times
4. **Clear old conversations** periodically

## Development

To modify the UI:

1. Edit the desired streamlit_app_*.py file
2. Changes reflect immediately (Streamlit auto-reloads)
3. For production, rebuild the Docker image:
   ```bash
   docker-compose build
   docker-compose up -d
   ```

## Security Notes

- User IDs are generated automatically
- No authentication is implemented by default
- Add authentication middleware for production use
- Documents are stored per conversation
- API endpoints should be secured in production