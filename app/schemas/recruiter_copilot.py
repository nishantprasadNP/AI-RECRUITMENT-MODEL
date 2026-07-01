"""
Pydantic data models for the Recruiter Copilot (Explainability DTO) in ARIS V2.
"""

from typing import List, Dict
from pydantic import BaseModel, Field, ConfigDict


class RecruiterRecommendation(BaseModel):
    """
    Represents the recruiter-friendly explanation and recommendation for a candidate.
    """
    model_config = ConfigDict(strict=True)

    overall_score: float = Field(
        ...,
        description="The overall role-weighted candidate evaluation score."
    )
    why_score: List[str] = Field(
        default_factory=list,
        description="Deterministic list of check/cross points explaining the overall score."
    )
    strengths: List[str] = Field(
        default_factory=list,
        description="Recruiter-friendly summary list of candidate strengths."
    )
    missing_skills: List[str] = Field(
        default_factory=list,
        description="Skills from the job description that the candidate is missing."
    )
    recommendation: str = Field(
        ...,
        description="Actionable decision recommendation (Reject, Not Recommended, Recruiter Review, Proceed to Technical Interview)."
    )
    confidence_summary: Dict[str, float] = Field(
        default_factory=dict,
        description="Mapping of skill names to numerical confidence scores (0-100)."
    )
