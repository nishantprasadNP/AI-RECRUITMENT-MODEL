import logging
from typing import Union, List
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Setup logger
logger = logging.getLogger(__name__)


class SemanticMatchingError(Exception):
    """
    Custom exception raised when similarity computation fails.
    """
    pass


class SemanticMatcher:
    """
    Computes semantic similarity scores between candidate resumes and job descriptions.
    """

    def compute_similarity(
        self,
        resume_embedding: Union[np.ndarray, List[float]],
        jd_embedding: Union[np.ndarray, List[float]],
    ) -> float:
        """
        Computes the Cosine Similarity between a resume embedding and a job description embedding.

        Args:
            resume_embedding (np.ndarray or list): The vector embedding of the candidate resume.
            jd_embedding (np.ndarray or list): The vector embedding of the job description.

        Returns:
            float: Cosine similarity score bounded between 0.0 and 1.0, rounded to 4 decimal places.

        Raises:
            ValueError: If either embedding is None, empty, or has incompatible shapes.
            SemanticMatchingError: If the similarity score computation fails.
        """
        # 1. Validate inputs cannot be None
        if resume_embedding is None:
            logger.error("Similarity computation failed: resume_embedding is None.")
            raise ValueError("resume_embedding cannot be None.")

        if jd_embedding is None:
            logger.error("Similarity computation failed: jd_embedding is None.")
            raise ValueError("jd_embedding cannot be None.")

        # Convert to numpy arrays for validation and computation
        try:
            r_arr = np.asarray(resume_embedding, dtype=float)
            j_arr = np.asarray(jd_embedding, dtype=float)
        except Exception as e:
            logger.error(f"Failed to convert inputs to numpy float arrays: {str(e)}")
            raise ValueError(f"Embeddings must be numerical arrays or lists: {str(e)}") from e

        # 2. Validate inputs cannot be empty
        if r_arr.size == 0:
            logger.error("Similarity computation failed: resume_embedding is empty.")
            raise ValueError("resume_embedding cannot be empty.")

        if j_arr.size == 0:
            logger.error("Similarity computation failed: jd_embedding is empty.")
            raise ValueError("jd_embedding cannot be empty.")

        # Ensure they are 1D arrays or check dimension compatibility
        if r_arr.ndim != 1 or j_arr.ndim != 1:
            logger.error(f"Embeddings must be 1D vectors, got dimensions: resume={r_arr.ndim}, jd={j_arr.ndim}")
            raise ValueError("Both embeddings must be 1D vectors.")

        if r_arr.shape[0] != j_arr.shape[0]:
            logger.error(f"Embedding dimensions mismatch: resume={r_arr.shape[0]}, jd={j_arr.shape[0]}")
            raise ValueError("Both embeddings must have the same dimension length.")

        try:
            logger.info("Reshaping embedding arrays for sklearn cosine_similarity computation...")
            # Reshape 1D arrays to 2D row vectors (1, N) for scikit-learn
            r_reshaped = r_arr.reshape(1, -1)
            j_reshaped = j_arr.reshape(1, -1)

            # Compute similarity
            raw_score = cosine_similarity(r_reshaped, j_reshaped)[0][0]

            # Bound the score between 0.0 and 1.0 (cosine similarity ranges from -1.0 to 1.0)
            bounded_score = max(0.0, min(1.0, float(raw_score)))

            # Round to 4 decimal places
            final_score = round(bounded_score, 4)

            logger.info(f"Similarity score calculated successfully: {final_score}")
            return final_score

        except Exception as e:
            logger.error(f"Cosine similarity computation failed: {str(e)}")
            raise SemanticMatchingError(f"Similarity calculation failed: {str(e)}") from e
