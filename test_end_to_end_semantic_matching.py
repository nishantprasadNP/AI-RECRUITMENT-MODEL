import os
import json
import logging
import glob
from app.models.resume_schema import ResumeProfile
from app.models.job_schema import JobProfile
from app.embeddings.text_builder import build_resume_text, build_job_text
from app.embeddings.embedding_generator import EmbeddingGenerator, EmbeddingGenerationError
from app.matcher.semantic_matcher import SemanticMatcher, SemanticMatchingError

# Configure logging to console
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("test_end_to_end_semantic_matching")

def main():
    try:
        # 1. Load Resume Profile
        profiles_dir = os.path.join("data", "extracted_profiles")
        json_resumes = glob.glob(os.path.join(profiles_dir, "*.json"))
        
        if not json_resumes:
            logger.error(f"No JSON resume profile files found in {profiles_dir}. Please run the resume parser first.")
            return

        selected_resume_path = json_resumes[0]
        logger.info(f"Loading resume profile from: {selected_resume_path}")
        
        with open(selected_resume_path, "r", encoding="utf-8") as f:
            resume_data = json.load(f)
            resume_profile = ResumeProfile.model_validate(resume_data)
        
        candidate_name = resume_profile.name if resume_profile.name else "Unknown Candidate"
        logger.info(f"Successfully loaded profile for candidate: {candidate_name}")

        # 2. Load Job Profile
        jobs_dir = os.path.join("data", "extracted_jobs")
        json_jobs = glob.glob(os.path.join(jobs_dir, "*.json"))
        
        if not json_jobs:
            logger.error(f"No JSON job files found in {jobs_dir}. Please run the job extractor first.")
            return

        selected_job_path = json_jobs[0]
        logger.info(f"Loading job profile from: {selected_job_path}")
        
        with open(selected_job_path, "r", encoding="utf-8") as f:
            job_data = json.load(f)
            job_profile = JobProfile.model_validate(job_data)
            
        # Infer Job Name from the JSON filename
        filename_raw = os.path.splitext(os.path.basename(selected_job_path))[0]
        job_name = " ".join(word.capitalize() for word in filename_raw.split("_"))
        logger.info(f"Successfully loaded job profile: {job_name}")

        # 3. Convert ResumeProfile to semantic text
        logger.info("Converting ResumeProfile to semantic text...")
        resume_text = build_resume_text(resume_profile)

        # 4. Convert JobProfile to semantic text
        logger.info("Converting JobProfile to semantic text...")
        job_text = build_job_text(job_profile)

        # 5. Generate Embeddings using EmbeddingGenerator
        logger.info("Initializing SentenceTransformer EmbeddingGenerator...")
        generator = EmbeddingGenerator()
        
        logger.info("Generating embedding for candidate resume text...")
        resume_embedding = generator.generate_embedding(resume_text)
        
        logger.info("Generating embedding for job description text...")
        jd_embedding = generator.generate_embedding(job_text)

        # 6. Compute similarity using SemanticMatcher
        logger.info("Initializing SemanticMatcher...")
        matcher = SemanticMatcher()
        
        logger.info("Computing semantic similarity score...")
        score = matcher.compute_similarity(resume_embedding, jd_embedding)

        # 7. Print results
        print("\n==================================================")
        print(" END-TO-END SEMANTIC MATCHING RESULTS")
        print("==================================================")
        print(f"Candidate: {candidate_name}\n")
        print(f"Job: {job_name}\n")
        print(f"Semantic Score: {score:.4f}")
        print("==================================================\n")

    except FileNotFoundError as e:
        logger.error(f"File system error: {str(e)}")
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON file: {str(e)}")
    except ValueError as e:
        logger.error(f"Input validation error: {str(e)}")
    except EmbeddingGenerationError as e:
        logger.error(f"Embedding generation failed: {str(e)}")
    except SemanticMatchingError as e:
        logger.error(f"Similarity matching failed: {str(e)}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main()
