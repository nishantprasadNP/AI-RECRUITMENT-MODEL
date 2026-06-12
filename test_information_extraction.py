import os
import sys
import logging

# Ensure app directory can be imported
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.parsers.resume_parser import ResumeParser
from app.extractors.resume_information_extractor import ResumeInformationExtractor, MissingAPIKeyError
from app.storage.profile_storage import save_profile

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
    
    txt_path = "parsed_resume.txt"
    pdf_path = "sample_resumes/resume1.pdf"
    
    print("=" * 80)
    print("      AI Recruitment Intelligence System - Resume Information Extraction")
    print("=" * 80)
    
    # 1. Check if parsed_resume.txt exists, if not generate it from sample_resumes/resume1.pdf
    if not os.path.exists(txt_path):
        print(f"[*] '{txt_path}' not found. Generating from '{pdf_path}' first...")
        if not os.path.exists(pdf_path):
            print(f"[-] Error: '{pdf_path}' does not exist. Please place a sample PDF there.")
            sys.exit(1)
        
        parser = ResumeParser()
        try:
            resume_text = parser.extract_text(pdf_path)
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(resume_text)
            print(f"[+] Successfully generated and saved extracted text to '{txt_path}'")
        except Exception as e:
            print(f"[-] Failed to parse PDF: {str(e)}")
            sys.exit(1)
            
    # Read parsed_resume.txt
    print(f"[*] Reading parsed resume text from '{txt_path}'...")
    with open(txt_path, "r", encoding="utf-8") as f:
        resume_text = f.read()

    # 2. Instantiate extractor and perform extraction
    print("[*] Extracting structured profile details using LLM...")
    extractor = ResumeInformationExtractor()
    
    try:
        profile = extractor.extract(resume_text)
        
        # 3. Save extraction to disk
        print("[*] Saving validated profile to disk...")
        saved_path = save_profile(profile)
        
        # 4. Print final output
        print("\n" + "=" * 25 + " EXTRACTED STRUCTURED PROFILE JSON " + "=" * 25)
        print(profile.model_dump_json(indent=2))
        print("=" * 85)
        print(f"\n[+] Success! Profile JSON saved at: {saved_path}")
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
