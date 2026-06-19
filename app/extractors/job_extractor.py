"""
Backward-compatibility shim — app.extractors.job_extractor is preserved so
that existing tests still work via mock patching.
New code should import from app.extraction.job_extractor.
"""
from app.extraction.job_extractor import (  # noqa: F401
    JobExtractor,
    JobExtractorError,
    EmptyJobTextError,
    MissingAPIKeyError,
    GeminiAPIError,
    InvalidJSONResponseError,
    ProfileValidationError,
)
