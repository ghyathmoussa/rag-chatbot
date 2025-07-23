import pytest
from unittest.mock import Mock, patch, MagicMock
from src.models.qdrant_model import QDrantModel


class TestQDrantModel:
    @pytest.fixture
    def mock_qdrant_client(self):
        with patch('src.models.qdrant_model.QdrantClient') as mock:
            yield mock
    
    @pytest.fixture
    def qdrant_model(self, mock_qdrant_client):
        return QDrantModel(collection_name="test_collection")
    
    def test_connect(self, qdrant_model, mock_qdrant_client):
        # Test connection initialization
        assert qdrant_model.client is not None
        mock_qdrant_client.assert_called_once()
    
    def test_store_embeddings(self, qdrant_model):
        # Mock the client methods
        qdrant_model.client.collection_exists = Mock(return_value=False)
        qdrant_model.client.create_collection = Mock()
        qdrant_model.client.upsert = Mock()
        
        embeddings = [[0.1, 0.2], [0.3, 0.4]]
        chunks = ["chunk1", "chunk2"]
        
        qdrant_model.store(embeddings, chunks)
        
        # Verify collection creation
        qdrant_model.client.collection_exists.assert_called_once_with("test_collection")
        qdrant_model.client.create_collection.assert_called_once()
        
        # Verify upsert was called
        qdrant_model.client.upsert.assert_called_once()
    
    def test_query(self, qdrant_model):
        # Mock search response
        mock_response = [
            Mock(payload={"text": "result1"}, score=0.9),
            Mock(payload={"text": "result2"}, score=0.8)
        ]
        qdrant_model.client.search = Mock(return_value=mock_response)
        
        query_embedding = [0.1, 0.2]
        results = qdrant_model.query(query_embedding, top_k=2)
        
        assert len(results) == 2
        assert results[0]["text"] == "result1"
        assert results[0]["score"] == 0.9
        
        qdrant_model.client.search.assert_called_once()
    
    def test_disconnect(self, qdrant_model):
        qdrant_model._disconnect()
        # In the current implementation, disconnect doesn't do anything
        # but we can test it doesn't raise errors
        assert True