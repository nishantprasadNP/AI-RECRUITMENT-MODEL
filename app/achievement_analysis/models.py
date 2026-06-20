"""
Pydantic data models for the Phase 9 Achievement Analyzer in ARIS V2.
"""

from typing import List, Dict, Optional
from pydantic import BaseModel, Field, ConfigDict


class AchievementDetail(BaseModel):
    """
    Represents the details and source evidence of a single detected achievement.
    """
    model_config = ConfigDict(strict=True)

    title: str = Field(
        ...,
        description="The detailed name or description of the detected achievement."
    )
    source_section: str = Field(
        ...,
        description="The section of the resume where this was detected ('achievements', 'experience', 'projects', 'education')."
    )
    source_detail: str = Field(
        ...,
        description="Contextual details of the source (e.g. project name, company, degree, or raw text)."
    )
    score_contribution: float = Field(
        ...,
        description="The numerical score contribution of this specific achievement."
    )
    explanation: str = Field(
        ...,
        description="Recruiter-friendly trace explanation of how and why this achievement was scored."
    )


class AchievementProfile(BaseModel):
    """
    Represents the complete achievement evaluation profile for a candidate.
    """
    model_config = ConfigDict(strict=True)

    achievement_score: float = Field(
        ...,
        ge=0.0,
        le=10.0,
        description="Overall consolidated achievement score between 0.0 and 10.0."
    )
    academic: List[AchievementDetail] = Field(
        default_factory=list,
        description="List of academic achievements (e.g. JEE ranks, university distinctions, scholarships)."
    )
    technical: List[AchievementDetail] = Field(
        default_factory=list,
        description="List of technical achievements (e.g. hackathons, competitive programming, open source)."
    )
    research: List[AchievementDetail] = Field(
        default_factory=list,
        description="List of research achievements (e.g. papers, patents, research internships)."
    )
    leadership: List[AchievementDetail] = Field(
        default_factory=list,
        description="List of leadership signals (e.g. team management, club leadership, mentorship)."
    )
    entrepreneurship: List[AchievementDetail] = Field(
        default_factory=list,
        description="List of entrepreneurial signals (e.g. startup founder, YC experience, product ownership)."
    )
    category_scores: Dict[str, float] = Field(
        default_factory=dict,
        description="Calculated individual scores per achievement category."
    )
    explanation_traces: List[str] = Field(
        default_factory=list,
        description="Consolidated trace statements explaining the scoring justifications."
    )
