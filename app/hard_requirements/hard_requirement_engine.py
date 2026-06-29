"""
Hard Requirements Engine for Phase 5 in ARIS V2.
Matches candidate capabilities against job requirements.
"""

import logging
from typing import Optional
from app.schemas.job_schema import JobProfile
from app.role_classification.models import RoleProfile
from app.hard_requirements.models import HardRequirementResult, CapabilityResolutionResult
from app.hard_requirements.requirement_matcher import RequirementMatcher
from app.hard_requirements.exceptions import RequirementMatchingError

logger = logging.getLogger("aris.hard_requirements.engine")


class HardRequirementEngine:
    """
    Evaluates resolved candidate capabilities against required and preferred job criteria
    using the RequirementMatcher layer.
    """

    def __init__(self, matcher: Optional[RequirementMatcher] = None) -> None:
        self._matcher = matcher or RequirementMatcher()

    def evaluate_compliance(
        self,
        job_profile: JobProfile,
        role_profile: RoleProfile,
        capabilities: CapabilityResolutionResult
    ) -> HardRequirementResult:
        """
        Evaluates candidate capability compliance against job requirements.

        Args:
            job_profile: The JobProfile containing job requirements.
            role_profile: The classified RoleProfile context (reserved for future use).
            capabilities: The resolved candidate capabilities.

        Returns:
            A HardRequirementResult with compliance evaluation details.

        Raises:
            RequirementMatchingError: If any of the inputs is None or evaluation fails.
        """
        if job_profile is None:
            raise RequirementMatchingError("job_profile cannot be None.")
        if role_profile is None:
            raise RequirementMatchingError("role_profile cannot be None.")
        if capabilities is None:
            raise RequirementMatchingError("capabilities cannot be None.")

        try:
            logger.info("Evaluating hard requirements compliance...")

            # 1. Call RequirementMatcher
            match_result = self._matcher.match_requirements(job_profile, capabilities)

            # 2. Determine pass/fail
            passed = len(match_result.missing_required) == 0

            # 3. Decision Reason
            if passed:
                decision_reason = "All required skills satisfied."
            else:
                decision_reason = f"Missing required skills: {', '.join(match_result.missing_required)}"

            # Build and return the result Pydantic model
            return HardRequirementResult(
                passed=passed,
                coverage_score=match_result.coverage_score,
                matched_required=match_result.matched_required,
                missing_required=match_result.missing_required,
                matched_preferred=match_result.matched_preferred,
                missing_preferred=match_result.missing_preferred,
                critical_failures=match_result.critical_failures,
                decision_reason=decision_reason
            )

        except Exception as e:
            if isinstance(e, RequirementMatchingError):
                raise
            raise RequirementMatchingError(f"Compliance evaluation failed: {e}") from e
