import pytest
import google.generativeai as genai
from unittest.mock import patch

from app.embeddings.embedder import (
    EmbeddingService,
    MissingAPIKeyError,
    GeminiAPIError
)

# Test vectors for similarity math validation
V_1 = [1.0, 0.0, 0.0]
V_SAME = [1.0, 0.0, 0.0]
V_OPPOSITE = [-1.0, 0.0, 0.0]
V_ORTHOGONAL = [0.0, 1.0, 0.0]
V_DIFFERENT = [1.0, 1.0, 0.0] # Cosine similarity should be 1/sqrt(2) approx 0.7071


def test_cosine_similarity_math():
    """Verify the mathematical correctness of cosine similarity calculations."""
    service = EmbeddingService(api_key="mock_key")
    
    # 1. Identical vectors -> 1.0
    assert pytest.approx(service.calculate_similarity(V_1, V_SAME)) == 1.0
    
    # 2. Opposite vectors -> -1.0
    assert pytest.approx(service.calculate_similarity(V_1, V_OPPOSITE)) == -1.0
    
    # 3. Orthogonal vectors -> 0.0
    assert pytest.approx(service.calculate_similarity(V_1, V_ORTHOGONAL)) == 0.0
    
    # 4. Known angle (45 degrees) -> cos(45) = 0.70710678
    assert pytest.approx(service.calculate_similarity(V_1, V_DIFFERENT)) == 0.70710678


def test_cosine_similarity_validation():
    """Verify input validation rules for similarity calculation."""
    service = EmbeddingService(api_key="mock_key")
    
    # Empty inputs
    with pytest.raises(ValueError, match="Input vectors cannot be empty"):
        service.calculate_similarity([], [1.0])
        
    # Dimension mismatch
    with pytest.raises(ValueError, match="Input vectors must have the same length"):
        service.calculate_similarity([1.0, 2.0], [1.0, 2.0, 3.0])
        
    # Zero norm vectors
    with pytest.raises(ValueError, match="Vectors must have non-zero norms"):
        service.calculate_similarity([0.0, 0.0], [1.0, 1.0])


def test_get_embedding_success():
    """Verify that get_embedding makes correct API calls and returns the embedding vector."""
    service = EmbeddingService(api_key="mock_key")
    
    mock_response = {"embedding": [0.15, 0.25, -0.35]}
    
    with patch.object(genai, "embed_content", return_value=mock_response) as mock_embed:
        vector = service.get_embedding("Hello recruiting world", task_type="semantic_similarity")
        
        assert vector == [0.15, 0.25, -0.35]
        mock_embed.assert_called_once_with(
            model="models/gemini-embedding-001",
            content="Hello recruiting world",
            task_type="semantic_similarity"
        )


def test_get_embedding_validation():
    """Verify get_embedding input validation."""
    service = EmbeddingService(api_key="mock_key")
    
    # Empty string
    with pytest.raises(ValueError, match="Input text cannot be empty or whitespace only"):
        service.get_embedding("   ")
        
    # None value
    with pytest.raises(ValueError, match="Input text cannot be empty or whitespace only"):
        service.get_embedding(None)


def test_get_embedding_missing_api_key():
    """Verify error raised when API key is missing."""
    service = EmbeddingService(api_key="")
    
    with pytest.raises(MissingAPIKeyError, match="Gemini API Key is missing"):
        service.get_embedding("Valid text")


def test_get_embedding_api_failure():
    """Verify exception wrapping when Gemini API calls fail."""
    service = EmbeddingService(api_key="mock_key")
    
    with patch.object(genai, "embed_content", side_effect=Exception("Network failure")):
        with pytest.raises(GeminiAPIError, match="Gemini embedding API call failed"):
            service.get_embedding("Valid text")


def test_get_embedding_invalid_response_format():
    """Verify error when API response is missing expected embedding structure."""
    service = EmbeddingService(api_key="mock_key")
    
    # Missing 'embedding' key
    mock_invalid_response = {"some_other_key": [1, 2, 3]}
    
    with patch.object(genai, "embed_content", return_value=mock_invalid_response):
        with pytest.raises(GeminiAPIError, match="Failed to retrieve 'embedding'"):
            service.get_embedding("Valid text")
