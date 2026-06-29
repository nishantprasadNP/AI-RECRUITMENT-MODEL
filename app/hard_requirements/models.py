"""
Pydantic data models for the Phase 5 Hard Requirements matching module in ARIS V2.
"""

from typing import List, Dict
from pydantic import BaseModel, Field, ConfigDict


class HardRequirementResult(BaseModel):
    """
    Represents the evaluation results of matching candidate profiles
    against hard (required/preferred) job requirements.
    """
    model_config = ConfigDict(strict=True)

    passed: bool = Field(
        default=False,
        description="Whether the candidate met all critical hard requirements."
    )
    coverage_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="The percentage of hard requirements matched, as a float between 0.0 and 1.0 inclusive."
    )
    matched_required: List[str] = Field(
        default_factory=list,
        description="List of mandatory/required skills or criteria successfully matched."
    )
    missing_required: List[str] = Field(
        default_factory=list,
        description="List of mandatory/required skills or criteria that were not matched."
    )
    matched_preferred: List[str] = Field(
        default_factory=list,
        description="List of preferred (nice-to-have) skills or criteria successfully matched."
    )
    missing_preferred: List[str] = Field(
        default_factory=list,
        description="List of preferred (nice-to-have) skills or criteria that were not matched."
    )
    critical_failures: List[str] = Field(
        default_factory=list,
        description="Specific mandatory skills or criteria whose absence triggered a direct failure."
    )
    decision_reason: str = Field(
        default="",
        description="Recruiter-friendly summary justification explaining the evaluation outcome."
    )


class CapabilityResolutionResult(BaseModel):
    """
    Represents the unified candidate capability set, separating explicit skills,
    inferred skills, and the combined capability set.
    """
    model_config = ConfigDict(strict=True)

    explicit_skills: List[str] = Field(
        default_factory=list,
        description="List of explicit skills extracted from the candidate resume profile."
    )
    inferred_skills: List[str] = Field(
        default_factory=list,
        description="List of parent/ancestor skills inferred via the Skill Knowledge Graph."
    )
    candidate_capabilities: List[str] = Field(
        default_factory=list,
        description="The combined, deduplicated list of explicit and inferred skills."
    )
    skill_origins: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="A mapping from inferred skills to the explicit source skills that triggered them."
    )


class RequirementMatchResult(BaseModel):
    """
    Represents the detailed matching result between candidate capabilities and hard requirements.
    """
    model_config = ConfigDict(strict=True)

    matched_required: list[str] = Field(
        default_factory=list,
        description="List of required skills that the candidate has."
    )
    missing_required: list[str] = Field(
        default_factory=list,
        description="List of required skills that the candidate is missing."
    )
    matched_preferred: list[str] = Field(
        default_factory=list,
        description="List of preferred skills that the candidate has."
    )
    missing_preferred: list[str] = Field(
        default_factory=list,
        description="List of preferred skills that the candidate is missing."
    )
    coverage_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Score representing percentage of required requirements matched (0.0 to 1.0)."
    )
    critical_failures: list[str] = Field(
        default_factory=list,
        description="List of critical missing required skills."
    )


