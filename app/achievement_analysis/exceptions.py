"""
Custom exception classes for Phase 9 Achievement Analyzer in ARIS V2.
"""

from app.core.exceptions import ARISError


class AchievementAnalysisError(ARISError):
    """Base exception for all achievement analysis errors."""
    pass


class DetectionError(AchievementAnalysisError):
    """Exception raised when achievement detection fails."""
    pass


class ScoringError(AchievementAnalysisError):
    """Exception raised when achievement scoring fails."""
    pass
