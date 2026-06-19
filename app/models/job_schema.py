"""
Backward-compatibility shim — app.models.job_schema is preserved so that
existing tests and any external code still resolve. New code should import from app.schemas.
"""
from app.schemas.job_schema import (  # noqa: F401
    EducationRequirement,
    HiddenHiringSignals,
    JobProfile,
)
