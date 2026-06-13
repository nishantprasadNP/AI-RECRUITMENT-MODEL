import os
import sys
import logging

# Ensure app directory can be imported
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.extractors.job_extractor import JobExtractor, MissingAPIKeyError
from app.storage.job_storage import save_job_profile

def setup_logging():
    """Configures application logging to log to console and logs/resume_parser.log."""
    os.makedirs("logs", exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("logs/resume_parser.log", encoding="utf-8")
        ]
    )

def main():
    setup_logging()
    
    jd_path = "sample_jds/nishant_jd.txt"
    
    print("=" * 80)
    print("      AI Recruitment Intelligence System - Job Description Extraction")
    print("=" * 80)
    
    if not os.path.exists(jd_path):
        print(f"[-] Error: '{jd_path}' does not exist. Please place a sample JD at that path.")
        sys.exit(1)
        
    print(f"[*] Reading job description text from '{jd_path}'...")
    with open(jd_path, "r", encoding="utf-8") as f:
        job_text = f.read()

    print("[*] Extracting structured job profile details using LLM...")
    extractor = JobExtractor()
    
    try:
        profile = extractor.extract(job_text)
        
        print("[*] Saving validated job profile to disk...")
        saved_path = save_job_profile(profile, role_name="Senior_Software_Engineer")
        
        print("\n" + "=" * 25 + " EXTRACTED STRUCTURED JOB PROFILE JSON " + "=" * 25)
        print(profile.model_dump_json(indent=2))
        print("=" * 85)
        print(f"\n[+] Success! Job Profile JSON saved at: {saved_path}")
        print("[+] Check 'logs/resume_parser.log' for detailed execution logs.")
        
    except MissingAPIKeyError:
        print("\n[!] Configuration Error: Gemini API Key is missing.")
        print("    Please set the GEMINI_API_KEY environment variable and run again.")
        print("    Example (PowerShell): $env:GEMINI_API_KEY=\"your_key_here\"")
        print("    Example (CMD prompt): set GEMINI_API_KEY=your_key_here")
        sys.exit(1)
    except Exception as e:
        print(f"\n[-] Extraction failed: {type(e).__name__} - {e}")
        print("[-] Check the log file for stack traces and error logs.")
        sys.exit(1)

if __name__ == "__main__":
    main()
