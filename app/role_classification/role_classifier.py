"""
Role Classification Engine for ARIS.
Classifies job descriptions into role families, specializations, seniority levels,
and evaluation profiles using rule-based mappings.
"""

import logging
from app.schemas.job_schema import JobProfile
from app.role_classification.models import RoleProfile
from app.role_classification.exceptions import (
    RoleClassificationError,
    RoleFamilyDetectionError,
    SpecializationDetectionError,
    SeniorityDetectionError,
)
from app.role_classification.role_rules import (
    ROLE_FAMILY_KEYWORDS,
    SPECIALIZATION_KEYWORDS,
    BACKEND_SKILLS,
    FRONTEND_SKILLS,
    ML_SKILLS,
    DATA_ENGINEERING_SKILLS,
    DEVOPS_SKILLS,
    SECURITY_SKILLS,
)

logger = logging.getLogger("resume_parser.role_classifier")

# Map role families to their allowed specializations
FAMILY_TO_SPECIALIZATIONS = {
    "software_engineering": [
        "backend_engineer",
        "frontend_engineer",
        "fullstack_engineer",
        "mobile_engineer",
    ],
    "data_ai": [
        "ml_engineer",
        "data_engineer",
        "data_scientist",
        "ai_research_engineer",
    ],
    "cloud_engineering": [
        "devops_engineer",
        "cloud_engineer",
    ],
    "security_engineering": [
        "security_engineer",
    ],
    "product_management": [
        "product_manager",
    ],
}

# Map specializations to their skill sets for voting
SPECIALIZATION_SKILL_SETS = {
    "backend_engineer": set(BACKEND_SKILLS),
    "frontend_engineer": set(FRONTEND_SKILLS),
    "fullstack_engineer": set(BACKEND_SKILLS + FRONTEND_SKILLS),
    "mobile_engineer": {
        "swift", "kotlin", "objective-c", "android", "ios", "flutter",
        "react native", "cocoapods", "gradle", "mobile", "xcode"
    },
    "ml_engineer": set(ML_SKILLS),
    "data_engineer": set(DATA_ENGINEERING_SKILLS),
    "data_scientist": set(ML_SKILLS) | {
        "r", "statistics", "statistical", "matlab", "tableau", "sas",
        "data analysis", "analytics"
    },
    "ai_research_engineer": set(ML_SKILLS) | {
        "research", "paper", "arxiv", "publication", "novel", "nlp", "transformers"
    },
    "devops_engineer": set(DEVOPS_SKILLS),
    "cloud_engineer": set(DEVOPS_SKILLS) | {
        "cloud", "aws", "azure", "gcp", "networking", "vpc", "iam"
    },
    "security_engineer": set(SECURITY_SKILLS),
    "product_manager": {
        "agile", "scrum", "roadmap", "jira", "product owner", "requirements",
        "stakeholder", "backlog", "product management", "product strategy"
    },
}

# Default specializations for fallback/tie cases within a family
DEFAULT_SPECIALIZATIONS = {
    "software_engineering": "backend_engineer",
    "data_ai": "ml_engineer",
    "cloud_engineering": "devops_engineer",
    "security_engineering": "security_engineer",
    "product_management": "product_manager",
}


class RoleClassifier:
    """
    Classifies a JobProfile into a structured RoleProfile using deterministic rules.
    """

    def detect_role_family(self, job: JobProfile) -> str:
        """
        Determines the broad role category based on title, skills, and responsibilities.

        Args:
            job: The JobProfile containing job description details.

        Returns:
            One of: software_engineering, data_ai, cloud_engineering,
                    security_engineering, product_management.

        Raises:
            RoleFamilyDetectionError: If classification fails and no defaults are applied.
        """
        logger.info("Detecting role family")

        # 1. Check Title (Highest Priority)
        title_lower = (job.title or "").lower()
        if title_lower:
            for family, keywords in ROLE_FAMILY_KEYWORDS.items():
                for kw in keywords:
                    if kw in title_lower:
                        logger.info(f"Detected role family '{family}' from title '{job.title}'")
                        return family

        # 2. Check Required and Preferred Skills (Medium Priority)
        family_votes = {fam: 0 for fam in ROLE_FAMILY_KEYWORDS}
        all_skills = [
            s.lower() for s in (job.required_skills or []) + (job.preferred_skills or [])
        ]

        # Define high-level skill families for matching
        family_skills = {
            "software_engineering": set(BACKEND_SKILLS + FRONTEND_SKILLS),
            "data_ai": set(ML_SKILLS + DATA_ENGINEERING_SKILLS),
            "cloud_engineering": set(DEVOPS_SKILLS),
            "security_engineering": set(SECURITY_SKILLS),
            "product_management": SPECIALIZATION_SKILL_SETS["product_manager"],
        }

        for skill in all_skills:
            for family, skill_set in family_skills.items():
                if skill in skill_set or any(s_kw in skill for s_kw in skill_set):
                    family_votes[family] += 1

        # Check if we have a winner from skills
        if max(family_votes.values()) > 0:
            winner = max(family_votes, key=family_votes.get)
            logger.info(f"Detected role family '{winner}' from skills. Votes: {family_votes}")
            return winner

        # 3. Check Responsibility Themes (Lowest Priority)
        themes_lower = [t.lower() for t in job.responsibility_themes or []]
        for theme in themes_lower:
            for family, keywords in ROLE_FAMILY_KEYWORDS.items():
                for kw in keywords:
                    if kw in theme:
                        family_votes[family] += 1

        if max(family_votes.values()) > 0:
            winner = max(family_votes, key=family_votes.get)
            logger.info(f"Detected role family '{winner}' from responsibility themes. Votes: {family_votes}")
            return winner

        # If no signal was found, raise detection error to let classify fallback
        logger.warning("No role family signals found in title, skills, or responsibilities")
        raise RoleFamilyDetectionError("Could not detect role family from job description signals")

    def detect_specialization(self, job: JobProfile, role_family: str) -> str:
        """
        Determines the primary specialization within a role family.

        Args:
            job: The JobProfile containing job description details.
            role_family: The detected broad role family.

        Returns:
            The specialization identifier string.
        """
        logger.info(f"Detecting specialization for family '{role_family}'")

        allowed_specs = FAMILY_TO_SPECIALIZATIONS.get(role_family, [])
        if not allowed_specs:
            logger.warning(f"Unknown role family '{role_family}', cannot detect specialization")
            raise SpecializationDetectionError(f"No specializations allowed for family '{role_family}'")

        spec_votes = {spec: 0 for spec in allowed_specs}

        # 1. Vote based on Title (High Weight)
        title_lower = (job.title or "").lower()
        if title_lower:
            for spec in allowed_specs:
                keywords = SPECIALIZATION_KEYWORDS.get(spec, [])
                for kw in keywords:
                    if kw in title_lower:
                        spec_votes[spec] += 10

        # 2. Vote based on Skills (Required & Preferred)
        all_skills = [
            s.lower() for s in (job.required_skills or []) + (job.preferred_skills or [])
        ]
        for skill in all_skills:
            for spec in allowed_specs:
                skills_def = SPECIALIZATION_SKILL_SETS.get(spec, set())
                if skill in skills_def or any(s_kw in skill for s_kw in skills_def):
                    spec_votes[spec] += 1

        # Check if we have a winner
        if max(spec_votes.values()) > 0:
            winner = max(spec_votes, key=spec_votes.get)
            logger.info(f"Detected specialization '{winner}' with votes: {spec_votes}")
            return winner

        # Default fallback within the family if no signals present
        default_spec = DEFAULT_SPECIALIZATIONS.get(role_family)
        if default_spec:
            logger.info(f"No specialization signals found. Using default '{default_spec}' for family '{role_family}'")
            return default_spec

        raise SpecializationDetectionError(f"Could not determine specialization for family '{role_family}'")

    def detect_seniority(self, job: JobProfile) -> str:
        """
        Determines the seniority level from experience required or seniority level labels.

        Args:
            job: The JobProfile.

        Returns:
            One of: intern, mid_level, senior, staff.
        """
        logger.info("Detecting seniority level")

        # 1. Use seniority_level label if available
        seniority_label = (job.seniority_level or "").lower()
        if seniority_label:
            if any(x in seniority_label for x in ["entry", "intern", "graduate"]):
                return "intern"
            if any(x in seniority_label for x in ["junior", "associate", "mid"]):
                return "mid_level"
            if any(x in seniority_label for x in ["senior", "lead"]):
                return "senior"
            if any(x in seniority_label for x in ["staff", "principal", "architect"]):
                return "staff"

        # 2. Fallback to experience_required (years)
        exp = job.experience_required
        if exp is not None:
            if exp == 0:
                return "intern"
            if 1 <= exp <= 3:
                return "mid_level"
            if 4 <= exp <= 7:
                return "senior"
            if exp >= 8:
                return "staff"

        # 3. Default fallback
        logger.info("No seniority signals found. Defaulting to 'mid_level'")
        return "mid_level"

    def build_evaluation_profile(self, seniority: str, specialization: str) -> str:
        """
        Combines seniority and specialization into a standardized evaluation profile identifier.

        Args:
            seniority: Detected seniority level (intern, mid_level, senior, staff).
            specialization: Detected specialization.

        Returns:
            Standardized evaluation profile identifier string.
        """
        # Map seniority level to evaluation profile prefix
        seniority_map = {
            "intern": "intern",
            "mid_level": "mid",
            "senior": "senior",
            "staff": "staff",
        }
        prefix = seniority_map.get(seniority, "mid")

        # Remove '_engineer' suffix if present
        spec_clean = specialization
        if spec_clean.endswith("_engineer"):
            spec_clean = spec_clean[:-9]  # length of '_engineer' is 9

        profile = f"{prefix}_{spec_clean}"
        logger.info(f"Built evaluation profile: '{profile}' from seniority='{seniority}', spec='{specialization}'")
        return profile

    def classify(self, job: JobProfile) -> RoleProfile:
        """
        Runs the full classification pipeline to output a RoleProfile.
        Catches classification exceptions gracefully and falls back to backend engineer defaults.

        Args:
            job: The job profile contract.

        Returns:
            The derived RoleProfile.
        """
        logger.info("Classifying role")
        try:
            role_family = self.detect_role_family(job)
            specialization = self.detect_specialization(job, role_family)
            seniority = self.detect_seniority(job)
            evaluation_profile = self.build_evaluation_profile(seniority, specialization)

            return RoleProfile(
                role_family=role_family,
                specialization=specialization,
                seniority=seniority,
                evaluation_profile=evaluation_profile,
            )
        except Exception as e:
            logger.error(
                f"Classification failed with error: {str(e)}. Falling back to software engineering backend default.",
                exc_info=True,
            )
            # Safe fallback defaults
            return RoleProfile(
                role_family="software_engineering",
                specialization="backend_engineer",
                seniority="mid_level",
                evaluation_profile="mid_backend",
            )
