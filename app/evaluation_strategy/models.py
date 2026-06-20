"""
Pydantic data models for the Phase 4 Evaluation Strategy Engine in ARIS V2.
"""

from typing import Dict
from pydantic import BaseModel, Field, ConfigDict, model_validator


class EvaluationStrategy(BaseModel):
    """
    Represents the evaluation strategy containing criteria weights and thresholds
    customized for a specific role and seniority level.
    """
    model_config = ConfigDict(strict=True)

    evaluation_profile: str = Field(
        ...,
        description="The standardized evaluation profile identifier, e.g. 'intern_backend'."
    )
    strictness_level: str = Field(
        ...,
        description="The qualification strictness level ('low', 'medium', 'high')."
    )
    component_weights: Dict[str, float] = Field(
        ...,
        description="Attribute component weights for candidate evaluation (must sum to 1.0)."
    )
    minimum_skill_confidence: float = Field(
        ...,
        description="The minimum confidence score required for skill verification."
    )
    hard_requirement_tolerance: float = Field(
        ...,
        description="Allowed threshold of missing hard requirements (between 0.0 and 1.0 or percentage)."
    )

    @model_validator(mode="after")
    def validate_weights_sum(self) -> "EvaluationStrategy":
        """
        Validates that the sum of all component weights is approximately 1.0.
        """
        total_weight = sum(self.component_weights.values())
        if not (0.999 <= total_weight <= 1.001):
            raise ValueError(f"Component weights must sum to approximately 1.0, got {total_weight}")
        return self
