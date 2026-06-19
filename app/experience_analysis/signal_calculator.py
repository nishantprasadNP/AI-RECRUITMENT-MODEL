"""
Signal calculator for generating normalized evidence signals for skills.
"""

import logging
from app.schemas.resume_schema import ResumeProfile
from app.experience_analysis.models import SkillEvidence


# Setup logger
logger = logging.getLogger("app.experience_analysis.signal_calculator")


# Normalization constants to avoid magic numbers
ACHIEVEMENT_DENOMINATOR = 5.0
SIGNAL_MIN = 0.0
SIGNAL_MAX = 1.0

INTERNSHIP_SIGNAL = 0.5
FULL_TIME_SIGNAL = 1.0


# Keyword configuration for internship classification
INTERNSHIP_KEYWORDS = {
    "intern",
    "internship",
    "co-op",
    "trainee",
    "apprentice",
    "student",
    "graduate trainee",
    "summer intern",
    "research intern",
    "teaching assistant"
}


class SignalCalculator:
    """
    Computes normalized evidence signals for skills using candidate profile data and collected evidence.
    """

    def calculate_project_signal(self, evidence: SkillEvidence, profile: ResumeProfile) -> float:
        """
        Measures how broadly a skill is used across candidate projects.

        Formula:
            project_signal = projects_with_skill / total_projects

        Args:
            evidence: SkillEvidence object containing project details.
            profile: Candidate ResumeProfile object.

        Returns:
            A project signal float clamped between 0.0 and 1.0.
        """
        if not profile or not profile.projects:
            logger.info("No projects found in candidate profile. Returning project signal 0.0.")
            return SIGNAL_MIN

        total_projects = len(profile.projects)
        if total_projects == 0:
            logger.info("Total projects count is 0. Returning project signal 0.0.")
            return SIGNAL_MIN

        projects_with_skill = evidence.project_count
        signal = projects_with_skill / total_projects
        
        final_signal = min(max(signal, SIGNAL_MIN), SIGNAL_MAX)
        logger.debug(f"Project signal calculated: {final_signal} ({projects_with_skill}/{total_projects})")
        return final_signal

    def calculate_professional_signal(self, evidence: SkillEvidence) -> float:
        """
        Measures professional evidence of skill usage.

        Args:
            evidence: SkillEvidence object containing roles and professional usage status.

        Returns:
            0.0 if no professional usage or empty roles.
            0.5 if all matching roles are detected as internships.
            1.0 if at least one matching role is detected as a full-time role.
        """
        if not evidence or not evidence.professional_usage or not evidence.roles:
            logger.debug("No professional usage or empty roles found. Returning professional signal 0.0.")
            return SIGNAL_MIN

        is_internship_only = True
        for role in evidence.roles:
            if not role:
                continue
            
            role_lower = role.lower()
            # Case-insensitive check against internship keywords
            has_intern_keyword = any(kw in role_lower for kw in INTERNSHIP_KEYWORDS)
            if not has_intern_keyword:
                is_internship_only = False
                break

        final_signal = INTERNSHIP_SIGNAL if is_internship_only else FULL_TIME_SIGNAL
        logger.debug(f"Professional signal calculated: {final_signal} (Roles checked: {evidence.roles})")
        return final_signal

    def calculate_depth_signal(self, evidence: SkillEvidence, max_skill_mentions_in_resume: int) -> float:
        """
        Measures how strongly the skill appears throughout the candidate's resume,
        incorporating both direct mentions and graph-aware dependency mentions.

        Formula:
            effective_mentions = direct_mentions + dependency_mentions
            depth_signal = effective_mentions / max_skill_mentions_in_resume

        Args:
            evidence: SkillEvidence object containing mentions counts.
            max_skill_mentions_in_resume: Dynamic normalization factor (highest skill mention count in resume).

        Returns:
            A depth signal float clamped between 0.0 and 1.0.
        """
        if not evidence or max_skill_mentions_in_resume <= 0:
            logger.info("Invalid normalization parameter or empty evidence. Returning depth signal 0.0.")
            return SIGNAL_MIN

        effective_mentions = evidence.direct_mentions + evidence.dependency_mentions
        signal = effective_mentions / max_skill_mentions_in_resume
        
        final_signal = min(max(signal, SIGNAL_MIN), SIGNAL_MAX)
        logger.debug(f"Depth signal calculated: {final_signal} ({effective_mentions}/{max_skill_mentions_in_resume})")
        return final_signal


    def calculate_achievement_signal(self, evidence: SkillEvidence) -> float:
        """
        Measures evidence of the skill from candidate achievements.

        Formula:
            achievement_signal = achievement_mentions / 5

        Args:
            evidence: SkillEvidence object containing achievement details.

        Returns:
            An achievement signal float clamped between 0.0 and 1.0.
        """
        if not evidence or evidence.achievement_mentions <= 0:
            logger.debug("No achievement mentions. Returning achievement signal 0.0.")
            return SIGNAL_MIN

        signal = evidence.achievement_mentions / ACHIEVEMENT_DENOMINATOR
        
        final_signal = min(max(signal, SIGNAL_MIN), SIGNAL_MAX)
        logger.debug(f"Achievement signal calculated: {final_signal} ({evidence.achievement_mentions}/5)")
        return final_signal
