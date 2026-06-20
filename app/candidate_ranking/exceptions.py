"""
Custom exception classes for Phase 11 Candidate Ranking Engine in ARIS V2.
"""

from app.core.exceptions import ARISError


class CandidateRankingError(ARISError):
    """Base exception for all candidate ranking errors."""
    pass


class TieBreakerError(CandidateRankingError):
    """Exception raised when sorting tie-breakers fail."""
    pass


class RankingEngineError(CandidateRankingError):
    """Exception raised when candidate ranking execution fails."""
    pass
