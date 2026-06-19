import pytest
import numpy as np
from unittest.mock import patch
from app.matching.semantic_matcher import SemanticMatcher, SemanticMatchingError

def test_semantic_matcher_success_identical():
    """Verify that identical vectors produce a similarity score of 1.0."""
    matcher = SemanticMatcher()
    v1 = np.array([1.0, 2.0, 3.0])
    v2 = np.array([1.0, 2.0, 3.0])
    
    score = matcher.compute_similarity(v1, v2)
    assert score == 1.0


def test_semantic_matcher_success_orthogonal():
    """Verify that orthogonal vectors produce a similarity score of 0.0."""
    matcher = SemanticMatcher()
    v1 = np.array([1.0, 0.0, 0.0])
    v2 = np.array([0.0, 1.0, 0.0])
    
    score = matcher.compute_similarity(v1, v2)
    assert score == 0.0


def test_semantic_matcher_success_opposite():
    """Verify that opposite vectors produce a similarity score of 0.0 (clipped from -1.0)."""
    matcher = SemanticMatcher()
    v1 = np.array([1.0, 0.0, 0.0])
    v2 = np.array([-1.0, 0.0, 0.0])
    
    score = matcher.compute_similarity(v1, v2)
    assert score == 0.0


def test_semantic_matcher_success_similar():
    """Verify similar vectors (45 degrees angle) compute and round correctly."""
    matcher = SemanticMatcher()
    v1 = np.array([1.0, 0.0])
    v2 = np.array([1.0, 1.0]) # cos(45) = 1 / sqrt(2) approx 0.70710678
    
    score = matcher.compute_similarity(v1, v2)
    assert score == 0.7071


def test_semantic_matcher_list_inputs():
    """Verify that regular python lists are handled correctly."""
    matcher = SemanticMatcher()
    v1 = [1.0, 0.0]
    v2 = [1.0, 1.0]
    
    score = matcher.compute_similarity(v1, v2)
    assert score == 0.7071


def test_semantic_matcher_validation_none():
    """Verify ValueError is raised if either embedding is None."""
    matcher = SemanticMatcher()
    
    with pytest.raises(ValueError, match="resume_embedding cannot be None"):
        matcher.compute_similarity(None, [1.0, 2.0])
        
    with pytest.raises(ValueError, match="jd_embedding cannot be None"):
        matcher.compute_similarity([1.0, 2.0], None)


def test_semantic_matcher_validation_empty():
    """Verify ValueError is raised if either embedding is empty."""
    matcher = SemanticMatcher()
    
    with pytest.raises(ValueError, match="resume_embedding cannot be empty"):
        matcher.compute_similarity([], [1.0, 2.0])
        
    with pytest.raises(ValueError, match="jd_embedding cannot be empty"):
        matcher.compute_similarity([1.0, 2.0], [])


def test_semantic_matcher_validation_dimension_mismatch():
    """Verify ValueError is raised if vector dimensions mismatch."""
    matcher = SemanticMatcher()
    
    with pytest.raises(ValueError, match="Both embeddings must have the same dimension length"):
        matcher.compute_similarity([1.0, 2.0], [1.0, 2.0, 3.0])


def test_semantic_matcher_validation_not_1d():
    """Verify ValueError is raised if embeddings are not 1D vectors."""
    matcher = SemanticMatcher()
    v2d = np.array([[1.0, 2.0], [3.0, 4.0]])
    v1d = np.array([1.0, 2.0])
    
    with pytest.raises(ValueError, match="Both embeddings must be 1D vectors"):
        matcher.compute_similarity(v2d, v1d)


def test_semantic_matcher_internal_failure():
    """Verify SemanticMatchingError wraps internal sklearn exception."""
    matcher = SemanticMatcher()
    v1 = np.array([1.0, 2.0])
    v2 = np.array([1.0, 2.0])
    
    with patch("app.matching.semantic_matcher.cosine_similarity", side_effect=RuntimeError("Sklearn internal error")):
        with pytest.raises(SemanticMatchingError, match="Similarity calculation failed"):
            matcher.compute_similarity(v1, v2)
