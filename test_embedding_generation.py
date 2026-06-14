import os
import json
import logging
import glob
from app.models.resume_schema import ResumeProfile
from app.embeddings.text_builder import build_resume_text
from app.embeddings.embedding_generator import EmbeddingGenerator, EmbeddingGenerationError

# Configure logging to console
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("test_embedding_generation")

def main():
    try:
        # 1. Discover and load a ResumeProfile JSON
        profiles_dir = os.path.join("data", "extracted_profiles")
        json_files = glob.glob(os.path.join(profiles_dir, "*.json"))
        
        if not json_files:
            logger.error(f"No JSON profile files found in {profiles_dir}. Please run the resume parser first.")
            return

        selected_profile_path = json_files[0]
        logger.info(f"Loading resume profile from: {selected_profile_path}")
        
        with open(selected_profile_path, "r", encoding="utf-8") as f:
            profile_data = json.load(f)
            profile = ResumeProfile.model_validate(profile_data)
        
        candidate_name = profile.name if profile.name else "Unknown Candidate"
        logger.info(f"Successfully loaded profile for candidate: {candidate_name}")

        # 2. Convert to clean semantic text
        logger.info("Converting structured JSON profile to clean semantic text...")
        resume_text = build_resume_text(profile)
        logger.debug(f"Generated text block:\n{resume_text[:200]}...")

        # 3. Generate embedding using EmbeddingGenerator
        logger.info("Initializing local SentenceTransformer EmbeddingGenerator...")
        generator = EmbeddingGenerator()
        
        logger.info("Generating embedding vector...")
        embedding = generator.generate_embedding(resume_text)

        # 4. Print results
        print("\n==================================================")
        print(" LOCAL EMBEDDING GENERATION COMPLETE")
        print("==================================================")
        print(f"Candidate: {candidate_name}\n")
        print("Embedding Shape:")
        print(embedding.shape)
        print("==================================================\n")

    except FileNotFoundError as e:
        logger.error(f"File system error: {str(e)}")
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON file: {str(e)}")
    except ValueError as e:
        logger.error(f"Input validation error: {str(e)}")
    except EmbeddingGenerationError as e:
        logger.error(f"Embedding generation engine failed: {str(e)}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main()
