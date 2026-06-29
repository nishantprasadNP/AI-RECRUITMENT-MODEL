"""
Custom exception classes for Phase 12 Skill Gap Analysis Engine in ARIS V2.
"""

from app.core.exceptions import ARISError


class SkillGapError(ARISError):
    """Base exception for all skill gap analysis and recommendation errors."""
    pass


class GapAnalysisError(SkillGapError):
    """Exception raised when skill gap calculation or analysis fails."""
    pass


class RecommendationGenerationError(SkillGapError):
    """Exception raised when generating skill gap recommendations fails."""
    pass
