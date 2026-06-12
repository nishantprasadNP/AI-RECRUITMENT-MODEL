from app.parsers.resume_parser import ResumeParser

parser = ResumeParser()

resume_text = parser.extract_text(
    "sample_resumes/resume1.pdf"
)

print("\n===== EXTRACTED TEXT =====\n")
print(resume_text)

print("\n========================")
print("Characters:", len(resume_text))