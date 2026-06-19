"""
Shared exception base classes for the AI Recruitment Intelligence System.

Domain-specific exceptions (e.g. EmptyResumeTextError, EmptyPDFError) are still
defined in their respective modules to keep those modules self-contained.  The
classes here are shared infrastructure types used across more than one module.
"""


class ARISError(Exception):
    """Root base exception for all ARIS errors."""
    pass


class MissingAPIKeyError(ARISError):
    """Raised when the Gemini API key is not configured."""
    pass


class GeminiAPIError(ARISError):
    """Raised when a Gemini API request fails or returns an unexpected response."""
    pass


class InvalidJSONResponseError(ARISError):
    """Raised when the LLM response cannot be parsed as valid JSON."""
    pass


class ProfileValidationError(ARISError):
    """Raised when a parsed JSON payload fails Pydantic schema validation."""
    pass
