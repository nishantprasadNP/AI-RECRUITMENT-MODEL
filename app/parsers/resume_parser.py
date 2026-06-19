"""
Backward-compatibility shim — app.parsers.resume_parser is preserved so that
existing tests and scripts still work. New code should import from app.ingestion.
"""
from app.ingestion.resume_parser import ResumeParser  # noqa: F401
