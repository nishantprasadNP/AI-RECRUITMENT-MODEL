"""
Phase 12 — Skill Gap Analysis package.
"""

from app.skill_gap.models import SkillGapResult
from app.skill_gap.exceptions import (
    SkillGapError,
    GapAnalysisError,
    RecommendationGenerationError,
)
from app.skill_gap.skill_gap_engine import SkillGapEngine

__all__ = [
    "SkillGapResult",
    "SkillGapError",
    "GapAnalysisError",
    "RecommendationGenerationError",
    "SkillGapEngine",
]

