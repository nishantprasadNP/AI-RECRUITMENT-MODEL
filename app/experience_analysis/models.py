"""
Models for representing skill evidence and confidence profiles.
"""

from typing import List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class SkillEvidence(BaseModel):
    """
    Represents the collected evidence for a specific skill from a candidate's profile.
    """
    model_config = ConfigDict(strict=True)

    skill: str = Field(
        ...,
        description="The normalized name of the skill."
    )
    project_count: int = Field(
        default=0,
        description="The number of projects in which the candidate utilized this skill."
    )
    projects: List[str] = Field(
        default_factory=list,
        description="List of project names where this skill was explicitly used."
    )
    professional_usage: bool = Field(
        default=False,
        description="True if the skill was demonstrated in a professional employment context."
    )
    roles: List[str] = Field(
        default_factory=list,
        description="List of professional roles/job titles associated with the usage of this skill."
    )
    skill_mentions: int = Field(
        default=0,
        description="Number of times the skill is explicitly mentioned across the candidate's profile."
    )
    achievement_mentions: int = Field(
        default=0,
        description="Number of times the skill is mentioned within candidate achievements or awards."
    )
    dependency_mentions: float = Field(
        default=0.0,
        description="Propagated mentions from requiring dependencies."
    )
    dependency_sources: List[str] = Field(
        default_factory=list,
        description="Unique Requiring dependency skill names that propagated evidence."
    )
    direct_mentions: int = Field(
        default=0,
        description="Number of direct mentions of the skill on the resume."
    )


class SkillConfidenceProfile(BaseModel):
    """
    Represents the computed signal strengths and overall confidence level for a skill.
    """
    model_config = ConfigDict(strict=True)

    skill: str = Field(
        ...,
        description="The normalized name of the skill."
    )
    professional_signal: float = Field(
        ...,
        description="Signal strength derived from professional workspace usage (range 0.0 to 1.0)."
    )
    depth_signal: float = Field(
        ...,
        description="Signal strength derived from duration and depth of experience (range 0.0 to 1.0)."
    )
    complexity_signal: float = Field(
        ...,
        description="Signal strength derived from the complexity of the roles and projects (range 0.0 to 1.0)."
    )
    confidence_score: float = Field(
        ...,
        description="The computed overall confidence score (range 0.0 to 100.0)."
    )
    confidence_level: str = Field(
        ...,
        description="The qualitative confidence level category (e.g., 'Low', 'Medium', 'High', 'Expert')."
    )
    skill_tier: str = Field(
        default="Beginner",
        description="The qualitative recruiter-friendly skill tier (e.g., 'Beginner', 'Intermediate', 'Advanced', 'Expert')."
    )
    evidence_summary: Dict[str, Any] = Field(
        default_factory=dict,
        description="Explainability metadata summarizing the raw evidence collected for the skill."
    )



