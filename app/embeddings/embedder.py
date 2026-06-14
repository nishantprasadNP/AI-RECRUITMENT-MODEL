import logging
import math
from typing import List, Optional
import google.generativeai as genai

from app.config import GEMINI_API_KEY

logger = logging.getLogger(__name__)

class EmbeddingError(Exception):
    """Base exception for all embedding-related errors."""
    pass

class MissingAPIKeyError(EmbeddingError):
    """Exception raised when GEMINI_API_KEY is not configured."""
    pass

class GeminiAPIError(EmbeddingError):
    """Exception raised when the Gemini API request fails."""
    pass

class EmbeddingService:
    """
    Service to interact with the Gemini embedding API and compute similarity scores.
    """
    def __init__(self, api_key: Optional[str] = None, model: str = "models/gemini-embedding-001"):
        self.api_key = api_key if api_key is not None else GEMINI_API_KEY
        self.model = model
        
    def get_embedding(self, text: str, task_type: Optional[str] = None) -> List[float]:
        """
        Generates a vector embedding for the given text.
        
        Args:
            text (str): The text to embed.
            task_type (str, optional): The task type for the embedding.
            
        Returns:
            List[float]: The embedding vector.
            
        Raises:
            ValueError: If the input text is empty or whitespace only.
            MissingAPIKeyError: If the Gemini API Key is missing.
            GeminiAPIError: If the Gemini API call fails.
        """
        if not text or not text.strip():
            logger.error("Embedding generation failed: empty text input.")
            raise ValueError("Input text cannot be empty or whitespace only.")
            
        if not self.api_key:
            logger.error("Embedding generation failed: missing GEMINI_API_KEY.")
            raise MissingAPIKeyError("Gemini API Key is missing. Please set the GEMINI_API_KEY environment variable.")
            
        try:
            genai.configure(api_key=self.api_key)
            kwargs = {
                "model": self.model,
                "content": text
            }
            if task_type:
                kwargs["task_type"] = task_type
                
            logger.info(f"Sending request to Gemini embedding API using model={self.model}")
            response = genai.embed_content(**kwargs)
            
            if "embedding" not in response:
                logger.error("Failed to retrieve 'embedding' from Gemini API response.")
                raise GeminiAPIError("Failed to retrieve 'embedding' from Gemini API response.")
                
            vector = response["embedding"]
            logger.info(f"Successfully generated embedding vector of dimension {len(vector)}")
            return vector
            
        except Exception as e:
            if isinstance(e, EmbeddingError):
                raise
            logger.error(f"Gemini embedding API call failed: {str(e)}")
            raise GeminiAPIError(f"Gemini embedding API call failed: {str(e)}") from e

    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Computes the Cosine Similarity between two embedding vectors.
        
        Args:
            embedding1 (List[float]): First vector.
            embedding2 (List[float]): Second vector.
            
        Returns:
            float: Cosine similarity score (between -1.0 and 1.0).
            
        Raises:
            ValueError: If vectors are empty, of different lengths, or one has zero norm.
        """
        if not embedding1 or not embedding2:
            logger.error("Similarity calculation failed: empty vector inputs.")
            raise ValueError("Input vectors cannot be empty.")
            
        if len(embedding1) != len(embedding2):
            logger.error(f"Similarity calculation failed: vector length mismatch ({len(embedding1)} vs {len(embedding2)}).")
            raise ValueError("Input vectors must have the same length.")
            
        dot_product = sum(x * y for x, y in zip(embedding1, embedding2))
        norm1 = math.sqrt(sum(x * x for x in embedding1))
        norm2 = math.sqrt(sum(x * x for x in embedding2))
        
        if norm1 == 0.0 or norm2 == 0.0:
            logger.error("Similarity calculation failed: one or both vectors have a norm of zero.")
            raise ValueError("Vectors must have non-zero norms.")
            
        similarity = dot_product / (norm1 * norm2)
        # Handle precision boundary issues
        similarity = max(-1.0, min(1.0, similarity))
        
        logger.info(f"Computed cosine similarity score: {similarity:.4f}")
        return similarity
