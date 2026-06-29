"""
Skill Gap Analysis Engine for Phase 12 in ARIS V2.
"""

import logging
from app.schemas.job_schema import JobProfile
from app.hard_requirements.models import HardRequirementResult
from app.experience_analysis.models import SkillConfidenceProfile
from app.skill_gap.models import SkillGapResult
from app.skill_gap.exceptions import GapAnalysisError

logger = logging.getLogger("aris.skill_gap.engine")


class SkillGapEngine:
    """
    Engine to identify skill gaps and generate recommendations by aggregating
    data from job profiles, hard requirement results, and skill confidence profiles.
    """

    def __init__(self) -> None:
        pass

    def analyze_gaps(
        self,
        job_profile: JobProfile,
        hard_requirement_result: HardRequirementResult,
        confidence_profiles: dict[str, SkillConfidenceProfile]
    ) -> SkillGapResult:
        """
        Analyzes the gaps between the candidate's skills and the job profile.

        Args:
            job_profile: The target job description profile.
            hard_requirement_result: The result of matching hard requirements.
            confidence_profiles: A dictionary mapping skill names to their confidence profiles.

        Returns:
            A SkillGapResult object detailing missing, weak, strong skills and recommendations.

        Raises:
            GapAnalysisError: If any of the inputs are None or if gap analysis fails.
        """
        if job_profile is None:
            raise GapAnalysisError("job_profile cannot be None.")
        if hard_requirement_result is None:
            raise GapAnalysisError("hard_requirement_result cannot be None.")
        if confidence_profiles is None:
            raise GapAnalysisError("confidence_profiles cannot be None.")

        try:
            logger.info("Starting skill gap analysis...")

            # 1. Missing required skills (direct population)
            missing_required = list(hard_requirement_result.missing_required)

            # 2. Missing preferred skills (direct population)
            missing_preferred = list(hard_requirement_result.missing_preferred)

            # 3. Weak skills (confidence_score < 50)
            weak_skills = []
            # 4. Strong skills (confidence_score >= 75)
            strong_skills = []

            for profile in confidence_profiles.values():
                if profile.confidence_score < 50.0:
                    weak_skills.append(profile.skill)
                elif profile.confidence_score >= 75.0:
                    strong_skills.append(profile.skill)

            # 5. Improvement Areas / Recommendations
            improvement_areas = []

            # Mapping rules for recommendations (case-insensitive keys)
            recommendation_rules = {
                "kafka": "Gain experience with Kafka",
                "docker": "Build deployment projects using Docker",
                "aws": "Gain cloud deployment experience",
                "kubernetes": "Gain container orchestration experience",
                "terraform": "Learn infrastructure as code practices"
            }

            def get_recommendation(skill: str) -> str:
                skill_lower = skill.strip().lower()
                if skill_lower in recommendation_rules:
                    return recommendation_rules[skill_lower]
                return f"Improve proficiency in {skill}"

            # Generate recommendations in order: missing required, missing preferred, weak skills
            for skill in missing_required:
                improvement_areas.append(get_recommendation(skill))

            for skill in missing_preferred:
                improvement_areas.append(get_recommendation(skill))

            for skill in weak_skills:
                improvement_areas.append(get_recommendation(skill))

            # Avoid duplicates while preserving insertion order
            improvement_areas = list(dict.fromkeys(improvement_areas))

            # 6. Overall Gap Score
            required_missing_count = len(missing_required)
            preferred_missing_count = len(missing_preferred)
            weak_skill_count = len(weak_skills)

            raw_score = (
                required_missing_count * 0.5 +
                preferred_missing_count * 0.2 +
                weak_skill_count * 0.1
            )
            overall_gap_score = float(round(max(0.0, min(1.0, raw_score)), 4))

            # 7. Decision Summary
            if not missing_required and not weak_skills:
                decision_summary = (
                    "Candidate satisfies all identified requirements and "
                    "demonstrates strong skill evidence."
                )
            elif missing_required and not weak_skills:
                decision_summary = (
                    f"Candidate is missing required skills: {', '.join(missing_required)}."
                )
            elif not missing_required and weak_skills:
                decision_summary = (
                    f"Candidate meets requirements but has weak evidence in {', '.join(weak_skills)}."
                )
            else:
                decision_summary = (
                    f"Candidate satisfies most requirements but lacks {', '.join(missing_required)} "
                    f"and has weak {', '.join(weak_skills)} evidence."
                )

            # Build and return the result Pydantic model
            result = SkillGapResult(
                missing_required_skills=missing_required,
                missing_preferred_skills=missing_preferred,
                weak_skills=weak_skills,
                strong_skills=strong_skills,
                improvement_areas=improvement_areas,
                overall_gap_score=overall_gap_score,
                decision_summary=decision_summary
            )

            logger.info("Skill gap analysis completed successfully.")
            return result

        except Exception as e:
            if isinstance(e, GapAnalysisError):
                raise
            raise GapAnalysisError(f"Error occurred during skill gap analysis: {e}") from e
