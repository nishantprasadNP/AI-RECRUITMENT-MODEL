"""
run_resume_pipeline.py — Resume parsing + extraction demo script.

Reads a resume PDF, extracts raw text via the dual-engine parser, calls the
Gemini LLM to extract a structured candidate profile, and saves it to
data/extracted_profiles/.

Usage:
    python scripts/run_resume_pipeline.py
    python scripts/run_resume_pipeline.py path/to/resume.pdf
"""

import os
import sys

# Ensure the project root is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.logging_setup import setup_logging
from app.ingestion.resume_parser import ResumeParser
from app.extraction.resume_extractor import ResumeInformationExtractor, MissingAPIKeyError
from app.storage.profile_storage import save_profile


def main() -> None:
    setup_logging()

    resume_path = sys.argv[1] if len(sys.argv) > 1 else "sample_resumes/resume1.pdf"

    print("=" * 80)
    print("      AI Recruitment Intelligence System — Resume Pipeline")
    print("=" * 80)

    if not os.path.exists(resume_path):
        print(f"[-] Error: Resume file not found at '{resume_path}'.")
        sys.exit(1)

    # Stage 1: Parse PDF
    print(f"[*] Parsing resume PDF: {resume_path}")
    parser = ResumeParser()
    try:
        resume_text = parser.extract_text(resume_path)
        print(f"[+] Text extracted successfully ({len(resume_text)} characters).")
    except Exception as e:
        print(f"[-] Failed to parse PDF: {type(e).__name__} — {e}")
        sys.exit(1)

    # Stage 2: Extract structured profile
    print("[*] Extracting structured profile via LLM...")
    extractor = ResumeInformationExtractor()
    try:
        profile = extractor.extract(resume_text)
    except MissingAPIKeyError:
        print("\n[!] GEMINI_API_KEY is not set. Please configure it in .env and try again.")
        sys.exit(1)
    except Exception as e:
        print(f"[-] Extraction failed: {type(e).__name__} — {e}")
        sys.exit(1)

    # Stage 3: Save profile
    saved_path = save_profile(profile)
    print(f"[+] Profile saved to: {saved_path}")

    print("\n" + "=" * 30 + " EXTRACTED PROFILE " + "=" * 31)
    print(profile.model_dump_json(indent=2))
    print("=" * 80)


if __name__ == "__main__":
    main()
