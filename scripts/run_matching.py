"""
run_matching.py — Semantic matching demo script.

Loads existing candidate and job profile JSONs from data/, builds semantic
text representations, generates local SentenceTransformer embeddings, and
computes the cosine similarity match score.

Usage:
    python scripts/run_matching.py
    python scripts/run_matching.py data/extracted_profiles/john_doe.json data/extracted_jobs/senior_engineer.json
"""

import glob
import json
import logging
import os
import sys

# Ensure the project root is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.logging_setup import setup_logging
from app.schemas.resume_schema import ResumeProfile
from app.schemas.job_schema import JobProfile
from app.embeddings.text_builder import build_resume_text, build_job_text
from app.embeddings.embedding_generator import EmbeddingGenerator, EmbeddingGenerationError
from app.matching.semantic_matcher import SemanticMatcher, SemanticMatchingError

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("run_matching")


def main() -> None:
    setup_logging()

    # Resolve profile paths
    resume_path = sys.argv[1] if len(sys.argv) > 1 else None
    job_path = sys.argv[2] if len(sys.argv) > 2 else None

    if not resume_path:
        profiles = glob.glob(os.path.join("data", "extracted_profiles", "*.json"))
        if not profiles:
            logger.error("No resume profiles found in data/extracted_profiles/. Run run_resume_pipeline.py first.")
            sys.exit(1)
        resume_path = profiles[0]

    if not job_path:
        jobs = glob.glob(os.path.join("data", "extracted_jobs", "*.json"))
        if not jobs:
            logger.error("No job profiles found in data/extracted_jobs/. Run run_job_pipeline.py first.")
            sys.exit(1)
        job_path = jobs[0]

    logger.info("Loading resume profile: %s", resume_path)
    with open(resume_path, "r", encoding="utf-8") as f:
        resume_profile = ResumeProfile.model_validate(json.load(f))

    logger.info("Loading job profile: %s", job_path)
    with open(job_path, "r", encoding="utf-8") as f:
        job_profile = JobProfile.model_validate(json.load(f))

    job_name = " ".join(w.capitalize() for w in os.path.splitext(os.path.basename(job_path))[0].split("_"))
    candidate_name = resume_profile.name or "Unknown Candidate"

    # Build semantic text
    resume_text = build_resume_text(resume_profile)
    job_text = build_job_text(job_profile)

    # Generate embeddings
    logger.info("Initialising SentenceTransformer embedding model...")
    generator = EmbeddingGenerator()
    resume_embedding = generator.generate_embedding(resume_text)
    jd_embedding = generator.generate_embedding(job_text)

    # Compute similarity
    score = SemanticMatcher().compute_similarity(resume_embedding, jd_embedding)

    print("\n" + "=" * 60)
    print(" END-TO-END SEMANTIC MATCHING RESULTS")
    print("=" * 60)
    print(f" Candidate : {candidate_name}")
    print(f" Role      : {job_name}")
    print(f" Score     : {score:.4f}  ({score * 100:.2f}%)")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
