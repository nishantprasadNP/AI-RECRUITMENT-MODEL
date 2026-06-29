"""
Pydantic data models for the Phase 12 Skill Gap Analysis Engine in ARIS V2.
"""

from pydantic import BaseModel, Field, ConfigDict


class SkillGapResult(BaseModel):
    """
    Represents the result of a skill gap analysis for a candidate against a job description.
    """
    model_config = ConfigDict(strict=True)

    missing_required_skills: list[str] = Field(
        default_factory=list,
        description="List of required skills from the job description that the candidate is missing."
    )
    missing_preferred_skills: list[str] = Field(
        default_factory=list,
        description="List of preferred skills from the job description that the candidate is missing."
    )
    weak_skills: list[str] = Field(
        default_factory=list,
        description="List of candidate skills that require improvement or show weak evidence."
    )
    strong_skills: list[str] = Field(
        default_factory=list,
        description="List of candidate skills that show strong evidence and match the job description."
    )
    improvement_areas: list[str] = Field(
        default_factory=list,
        description="Actionable recommendations and areas of improvement for the candidate."
    )
    overall_gap_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Calculated overall skill gap score (0.0 to 1.0), where 0.0 means no gap and 1.0 means maximum gap."
    )
    decision_summary: str = Field(
        ...,
        description="A concise summary of the match decision and major skill gaps."
    )
