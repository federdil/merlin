"""
Unit tests for embedding tool.
"""

import pytest
import numpy as np
from unittest.mock import patch, Mock
from app.agents.tools.embedding import (
    generate_embedding,
    generate_embeddings_batch,
    compute_similarity,
    get_embedding_dimension
)


class TestGenerateEmbedding:
    """Test generate_embedding function."""

    @patch('app.agents.tools.embedding.model')
    def test_generate_embedding_success(self, mock_model):
        """Test successful embedding generation."""
        # Mock the model's encode method
        mock_embedding = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
        mock_model.encode.return_value = [mock_embedding]
        
        text = "This is a test text for embedding generation."
        result = generate_embedding(text)
        
        assert isinstance(result, list)
        assert len(result) == 5
        assert result == [0.1, 0.2, 0.3, 0.4, 0.5]
        mock_model.encode.assert_called_once_with([text])

    @patch('app.agents.tools.embedding.model')
    def test_generate_embedding_empty_text(self, mock_model):
        """Test embedding generation with empty text."""
        mock_embedding = np.array([0.0, 0.0, 0.0])
        mock_model.encode.return_value = [mock_embedding]
        
        text = ""
        result = generate_embedding(text)
        
        assert isinstance(result, list)
        assert len(result) == 3
        mock_model.encode.assert_called_once_with([text])

    @patch('app.agents.tools.embedding.model')
    def test_generate_embedding_long_text(self, mock_model):
        """Test embedding generation with long text."""
        mock_embedding = np.array([0.1] * 384)  # Standard embedding dimension
        mock_model.encode.return_value = [mock_embedding]
        
        text = "This is a very long text " * 100  # Long text
        result = generate_embedding(text)
        
        assert isinstance(result, list)
        assert len(result) == 384
        mock_model.encode.assert_called_once_with([text])


class TestGenerateEmbeddingsBatch:
    """Test generate_embeddings_batch function."""

    @patch('app.agents.tools.embedding.model')
    def test_generate_embeddings_batch_success(self, mock_model):
        """Test successful batch embedding generation."""
        # Mock the model's encode method for batch processing
        mock_embeddings = [
            np.array([0.1, 0.2, 0.3]),
            np.array([0.4, 0.5, 0.6]),
            np.array([0.7, 0.8, 0.9])
        ]
        mock_model.encode.return_value = mock_embeddings
        
        texts = ["Text 1", "Text 2", "Text 3"]
        result = generate_embeddings_batch(texts)
        
        assert isinstance(result, list)
        assert len(result) == 3
        assert result[0] == [0.1, 0.2, 0.3]
        assert result[1] == [0.4, 0.5, 0.6]
        assert result[2] == [0.7, 0.8, 0.9]
        mock_model.encode.assert_called_once_with(texts)

    @patch('app.agents.tools.embedding.model')
    def test_generate_embeddings_batch_empty_list(self, mock_model):
        """Test batch embedding generation with empty list."""
        mock_model.encode.return_value = []
        
        texts = []
        result = generate_embeddings_batch(texts)
        
        assert isinstance(result, list)
        assert len(result) == 0
        mock_model.encode.assert_called_once_with(texts)

    @patch('app.agents.tools.embedding.model')
    def test_generate_embeddings_batch_single_text(self, mock_model):
        """Test batch embedding generation with single text."""
        mock_embedding = np.array([0.1, 0.2, 0.3])
        mock_model.encode.return_value = [mock_embedding]
        
        texts = ["Single text"]
        result = generate_embeddings_batch(texts)
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0] == [0.1, 0.2, 0.3]
        mock_model.encode.assert_called_once_with(texts)


class TestComputeSimilarity:
    """Test compute_similarity function."""

    def test_compute_similarity_identical_vectors(self):
        """Test similarity computation with identical vectors."""
        embedding1 = [1.0, 0.0, 0.0]
        embedding2 = [1.0, 0.0, 0.0]
        
        result = compute_similarity(embedding1, embedding2)
        
        assert abs(result - 1.0) < 1e-6  # Should be exactly 1.0

    def test_compute_similarity_orthogonal_vectors(self):
        """Test similarity computation with orthogonal vectors."""
        embedding1 = [1.0, 0.0, 0.0]
        embedding2 = [0.0, 1.0, 0.0]
        
        result = compute_similarity(embedding1, embedding2)
        
        assert abs(result - 0.0) < 1e-6  # Should be exactly 0.0

    def test_compute_similarity_opposite_vectors(self):
        """Test similarity computation with opposite vectors."""
        embedding1 = [1.0, 0.0, 0.0]
        embedding2 = [-1.0, 0.0, 0.0]
        
        result = compute_similarity(embedding1, embedding2)
        
        assert abs(result - (-1.0)) < 1e-6  # Should be exactly -1.0

    def test_compute_similarity_partial_similarity(self):
        """Test similarity computation with partial similarity."""
        embedding1 = [1.0, 1.0, 0.0]
        embedding2 = [1.0, 0.0, 0.0]
        
        result = compute_similarity(embedding1, embedding2)
        
        # Should be positive but less than 1.0
        assert 0.0 < result < 1.0

    def test_compute_similarity_zero_vectors(self):
        """Test similarity computation with zero vectors."""
        embedding1 = [0.0, 0.0, 0.0]
        embedding2 = [0.0, 0.0, 0.0]
        
        result = compute_similarity(embedding1, embedding2)
        
        assert result == 0.0

    def test_compute_similarity_different_dimensions(self):
        """Test similarity computation with different dimension vectors."""
        embedding1 = [1.0, 0.0, 0.0]
        embedding2 = [1.0, 0.0, 0.0, 0.0]  # Different dimension
        
        # This should still work as numpy handles broadcasting
        result = compute_similarity(embedding1, embedding2)
        
        assert isinstance(result, float)

    def test_compute_similarity_large_vectors(self):
        """Test similarity computation with large vectors."""
        embedding1 = [0.1] * 384
        embedding2 = [0.2] * 384
        
        result = compute_similarity(embedding1, embedding2)
        
        assert isinstance(result, float)
        assert -1.0 <= result <= 1.0


class TestGetEmbeddingDimension:
    """Test get_embedding_dimension function."""

    def test_get_embedding_dimension(self):
        """Test getting embedding dimension."""
        result = get_embedding_dimension()
        
        assert isinstance(result, int)
        assert result == 384  # all-MiniLM-L6-v2 dimension


class TestEmbeddingIntegration:
    """Integration tests for embedding functionality."""

    @patch('app.agents.tools.embedding.model')
    def test_end_to_end_embedding_workflow(self, mock_model):
        """Test complete embedding workflow."""
        # Mock the model
        mock_embedding = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
        mock_model.encode.return_value = [mock_embedding]
        
        # Generate embedding
        text = "Test text for embedding"
        embedding = generate_embedding(text)
        
        # Compute similarity with itself
        similarity = compute_similarity(embedding, embedding)
        
        # Should be identical (similarity = 1.0)
        assert abs(similarity - 1.0) < 1e-6

    @patch('app.agents.tools.embedding.model')
    def test_batch_vs_single_embedding_consistency(self, mock_model):
        """Test that batch and single embedding generation are consistent."""
        # Mock the model
        mock_embedding = np.array([0.1, 0.2, 0.3])
        mock_model.encode.return_value = [mock_embedding]
        
        text = "Test text"
        
        # Generate single embedding
        single_embedding = generate_embedding(text)
        
        # Reset mock for batch call
        mock_model.encode.return_value = [mock_embedding]
        
        # Generate batch embedding
        batch_embeddings = generate_embeddings_batch([text])
        
        # Should be identical
        assert single_embedding == batch_embeddings[0]
