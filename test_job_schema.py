from app.extraction.job_extractor import JobExtractor

jd = """
Backend Software Engineer

Required Skills:
- Python
- FastAPI
- Docker
- SQL
- Git

Preferred Skills:
- Redis
- Kafka
"""

extractor = JobExtractor()
job = extractor.extract(jd)

print(job)
print()

print(type(job.required_skills[0]))
print(job.required_skills[0])