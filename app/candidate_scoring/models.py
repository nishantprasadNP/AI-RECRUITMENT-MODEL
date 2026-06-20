"""
Pydantic data models for the Phase 10 Candidate Scoring Engine in ARIS V2.
"""

from typing import Dict, List
from pydantic import BaseModel, Field, ConfigDict


class CandidateScoreProfile(BaseModel):
    """
    Represents the calculated candidate scoring profile, containing component scores,
    weight breakdowns, and detailed explainability traces.
    """
    model_config = ConfigDict(strict=True)

    candidate_name: str = Field(
        ...,
        description="The full name of the candidate."
    )
    overall_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="The overall role-weighted candidate score between 0.0 and 100.0."
    )
    component_scores: Dict[str, float] = Field(
        default_factory=dict,
        description="Normalized scores (0-100) for each individual evaluation component."
    )
    weight_breakdown: Dict[str, float] = Field(
        default_factory=dict,
        description="The component weight allocations applied from the evaluation strategy."
    )
    explanation: List[str] = Field(
        default_factory=list,
        description="Trace explanations and justifications for each component score."
    )

    # Metadata metrics preserved for deterministic tie-breaking in ranking stage
    hard_requirements_coverage: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Preserved hard requirement coverage score (0.0 to 1.0) for tie-breaking."
    )
    semantic_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Preserved semantic match score (0.0 to 1.0) for tie-breaking."
    )
    skill_confidence_score: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Preserved average skill confidence score (0.0 to 100.0) for tie-breaking."
    )
    achievement_score: float = Field(
        default=0.0,
        ge=0.0,
        le=10.0,
        description="Preserved overall achievements score (0.0 to 10.0) for tie-breaking."
    )
