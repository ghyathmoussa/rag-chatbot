# RAG Chatbot

A Retrieval-Augmented Generation (RAG) chatbot that allows you to chat with your documents using advanced AI models. Built with FastAPI, Streamlit, and Qdrant vector database.

## Features

- 📄 **Document Upload & Processing**: Support for PDF and text files with automatic text extraction
- 🤖 **AI-Powered Conversations**: Leverages Groq's LLM models for intelligent responses
- 🔍 **Semantic Search**: Uses Qdrant vector database for efficient document retrieval
- 💬 **Conversation Management**: Save, load, and manage multiple chat sessions
- 🎨 **Modern UI**: Clean Streamlit interface with real-time chat functionality
- 🗄️ **Persistent Storage**: PostgreSQL database for conversation history
- 🐳 **Docker Support**: Easy deployment with Docker and Docker Compose

## Tech Stack

- **Backend**: FastAPI, Python 3.11+
- **Frontend**: Streamlit
- **Vector Database**: Qdrant
- **LLM**: Groq API (Llama models)
- **Embeddings**: Sentence Transformers
- **Database**: PostgreSQL
- **Containerization**: Docker & Docker Compose

## Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose (for containerized deployment)
- Groq API key
- PostgreSQL (if running locally without Docker)

## Installation

### Local Development

1. Clone the repository:
```bash
git clone https://github.com/yourusername/rag-chatbot.git
cd rag-chatbot
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the root directory:
```env
GROQ_API_KEY=your_groq_api_key
DATABASE_URL=postgresql://user:password@localhost:5432/rag_chatbot
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

5. Initialize the database:
```bash
alembic upgrade head
```

6. Start the services:
```bash
# Start Qdrant (using Docker)
docker run -p 6333:6333 qdrant/qdrant

# Start the FastAPI backend
uvicorn src.api.app:app --reload --port 8000

# In another terminal, start the Streamlit frontend
streamlit run streamlit_ui.py
```

### Docker Deployment

1. Clone the repository and navigate to the project directory

2. Create a `.env` file with your configuration

3. Build and run with Docker Compose:
```bash
docker-compose up --build
```

The application will be available at:
- Streamlit UI: http://localhost:8501
- FastAPI backend: http://localhost:8000
- API documentation: http://localhost:8000/docs

## Usage

1. **Start a New Conversation**: Click "New Conversation" in the sidebar
2. **Upload Documents**: Use the document upload section to add PDFs or text files
3. **Chat**: Type your questions in the chat input - the bot will respond using information from your uploaded documents
4. **Manage Conversations**: Switch between conversations, rename them, or delete old ones from the sidebar

## Project Structure

```
rag-chatbot/
├── src/
│   ├── api/           # FastAPI application and routes
│   ├── configs/       # Configuration files
│   ├── controller/    # Business logic controllers
│   ├── database/      # Database models and services
│   ├── models/        # AI model integrations
│   └── utils/         # Utility functions
├── tests/             # Unit tests
├── data/              # Data storage directory
├── logs/              # Application logs
├── streamlit_ui.py    # Streamlit frontend
├── docker-compose.yml # Docker composition
├── requirements.txt   # Python dependencies
└── README.md         # This file
```

## API Endpoints

- `POST /api/chat` - Send a chat message
- `GET /api/conversations` - List all conversations
- `POST /api/conversations` - Create a new conversation
- `GET /api/conversations/{id}` - Get conversation details
- `DELETE /api/conversations/{id}` - Delete a conversation
- `POST /api/documents/upload` - Upload and process documents
- `GET /api/documents` - List uploaded documents

## Development

### Running Tests

```bash
# Run all tests
./run_tests.sh

# Run with coverage
pytest --cov=src tests/
```

### Code Quality

The project uses:
- Type hints throughout the codebase
- Comprehensive error handling and logging
- Modular architecture for easy extensibility

## Configuration

Key configuration options in `src/configs/configs.py`:
- Embedding model settings
- Groq model parameters
- Qdrant collection configuration
- Database connection settings

## Troubleshooting

### Common Issues

1. **Qdrant Connection Error**: Ensure Qdrant is running on the configured host and port
2. **Database Connection Error**: Check PostgreSQL is running and credentials are correct
3. **Groq API Error**: Verify your API key is valid and has sufficient credits
4. **Document Upload Issues**: Ensure the data directory has write permissions

### Logs

Check the logs directory for detailed error information:
- `logs/rag_chatbot.log` - General application logs
- `logs/error_rag_chatbot.log` - Error-specific logs

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Groq for providing the LLM API
- Qdrant for the vector database
- Streamlit for the UI framework
- The open-source community for various libraries used in this project