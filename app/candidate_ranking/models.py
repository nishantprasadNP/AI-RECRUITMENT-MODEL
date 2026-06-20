"""
Pydantic data models for the Phase 11 Candidate Ranking Engine in ARIS V2.
"""

from typing import List
from pydantic import BaseModel, Field, ConfigDict, RootModel


class RankedCandidate(BaseModel):
    """
    Represents a single ranked candidate, including their score, rank, strengths, and concerns.
    Supports flexible field instantiation via aliases.
    """
    model_config = ConfigDict(strict=True, populate_by_name=True)

    rank: int = Field(
        ...,
        description="The assigned rank position of the candidate (1-indexed)."
    )
    candidate_name: str = Field(
        ...,
        alias="candidate",
        description="The full name of the candidate."
    )
    overall_score: float = Field(
        ...,
        alias="score",
        description="The overall evaluation score of the candidate."
    )
    strengths: List[str] = Field(
        default_factory=list,
        description="Recruiter-friendly summary list of candidate strengths."
    )
    concerns: List[str] = Field(
        default_factory=list,
        description="Recruiter-friendly summary list of concerns or warnings."
    )


class RankedCandidateList(RootModel[List[RankedCandidate]]):
    """
    A list of RankedCandidate objects that serializes directly to a JSON array.
    """
    pass
