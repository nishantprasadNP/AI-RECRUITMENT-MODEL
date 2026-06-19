"""
run_full_pipeline.py — End-to-end recruitment intelligence pipeline via the orchestrator.

This is the PRIMARY entry point for running the full ARIS pipeline.  It calls
RecruitmentOrchestrator.run() which handles all stages — PDF ingestion, LLM
extraction, semantic embedding, cosine similarity matching, and persistent
storage — in a single, clean call.

Usage:
    python scripts/run_full_pipeline.py
    python scripts/run_full_pipeline.py path/to/resume.pdf path/to/jd.txt "Role Name"
"""

import os
import sys

# Ensure the project root is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.logging_setup import setup_logging
from app.orchestrator import RecruitmentOrchestrator


def main() -> None:
    setup_logging()

    # Resolve arguments with sensible defaults
    resume_pdf_path = sys.argv[1] if len(sys.argv) > 1 else "sample_resumes/resume1.pdf"
    jd_path         = sys.argv[2] if len(sys.argv) > 2 else "sample_jds/senior_software_engineer.txt"
    job_name        = sys.argv[3] if len(sys.argv) > 3 else "role"

    print("=" * 80)
    print("       AI Recruitment Intelligence System (ARIS) — Full Pipeline")
    print("=" * 80)

    # Validate inputs
    if not os.path.exists(resume_pdf_path):
        print(f"[-] Resume PDF not found: {resume_pdf_path}")
        sys.exit(1)

    if not os.path.exists(jd_path):
        print(f"[-] Job description file not found: {jd_path}")
        sys.exit(1)

    with open(jd_path, "r", encoding="utf-8") as f:
        jd_text = f.read()

    print(f"[*] Resume  : {resume_pdf_path}")
    print(f"[*] JD file : {jd_path}")
    print(f"[*] Role    : {job_name}")
    print()

    # Run full pipeline via the orchestrator
    orchestrator = RecruitmentOrchestrator()
    try:
        result = orchestrator.run(
            resume_pdf_path=resume_pdf_path,
            jd_text=jd_text,
            job_name=job_name,
        )
    except Exception as e:
        print(f"\n[-] Pipeline failed: {type(e).__name__} — {e}")
        print("    Check logs/aris.log for full stack traces.")
        sys.exit(1)

    # Display results
    print("\n" + "=" * 80)
    print("  PIPELINE RESULTS")
    print("=" * 80)
    print(f"  Candidate          : {result.candidate_name}")
    print(f"  Role               : {result.job_name}")

    if result.role_profile:
        print("\n" + "=" * 80)
        print("\nROLE CONTEXT\n")
        print("=" * 80)
        print(f"\nRole Family        : {result.role_profile.role_family}")
        print(f"Specialization     : {result.role_profile.specialization}")
        print(f"Seniority          : {result.role_profile.seniority}")
        print(f"Evaluation Profile : {result.role_profile.evaluation_profile}\n")
        print("=" * 80)

    print(f"  Semantic Score     : {result.semantic_score:.4f}  ({result.semantic_score * 100:.2f}%)")
    print()
    print(f"  Resume Profile     : {result.resume_profile_path}")
    print(f"  Job Profile        : {result.job_profile_path}")
    print(f"  Match Report       : {result.match_report_path}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
