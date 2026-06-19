"""
app/main.py — Lightweight CLI shim (legacy entry point).

For the full pipeline, use:
    python scripts/run_full_pipeline.py

For individual stages, use:
    python scripts/run_resume_pipeline.py
    python scripts/run_job_pipeline.py
    python scripts/run_matching.py
"""

import os
import sys

# Ensure project root is in the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.logging_setup import setup_logging
from app.ingestion.resume_parser import ResumeParser


def main() -> None:
    setup_logging()

    resume_path = sys.argv[1] if len(sys.argv) > 1 else "sample_resumes/resume.pdf"

    print("=" * 70)
    print("       AI Recruitment Intelligence System — Resume Parsing Demo")
    print("=" * 70)
    print("Tip: Run 'python scripts/run_full_pipeline.py' for the full orchestrated pipeline.")
    print()

    parser = ResumeParser()

    try:
        if not os.path.exists(resume_path) and resume_path == "sample_resumes/resume.pdf":
            print(f"[!] Warning: Default sample resume not found at '{resume_path}'")
            print("    Please place a PDF at that path or run:")
            print("    python app/main.py <path_to_resume.pdf>")
            return

        print(f"[*] Parsing file: {resume_path}")
        resume_text = parser.extract_text(resume_path)

        print("\n" + "=" * 30 + " EXTRACTED RESUME TEXT " + "=" * 30)
        print(resume_text)
        print("=" * 83)
        print(f"\n[+] Extraction complete. Character count: {len(resume_text)}")
        print("[+] Check 'logs/aris.log' for detailed logs.")

    except Exception as e:
        print(f"\n[-] Error occurred during parsing: {type(e).__name__} - {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
