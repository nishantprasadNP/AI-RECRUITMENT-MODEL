"""
Pydantic data models for the Skill Normalization module in ARIS.
"""

from pydantic import BaseModel, Field, ConfigDict


class NormalizedSkill(BaseModel):
    """
    Represents a single resolved canonical skill with an associated confidence score.
    """
    model_config = ConfigDict(strict=True)

    canonical: str = Field(
        ...,
        description="The resolved canonical name of the skill."
    )
    confidence: int = Field(
        ...,
        ge=0,
        le=100,
        description="Confidence score as an integer percentage (e.g. 50 or 100)."
    )
