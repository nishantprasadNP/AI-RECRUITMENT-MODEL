import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from app.embeddings.embedding_generator import EmbeddingGenerator, EmbeddingGenerationError

def test_embedding_generator_init_success():
    """Verify that SentenceTransformer is loaded on initialization."""
    with patch("app.embeddings.embedding_generator.SentenceTransformer") as mock_transformer:
        generator = EmbeddingGenerator()
        mock_transformer.assert_called_once_with("sentence-transformers/all-mpnet-base-v2")
        assert generator.model is not None

def test_embedding_generator_init_failure():
    """Verify that EmbeddingGenerationError is raised if SentenceTransformer fails to load."""
    with patch("app.embeddings.embedding_generator.SentenceTransformer", side_effect=Exception("Failed to load weights")):
        with pytest.raises(EmbeddingGenerationError, match="Failed to load embedding model"):
            EmbeddingGenerator()

def test_generate_embedding_success():
    """Verify that generate_embedding returns a numpy array."""
    mock_vector = np.array([0.1, 0.2, 0.3])
    with patch("app.embeddings.embedding_generator.SentenceTransformer") as mock_transformer:
        mock_instance = MagicMock()
        mock_instance.encode.return_value = mock_vector
        mock_transformer.return_value = mock_instance
        
        generator = EmbeddingGenerator()
        result = generator.generate_embedding("Test text input")
        
        assert isinstance(result, np.ndarray)
        assert np.array_equal(result, mock_vector)
        mock_instance.encode.assert_called_once_with("Test text input")

def test_generate_embedding_validation():
    """Verify ValueError is raised on invalid inputs."""
    with patch("app.embeddings.embedding_generator.SentenceTransformer"):
        generator = EmbeddingGenerator()
        
        with pytest.raises(ValueError, match="Input text cannot be None"):
            generator.generate_embedding(None)
            
        with pytest.raises(ValueError, match="Input text cannot be empty or whitespace only"):
            generator.generate_embedding("")
            
        with pytest.raises(ValueError, match="Input text cannot be empty or whitespace only"):
            generator.generate_embedding("   ")

def test_generate_embedding_failure():
    """Verify EmbeddingGenerationError is raised if encoding fails."""
    with patch("app.embeddings.embedding_generator.SentenceTransformer") as mock_transformer:
        mock_instance = MagicMock()
        mock_instance.encode.side_effect = Exception("Encoding service timed out")
        mock_transformer.return_value = mock_instance
        
        generator = EmbeddingGenerator()
        with pytest.raises(EmbeddingGenerationError, match="Failed to generate embedding"):
            generator.generate_embedding("Valid text")
