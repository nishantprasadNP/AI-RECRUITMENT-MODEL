import os
import json
import logging
from app.models.resume_schema import ResumeProfile
from app.models.job_schema import JobProfile
from app.embeddings.text_builder import build_resume_text, build_job_text
from app.embeddings.embedder import EmbeddingService

# Configure logging to console
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

def main():
    resume_path = os.path.join("data", "extracted_profiles", "nishant_prasad.json")
    job_path = os.path.join("data", "extracted_jobs", "senior_software_engineer.json")

    print("\n==================================================")
    print("AI Recruitment Intelligence System (ARIS) - Matching Demo")
    print("==================================================\n")

    # 1. Load profiles
    print(f"[*] Loading Resume Profile from: {resume_path}")
    if not os.path.exists(resume_path):
        print(f"[!] Error: Resume file not found at {resume_path}. Make sure to run parsing first.")
        return
        
    with open(resume_path, "r", encoding="utf-8") as f:
        resume_data = json.load(f)
        resume_profile = ResumeProfile.model_validate(resume_data)
        
    print(f"[*] Loading Job Profile from: {job_path}")
    if not os.path.exists(job_path):
        print(f"[!] Error: Job description file not found at {job_path}. Make sure to run extraction first.")
        return
        
    with open(job_path, "r", encoding="utf-8") as f:
        job_data = json.load(f)
        job_profile = JobProfile.model_validate(job_data)

    # 2. Build semantic texts
    print("\n[*] Converting profiles into semantic text...")
    resume_text = build_resume_text(resume_profile)
    job_text = build_job_text(job_profile)

    print("\n--- RESUME SEMANTIC TEXT (FIRST 300 CHARACTERS) ---")
    print(resume_text[:300] + "...")
    print("--------------------------------------------------")

    print("\n--- JOB DESCRIPTION SEMANTIC TEXT (FIRST 300 CHARACTERS) ---")
    print(job_text[:300] + "...")
    print("--------------------------------------------------")

    # 3. Generate Embeddings & Calculate Similarity
    print("\n[*] Initializing Embedding Service...")
    # Will automatically pick up GEMINI_API_KEY from .env
    embedder = EmbeddingService()

    try:
        print("[*] Generating embedding vector for Resume...")
        resume_vector = embedder.get_embedding(resume_text)
        
        print("[*] Generating embedding vector for JD...")
        job_vector = embedder.get_embedding(job_text)
        
        print(f"\n[*] Vectors successfully created.")
        print(f"    Resume Vector Dimension: {len(resume_vector)}")
        print(f"    Job Vector Dimension: {len(job_vector)}")

        print("\n[*] Calculating cosine similarity...")
        similarity_score = embedder.calculate_similarity(resume_vector, job_vector)
        
        print("\n==================================================")
        print(f" SUCCESS: Matching Completed Successfully!")
        print(f" Semantic Match Score: {similarity_score:.4f} ({similarity_score * 100:.2f}%)")
        print("==================================================\n")
        
    except Exception as e:
        print(f"\n[!] Error during embedding or similarity computation: {str(e)}")

if __name__ == "__main__":
    main()
