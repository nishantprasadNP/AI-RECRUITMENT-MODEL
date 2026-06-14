import logging
import numpy as np
from sentence_transformers import SentenceTransformer

# Setup logger
logger = logging.getLogger(__name__)

class EmbeddingGenerationError(Exception):
    """
    Custom exception raised when embedding generation fails.
    """
    pass

class EmbeddingGenerator:
    """
    Generates semantic vector embeddings for text using the all-mpnet-base-v2 model locally.
    """
    def __init__(self, model_name: str = "sentence-transformers/all-mpnet-base-v2"):
        """
        Initializes the EmbeddingGenerator and loads the SentenceTransformer model once.

        Args:
            model_name (str): HuggingFace model path. Defaults to 'sentence-transformers/all-mpnet-base-v2'.

        Raises:
            EmbeddingGenerationError: If the model fails to load.
        """
        logger.info(f"Initializing EmbeddingGenerator with model: {model_name}")
        try:
            self.model = SentenceTransformer(model_name)
            logger.info("SentenceTransformer model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load SentenceTransformer model '{model_name}': {str(e)}")
            raise EmbeddingGenerationError(f"Failed to load embedding model: {str(e)}") from e

    def generate_embedding(self, text: str) -> np.ndarray:
        """
        Generates a 768-dimensional embedding vector for the provided text.

        Args:
            text (str): The text string to embed.

        Returns:
            np.ndarray: The resulting embedding vector as a NumPy array.

        Raises:
            ValueError: If the input text is None, empty, or whitespace-only.
            EmbeddingGenerationError: If the embedding generation process fails.
        """
        # Validate input
        if text is None:
            logger.error("Embedding generation failed: Input text is None.")
            raise ValueError("Input text cannot be None.")
            
        if not isinstance(text, str) or not text.strip():
            logger.error("Embedding generation failed: Input text is empty or not a string.")
            raise ValueError("Input text cannot be empty or whitespace only.")

        try:
            logger.info("Generating embedding vector...")
            embedding = self.model.encode(text)
            
            # Ensure return type is a numpy.ndarray
            if not isinstance(embedding, np.ndarray):
                logger.debug("Converting output to numpy ndarray.")
                embedding = np.array(embedding)
                
            logger.info(f"Successfully generated embedding vector of shape {embedding.shape}")
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {str(e)}")
            raise EmbeddingGenerationError(f"Failed to generate embedding: {str(e)}") from e
