import os
import sys
import logging

# Ensure project root is in the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.parsers.resume_parser import ResumeParser

def setup_logging():
    """
    Configures the python logging system.
    Logs INFO and above to both standard output and a file named logs/resume_parser.log.
    """
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
    
    # Default to sample resume, check args for custom paths
    resume_path = "sample_resumes/resume.pdf"
    if len(sys.argv) > 1:
        resume_path = sys.argv[1]
        
    print("=" * 70)
    print("       AI Recruitment Intelligence System - Resume Parsing Demo")
    print("=" * 70)
    
    parser = ResumeParser()
    
    try:
        # Check if the target file exists
        if not os.path.exists(resume_path) and resume_path == "sample_resumes/resume.pdf":
            print(f"[!] Warning: Default sample resume not found at '{resume_path}'")
            print("    Please place a sample PDF file at that path or run:")
            print("    python app/main.py <path_to_your_resume.pdf>")
            return

        print(f"[*] Parsing file: {resume_path}")
        resume_text = parser.extract_text(resume_path)
        
        print("\n" + "=" * 30 + " EXTRACTED RESUME TEXT " + "=" * 30)
        print(resume_text)
        print("=" * 83)
        print(f"\n[+] Extraction complete. Character count: {len(resume_text)}")
        print("[+] Check 'logs/resume_parser.log' for detailed logs.")
        
    except Exception as e:
        print(f"\n[-] Error occurred during parsing: {type(e).__name__} - {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
