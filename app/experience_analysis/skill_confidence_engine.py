"""
Skill confidence engine for orchestrating evidence and signal calculators into final confidence profiles.
"""

import logging
from typing import Dict, Any
from app.models.resume_schema import ResumeProfile
from app.experience_analysis.models import SkillConfidenceProfile
from app.experience_analysis.evidence_collector import SkillEvidenceCollector
from app.experience_analysis.complexity_calculator import ComplexityCalculator
from app.experience_analysis.signal_calculator import SignalCalculator
from app.experience_analysis.confidence_calculator import SkillConfidenceCalculator


# Setup logger
logger = logging.getLogger("app.experience_analysis.skill_confidence_engine")


class SkillConfidenceEngine:
    """
    Orchestrator to calculate comprehensive Skill Confidence Profiles for candidate skills.
    """

    def __init__(
        self,
        evidence_collector: SkillEvidenceCollector,
        complexity_calculator: ComplexityCalculator,
        signal_calculator: SignalCalculator,
        confidence_calculator: SkillConfidenceCalculator
    ) -> None:
        """
        Initializes the SkillConfidenceEngine with its required component dependencies.

        Args:
            evidence_collector: Gathers raw evidence counts and occurrences.
            complexity_calculator: Computes project-based technical complexity scores.
            signal_calculator: Generates normalized signals (0.0 to 1.0) for each evidence term.
            confidence_calculator: Aggregates signals into final scores and classifications.
        """
        self._evidence_collector = evidence_collector
        self._complexity_calculator = complexity_calculator
        self._signal_calculator = signal_calculator
        self._confidence_calculator = confidence_calculator

    def analyze(self, profile: ResumeProfile) -> Dict[str, SkillConfidenceProfile]:
        """
        Runs the end-to-end skill confidence evaluation pipeline on a ResumeProfile.

        Args:
            profile: Candidate ResumeProfile object.

        Returns:
            A dictionary mapping skill names to their computed SkillConfidenceProfile.
        """
        logger.info("Starting Skill Confidence Engine analysis.")

        if not profile or not profile.skills:
            logger.info("Resume profile or skills list is empty. Returning empty confidence profiles.")
            return {}

        # 1. Collect raw evidence (handles safe processing and case-insensitive skill deduplication)
        evidence_map = self._evidence_collector.collect(profile)
        if not evidence_map:
            logger.info("No skill evidence collected. Returning empty confidence profiles.")
            return {}

        # 2. Compute dynamic normalization factor (max mentions) once
        max_skill_mentions_in_resume = max(
            (ev.skill_mentions for ev in evidence_map.values()),
            default=0
        )
        logger.info(f"Max skill mentions normalized across resume: {max_skill_mentions_in_resume}")

        results: Dict[str, SkillConfidenceProfile] = {}

        # 3. Generate signals, scores, and explainability summaries for each unique skill
        for skill, evidence in evidence_map.items():
            # Calculate normalized signal scores (0.0 to 1.0)
            project_signal = self._signal_calculator.calculate_project_signal(evidence, profile)
            professional_signal = self._signal_calculator.calculate_professional_signal(evidence)
            depth_signal = self._signal_calculator.calculate_depth_signal(evidence, max_skill_mentions_in_resume)
            achievement_signal = self._signal_calculator.calculate_achievement_signal(evidence)
            
            # Calculate complexity signal from projects
            complexity_signal = self._complexity_calculator.get_skill_complexity(skill, profile)

            # Combine signals to calculate confidence score and level category
            confidence_score, confidence_level = self._confidence_calculator.calculate(
                professional_signal=professional_signal,
                depth_signal=depth_signal,
                complexity_signal=complexity_signal
            )

            # Retrieve recruiter-friendly skill tier classification
            skill_tier = self._confidence_calculator.get_skill_tier(confidence_score)

            # Build enhanced explainability metadata
            evidence_summary = {
                "project_count": evidence.project_count,
                "projects_used_in": evidence.projects,
                "direct_mentions": evidence.direct_mentions,
                "supporting_technologies": evidence.dependency_sources,
                "professional_roles": evidence.roles
            }

            # Build profile
            results[skill] = SkillConfidenceProfile(
                skill=skill,
                professional_signal=professional_signal,
                depth_signal=depth_signal,
                complexity_signal=complexity_signal,
                confidence_score=confidence_score,
                confidence_level=confidence_level.value,
                skill_tier=skill_tier,
                evidence_summary=evidence_summary
            )



        logger.info(f"Skill Confidence Engine analysis complete. Profiles generated for {len(results)} skill(s).")
        return results
