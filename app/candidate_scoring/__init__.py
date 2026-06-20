"""
Phase 10 — Candidate Scoring Engine package.
"""

from app.candidate_scoring.models import CandidateScoreProfile
from app.candidate_scoring.score_calculators import ComponentScoreCalculators, parse_duration_to_years
from app.candidate_scoring.scoring_engine import CandidateScoringEngine
from app.candidate_scoring.exceptions import (
    CandidateScoringError,
    CalculatorError,
    EngineExecutionError,
)

__all__ = [
    "CandidateScoreProfile",
    "ComponentScoreCalculators",
    "parse_duration_to_years",
    "CandidateScoringEngine",
    "CandidateScoringError",
    "CalculatorError",
    "EngineExecutionError",
]
