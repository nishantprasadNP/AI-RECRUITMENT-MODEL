from app.parsers.resume_parser import ResumeParser

parser = ResumeParser()

resume_text = parser.extract_text(
    "sample_resumes/resume1.pdf"
)

with open("parsed_resume.txt", "w", encoding="utf-8") as f:
    f.write(resume_text)

print("Resume parsed successfully.")
print(f"Characters extracted: {len(resume_text)}")