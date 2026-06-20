"""
Custom exception classes for Phase 10 Candidate Scoring Engine in ARIS V2.
"""

from app.core.exceptions import ARISError


class CandidateScoringError(ARISError):
    """Base exception for all candidate scoring errors."""
    pass


class CalculatorError(CandidateScoringError):
    """Exception raised when a component score calculation fails."""
    pass


class EngineExecutionError(CandidateScoringError):
    """Exception raised when scoring engine execution fails."""
    pass
