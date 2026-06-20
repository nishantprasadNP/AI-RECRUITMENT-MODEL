"""
Custom exceptions for the Phase 4 Evaluation Strategy Engine in ARIS V2.
"""

from app.core.exceptions import ARISError


class EvaluationStrategyError(ARISError):
    """Base exception for all evaluation strategy errors."""
    pass


class StrategyNotFoundError(EvaluationStrategyError):
    """Exception raised when a requested strategy profile is not found."""
    pass


class InvalidStrategyConfigError(EvaluationStrategyError):
    """Exception raised when a strategy configuration is invalid."""
    pass
