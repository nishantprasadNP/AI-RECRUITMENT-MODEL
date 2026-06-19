"""
run_job_pipeline.py — Job description extraction demo script.

Reads a raw job description text file, calls the Gemini LLM to extract a
structured hiring profile, and saves it to data/extracted_jobs/.

Usage:
    python scripts/run_job_pipeline.py
    python scripts/run_job_pipeline.py path/to/jd.txt "Senior Software Engineer"
"""

import os
import sys

# Ensure the project root is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.logging_setup import setup_logging
from app.extraction.job_extractor import JobExtractor, MissingAPIKeyError
from app.storage.job_storage import save_job_profile


def main() -> None:
    setup_logging()

    jd_path = sys.argv[1] if len(sys.argv) > 1 else "sample_jds/senior_software_engineer.txt"
    role_name = sys.argv[2] if len(sys.argv) > 2 else "role"

    print("=" * 80)
    print("      AI Recruitment Intelligence System — Job Description Pipeline")
    print("=" * 80)

    if not os.path.exists(jd_path):
        print(f"[-] Error: Job description file not found at '{jd_path}'.")
        sys.exit(1)

    print(f"[*] Reading job description from: {jd_path}")
    with open(jd_path, "r", encoding="utf-8") as f:
        job_text = f.read()

    print("[*] Extracting structured job profile via LLM...")
    extractor = JobExtractor()
    try:
        profile = extractor.extract(job_text)
    except MissingAPIKeyError:
        print("\n[!] GEMINI_API_KEY is not set. Please configure it in .env and try again.")
        sys.exit(1)
    except Exception as e:
        print(f"[-] Extraction failed: {type(e).__name__} — {e}")
        sys.exit(1)

    saved_path = save_job_profile(profile, role_name=role_name)
    print(f"[+] Job profile saved to: {saved_path}")

    print("\n" + "=" * 28 + " EXTRACTED JOB PROFILE " + "=" * 29)
    print(profile.model_dump_json(indent=2))
    print("=" * 80)


if __name__ == "__main__":
    main()
