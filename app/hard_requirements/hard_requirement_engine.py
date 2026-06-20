"""
Hard Requirements Engine for Phase 5 in ARIS V2.
Matches candidate capabilities against job requirements.
"""

import logging
from app.schemas.job_schema import JobProfile
from app.hard_requirements.models import HardRequirementResult, CapabilityResolutionResult
from app.hard_requirements.exceptions import RequirementMatchingError

logger = logging.getLogger("aris.hard_requirements.engine")


class HardRequirementEngine:
    """
    Evaluates resolved candidate capabilities against required and preferred job criteria.
    """
    def __init__(self) -> None:
        pass

    def evaluate_compliance(
        self,
        resolution: CapabilityResolutionResult,
        job_profile: JobProfile
    ) -> HardRequirementResult:
        """
        Matches resolved candidate capabilities against job description requirements.

        Args:
            resolution: The CapabilityResolutionResult from the CapabilityResolver.
            job_profile: The job requirements JobProfile.

        Returns:
            A HardRequirementResult with coverage and compliance details.
        """
        if not resolution:
            raise RequirementMatchingError("CapabilityResolutionResult cannot be None.")
        if not job_profile:
            raise RequirementMatchingError("JobProfile cannot be None.")

        try:
            candidate_caps = {c.lower().strip() for c in resolution.candidate_capabilities if c}

            req_skills = job_profile.required_skills or []
            pref_skills = job_profile.preferred_skills or []
            crit_skills = job_profile.critical_skills or []

            matched_req = []
            missing_req = []
            for skill in req_skills:
                if skill.lower().strip() in candidate_caps:
                    matched_req.append(skill)
                else:
                    missing_req.append(skill)

            matched_pref = []
            missing_pref = []
            for skill in pref_skills:
                if skill.lower().strip() in candidate_caps:
                    matched_pref.append(skill)
                else:
                    missing_pref.append(skill)

            # Determine critical failures based on job critical skills list
            # If critical_skills list is empty, all required skills are treated as critical
            crit_set = {c.lower().strip() for c in crit_skills if c}
            critical_failures = []
            for skill in missing_req:
                if not crit_set or skill.lower().strip() in crit_set:
                    critical_failures.append(skill)

            passed = len(critical_failures) == 0

            # Calculate coverage score
            total_req = len(req_skills)
            coverage = (len(matched_req) / total_req) if total_req > 0 else 1.0

            decision_reason = (
                f"Candidate matched {len(matched_req)} of {total_req} required skills. "
                f"Compliance result: {'PASSED' if passed else 'FAILED'}."
            )
            if not passed:
                decision_reason += f" Critical missing skills: {critical_failures}"

            return HardRequirementResult(
                passed=passed,
                coverage_score=round(coverage, 2),
                matched_required=matched_req,
                missing_required=missing_req,
                matched_preferred=matched_pref,
                missing_preferred=missing_pref,
                critical_failures=critical_failures,
                decision_reason=decision_reason
            )

        except Exception as e:
            raise RequirementMatchingError(f"Compliance evaluation failed: {e}") from e
