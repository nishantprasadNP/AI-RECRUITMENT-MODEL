import logging
from app.embeddings.embedding_generator import EmbeddingGenerator, EmbeddingGenerationError
from app.matcher.semantic_matcher import SemanticMatcher, SemanticMatchingError

# Configure logging to console
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("test_semantic_matcher_demo")

def main():
    resume_text = "Python Machine Learning TensorFlow"
    jd_text = "Python Machine Learning Deep Learning"
    
    print("\n==================================================")
    print(" SEMANTIC MATCHER WORKFLOW TEST")
    print("==================================================")
    print(f"Resume Text: '{resume_text}'")
    print(f"JD Text:     '{jd_text}'\n")

    try:
        # 1. Initialize local embedding generator
        logger.info("Initializing local SentenceTransformer EmbeddingGenerator...")
        generator = EmbeddingGenerator()

        # 2. Generate embeddings
        logger.info("Generating embedding for Resume Text...")
        resume_embedding = generator.generate_embedding(resume_text)
        
        logger.info("Generating embedding for JD Text...")
        jd_embedding = generator.generate_embedding(jd_text)

        # 3. Compute similarity
        logger.info("Initializing SemanticMatcher...")
        matcher = SemanticMatcher()
        
        logger.info("Computing semantic similarity score...")
        score = matcher.compute_similarity(resume_embedding, jd_embedding)

        # 4. Print results
        print("\n==================================================")
        print(f"Semantic Score: {score:.4f}")
        print("==================================================\n")

    except ValueError as e:
        logger.error(f"Input validation error: {str(e)}")
    except EmbeddingGenerationError as e:
        logger.error(f"Embedding generation failed: {str(e)}")
    except SemanticMatchingError as e:
        logger.error(f"Semantic similarity calculation failed: {str(e)}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main()
