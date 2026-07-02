"""
RequirementMatcher — Case-insensitive requirement matching layer for ARIS V2.
"""

from app.schemas.job_schema import JobProfile
from app.hard_requirements.models import CapabilityResolutionResult, RequirementMatchResult


class RequirementMatcher:
    """
    Evaluates how closely a candidate's resolved capabilities match the
    required and preferred skills of a job description.
    """

    def match_requirements(
        self,
        job_profile: JobProfile,
        capabilities: CapabilityResolutionResult
    ) -> RequirementMatchResult:
        """
        Matches a candidate's capabilities against job required/preferred requirements.

        Args:
            job_profile: Job profile containing required and preferred skills.
            capabilities: Candidate capabilities (explicit and inferred).

        Returns:
            A RequirementMatchResult containing matching reports and coverage score.
        """
        # 1. Build a lowercase set from candidate capabilities
        candidate_capabilities_set = {
            skill.strip().lower() for skill in capabilities.candidate_capabilities
        }

        matched_required = []
        missing_required = []
        matched_preferred = []
        missing_preferred = []

        # 2. Match required skills (case-insensitive, preserving original casing)
        for skill in job_profile.required_skills:
            if skill.strip().lower() in candidate_capabilities_set:
                matched_required.append(skill)
            else:
                missing_required.append(skill)

        # 3. Match preferred skills (case-insensitive, preserving original casing)
        for skill in job_profile.preferred_skills:
            if skill.strip().lower() in candidate_capabilities_set:
                matched_preferred.append(skill)
            else:
                missing_preferred.append(skill)

        # 4. Coverage score (weighted)
        sum_importance = sum(getattr(skill, "importance", 5.0) for skill in job_profile.required_skills)
        if sum_importance == 0.0:
            coverage_score = 1.0
        else:
            sum_matched_importance = sum(getattr(skill, "importance", 5.0) for skill in matched_required)
            coverage_score = sum_matched_importance / sum_importance

        # 5. critical_failures = missing_required
        critical_failures = list(missing_required)

        return RequirementMatchResult(
            matched_required=matched_required,
            missing_required=missing_required,
            matched_preferred=matched_preferred,
            missing_preferred=missing_preferred,
            coverage_score=coverage_score,
            critical_failures=critical_failures,
        )
