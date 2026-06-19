"""
Backward-compatibility shim — app.extractors.resume_information_extractor
is preserved so that existing tests still work via mock patching.
New code should import from app.extraction.resume_extractor.
"""
from app.extraction.resume_extractor import (  # noqa: F401
    ResumeInformationExtractor,
    ResumeExtractorError,
    EmptyResumeTextError,
    MissingAPIKeyError,
    GeminiAPIError,
    InvalidJSONResponseError,
    ProfileValidationError,
)
