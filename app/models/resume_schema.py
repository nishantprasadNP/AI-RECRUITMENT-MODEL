"""
Backward-compatibility shims — app.models.* is preserved so that existing
tests and any external code still resolve. New code should import from app.schemas.
"""
from app.schemas.resume_schema import (  # noqa: F401
    Skill,
    Experience,
    Project,
    Certification,
    Education,
    Achievement,
    ResumeProfile,
)
