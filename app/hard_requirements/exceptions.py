"""
Custom exception classes for the Phase 5 Hard Requirements matching module in ARIS V2.
"""

from app.core.exceptions import ARISError


class HardRequirementError(ARISError):
    """Base exception for all hard requirement matching errors."""
    pass


class CapabilityResolutionError(HardRequirementError):
    """Exception raised when skill graph capability resolution fails."""
    pass


class RequirementMatchingError(HardRequirementError):
    """Exception raised when matching candidate skills against job requirements fails."""
    pass


class CoverageEvaluationError(HardRequirementError):
    """Exception raised when calculating requirement coverage score fails."""
    pass
