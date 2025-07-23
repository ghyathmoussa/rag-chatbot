import pytest
from unittest.mock import Mock, patch, MagicMock
from src.models.groq_model import GroqModel


class TestGroqModel:
    @pytest.fixture
    def mock_groq_client(self):
        with patch('src.models.groq_model.Groq') as mock:
            yield mock
    
    @pytest.fixture
    def groq_model(self, mock_groq_client):
        with patch('src.models.groq_model.Embedder'), \
             patch('src.models.groq_model.QDrantModel'):
            return GroqModel()
    
    def test_grqo_chat(self, groq_model):
        # Mock the Groq client response
        mock_response = Mock()
        mock_response.choices = [
            Mock(message=Mock(content="Test response"))
        ]
        groq_model.client.chat.completions.create = Mock(return_value=mock_response)
        
        user_query = "Test query"
        context = ["context1", "context2"]
        
        response = groq_model.grqo_chat(user_query, context)
        
        assert response == "Test response"
        groq_model.client.chat.completions.create.assert_called_once()
        
        # Check the call arguments
        call_args = groq_model.client.chat.completions.create.call_args
        assert call_args[1]["model"] == "gemma2-9b-it"
        assert len(call_args[1]["messages"]) == 2  # system and user messages
    
    def test_grqo_chat_error_handling(self, groq_model):
        # Mock an error
        groq_model.client.chat.completions.create = Mock(
            side_effect=Exception("API Error")
        )
        
        response = groq_model.grqo_chat("query", [])
        
        assert response == "Sorry, I encountered an error while processing your request."
    
    def test_process_and_store(self, groq_model):
        # Mock document loader
        mock_loader = Mock()
        mock_loader.load = Mock(return_value=[
            Mock(page_content="Document content", metadata={})
        ])
        
        # Mock embedder and store
        groq_model.embedder.chunk_text = Mock(return_value=["chunk1", "chunk2"])
        groq_model.embedder.embed_chunks = Mock(return_value=[[0.1, 0.2], [0.3, 0.4]])
        groq_model.store.store = Mock()
        
        with patch('src.models.groq_model.TextLoader', return_value=mock_loader):
            groq_model.process_and_store("test.txt")
        
        # Verify the processing pipeline
        mock_loader.load.assert_called_once()
        groq_model.embedder.chunk_text.assert_called_once_with("Document content")
        groq_model.embedder.embed_chunks.assert_called_once_with(["chunk1", "chunk2"])
        groq_model.store.store.assert_called_once()