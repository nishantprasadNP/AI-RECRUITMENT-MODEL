"""
Normalized score calculators (0-100) for candidate scoring components in ARIS V2.
"""

import re
import logging
from typing import Dict, List, Any, Optional
from app.schemas.resume_schema import ResumeProfile
from app.achievement_analysis.models import AchievementProfile
from app.experience_analysis.models import SkillConfidenceProfile

logger = logging.getLogger("aris.candidate_scoring.calculators")


def parse_duration_to_years(duration_str: Optional[str]) -> float:
    """
    Parses a duration string (e.g. '2 years', '6 months', '1 year 6 months')
    and returns the equivalent float value in years.
    """
    if not duration_str:
        return 0.0
    
    duration_str = duration_str.lower()
    years = 0.0
    
    # Match years patterns: e.g. "2 years", "1.5 yrs", "1 year"
    year_match = re.search(r"(\d+(\.\d+)?)\s*(year|yr)", duration_str)
    if year_match:
        years += float(year_match.group(1))
        
    # Match months patterns: e.g. "6 months", "3 mos", "1 month"
    month_match = re.search(r"(\d+(\.\d+)?)\s*(month|mo)", duration_str)
    if month_match:
        years += float(month_match.group(1)) / 12.0
        
    # Fallback if no keywords matched but digits are present, assume years
    if years == 0.0:
        digits_match = re.search(r"(\d+(\.\d+)?)", duration_str)
        if digits_match:
            years += float(digits_match.group(1))
            
    return years


class ComponentScoreCalculators:
    """
    Utility calculators that compute normalized (0-100) scores for different candidate areas.
    """

    @staticmethod
    def calculate_semantic_score(semantic_score: float) -> float:
        """
        Calculates the normalized Semantic Alignment score.
        """
        # Bounded cosine similarity scaled to [0, 100]
        normalized = max(0.0, min(1.0, float(semantic_score))) * 100.0
        return round(normalized, 1)

    @staticmethod
    def calculate_skills_score(
        confidence_profiles: Dict[str, SkillConfidenceProfile],
        required_skills: List[str]
    ) -> float:
        """
        Calculates the normalized Skill Strength score based on candidate confidence
        profiles for required skills. Missing required skills are penalized with 0.0.
        """
        if not confidence_profiles:
            return 0.0

        # Clean/normalize required skills for comparison
        req_clean = [s.lower().strip() for s in required_skills if s and s.strip()]

        if not req_clean:
            # Fallback to averaging all skills possessed by candidate if no requirements are specified
            scores = [p.confidence_score for p in confidence_profiles.values()]
            if not scores:
                return 0.0
            return round(sum(scores) / len(scores), 1)

        # Average the confidence scores of the required skills
        total_score = 0.0
        # Map lowercased candidate skill names to their profiles for robust lookup
        profile_lookup = {k.lower().strip(): p for k, p in confidence_profiles.items()}

        for skill in req_clean:
            if skill in profile_lookup:
                total_score += profile_lookup[skill].confidence_score
            else:
                # Skill is missing: contributes 0.0 to the average
                total_score += 0.0

        normalized = total_score / len(req_clean)
        return round(normalized, 1)

    @staticmethod
    def calculate_experience_score(
        resume_profile: ResumeProfile,
        experience_required: Optional[int]
    ) -> float:
        """
        Calculates the normalized Experience Quality score by comparing candidate's
        parsed years of experience against the job's experience requirements.
        """
        if not resume_profile or not resume_profile.experience:
            return 0.0

        # Calculate total years of experience
        total_years = 0.0
        for exp in resume_profile.experience:
            duration_str = getattr(exp, "duration", None)
            total_years += parse_duration_to_years(duration_str)

        # Fallback if no durations are parsed but items exist: assume 1 year per entry
        if total_years == 0.0 and len(resume_profile.experience) > 0:
            total_years = float(len(resume_profile.experience))

        required_years = max(1.0, float(experience_required or 1.0))
        ratio = total_years / required_years
        normalized = min(100.0, ratio * 100.0)
        return round(normalized, 1)

    @staticmethod
    def calculate_achievements_score(achievement_profile: AchievementProfile) -> float:
        """
        Calculates the normalized Achievement Impact score.
        """
        if not achievement_profile:
            return 0.0
        # Scales 0.0-10.0 score to 0.0-100.0
        normalized = max(0.0, min(10.0, achievement_profile.achievement_score)) * 10.0
        return round(normalized, 1)

    @staticmethod
    def calculate_projects_score(
        resume_profile: ResumeProfile,
        required_skills: List[str]
    ) -> float:
        """
        Calculates the normalized Projects Strength score based on project quantity
        and technologies matching the job's required skills.
        """
        if not resume_profile or not resume_profile.projects:
            return 0.0

        total_projects = len(resume_profile.projects)
        req_clean = {s.lower().strip() for s in required_skills if s and s.strip()}

        relevant_projects_count = 0
        for proj in resume_profile.projects:
            techs = {t.lower().strip() for t in (proj.technologies or []) if t}
            if req_clean & techs:
                relevant_projects_count += 1

        # Score consists of 20% per project + 20% per relevant project, capped at 100.0
        score = (total_projects * 20.0) + (relevant_projects_count * 20.0)
        normalized = min(100.0, score)
        return round(normalized, 1)

    @staticmethod
    def calculate_leadership_score(
        resume_profile: ResumeProfile,
        achievement_profile: AchievementProfile
    ) -> float:
        """
        Calculates the normalized Leadership Strength score based on candidate experience
        lead roles and achievements.
        """
        if not resume_profile:
            return 0.0

        # Check if candidate held any explicit lead or manager role
        has_lead_role = False
        lead_keywords = ["lead", "manager", "head", "director", "founder", "president", "cto", "ceo"]
        for exp in resume_profile.experience:
            role = (exp.role or "").lower()
            if any(kw in role for kw in lead_keywords):
                has_lead_role = True
                break

        # Check achievement profile for leadership signals
        achievement_leadership_count = 0
        if achievement_profile and achievement_profile.leadership:
            achievement_leadership_count = len(achievement_profile.leadership)

        if has_lead_role:
            return 100.0
        
        # Scale based on leadership achievements: 50 points per achievement
        score = achievement_leadership_count * 50.0
        normalized = min(100.0, score)
        return round(normalized, 1)
