import pytest
from unittest.mock import Mock, patch
from src.models.embedding_model import Embedder


class TestEmbedder:
    @pytest.fixture
    def embedder(self):
        with patch('src.models.embedding_model.SentenceTransformer'):
            return Embedder()
    
    def test_chunk_text_basic(self, embedder):
        text = "This is a test sentence. Another sentence here."
        chunks = embedder.chunk_text(text, chunk_size=20, overlap=5)
        
        assert isinstance(chunks, list)
        assert len(chunks) > 0
        assert all(isinstance(chunk, str) for chunk in chunks)
    
    def test_chunk_text_empty(self, embedder):
        chunks = embedder.chunk_text("", chunk_size=100, overlap=10)
        assert chunks == []
    
    def test_chunk_text_overlap(self, embedder):
        text = "word1 word2 word3 word4 word5 word6"
        chunks = embedder.chunk_text(text, chunk_size=10, overlap=5)
        
        # Check that chunks have overlap
        if len(chunks) > 1:
            for i in range(len(chunks) - 1):
                assert chunks[i][-5:] in chunks[i+1]
    
    def test_embed_chunks(self, embedder):
        chunks = ["test chunk 1", "test chunk 2"]
        
        # Mock the model's encode method
        embedder.model.encode = Mock(return_value=[[0.1, 0.2], [0.3, 0.4]])
        
        embeddings = embedder.embed_chunks(chunks)
        
        assert len(embeddings) == 2
        assert embedder.model.encode.called
        assert embedder.model.encode.call_args[0][0] == chunks