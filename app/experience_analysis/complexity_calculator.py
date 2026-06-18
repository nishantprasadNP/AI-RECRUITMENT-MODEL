"""
Complexity calculator for evaluating technical project complexity and skill signals.
"""

import re
import logging
from typing import List, Set, Optional
from app.models.resume_schema import ResumeProfile, Project


# Setup logger
logger = logging.getLogger("app.experience_analysis.complexity_calculator")


# Scoring constants to avoid magic numbers
BASE_SCORE = 2.0
MAX_CATEGORY_BONUS = 3.0
MAX_DOMAIN_BONUS = 2.0
MAX_DEPLOYMENT_BONUS = 2.0
MAX_DESCRIPTION_BONUS = 1.0
MAX_ADVANCED_BONUS = 1.0
MAX_COMPLEXITY_SCORE = 10.0

DESCRIPTION_INDICATOR_WEIGHT = 0.25


# Categorization mappings
TECHNOLOGY_CATEGORIES = {
    # Frontend
    "react": "FRONTEND",
    "react.js": "FRONTEND",
    "angular": "FRONTEND",
    "vue": "FRONTEND",
    "html": "FRONTEND",
    "css": "FRONTEND",
    "javascript": "FRONTEND",
    "typescript": "FRONTEND",
    "next.js": "FRONTEND",
    
    # Backend
    "django": "BACKEND",
    "flask": "BACKEND",
    "fastapi": "BACKEND",
    "node.js": "BACKEND",
    "spring boot": "BACKEND",
    "express": "BACKEND",
    "go": "BACKEND",
    "golang": "BACKEND",
    "python": "BACKEND",
    "java": "BACKEND",
    "c#": "BACKEND",
    "ruby": "BACKEND",
    "php": "BACKEND",
    
    # Database
    "mongodb": "DATABASE",
    "postgresql": "DATABASE",
    "postgres": "DATABASE",
    "mysql": "DATABASE",
    "sqlite": "DATABASE",
    "redis": "DATABASE",
    "sql": "DATABASE",
    "cassandra": "DATABASE",
    "dynamodb": "DATABASE",
    "oracle": "DATABASE",
    
    # Machine Learning
    "scikit-learn": "MACHINE_LEARNING",
    "pytorch": "MACHINE_LEARNING",
    "tensorflow": "MACHINE_LEARNING",
    "keras": "MACHINE_LEARNING",
    "numpy": "MACHINE_LEARNING",
    "pandas": "MACHINE_LEARNING",
    "spacy": "MACHINE_LEARNING",
    "huggingface": "MACHINE_LEARNING",
    "cnn": "MACHINE_LEARNING",
    "yolo": "MACHINE_LEARNING",
    "transformer": "MACHINE_LEARNING",
    "deep learning": "MACHINE_LEARNING",
    
    # Cloud
    "aws": "CLOUD",
    "azure": "CLOUD",
    "gcp": "CLOUD",
    "google cloud": "CLOUD",
    
    # DevOps
    "docker": "DEVOPS",
    "kubernetes": "DEVOPS",
    "k8s": "DEVOPS",
    "terraform": "DEVOPS",
    "ci/cd": "DEVOPS",
    "jenkins": "DEVOPS",
    "ansible": "DEVOPS",
    
    # Distributed Systems
    "kafka": "DISTRIBUTED_SYSTEMS",
    "rabbitmq": "DISTRIBUTED_SYSTEMS",
    "spark": "DISTRIBUTED_SYSTEMS",
    "hadoop": "DISTRIBUTED_SYSTEMS",
    "grpc": "DISTRIBUTED_SYSTEMS"
}

HIGH_COMPLEXITY_KEYWORDS = [
    "distributed",
    "concurrency",
    "parallelism",
    "scalable",
    "streaming",
    "pipeline",
    "machine learning",
    "deep learning",
    "inference",
    "training",
    "vector database",
    "retrieval"
]

DEPLOYMENT_TECHNOLOGIES = [
    "aws",
    "azure",
    "gcp",
    "docker",
    "kubernetes",
    "terraform",
    "ci/cd"
]

ENGINEERING_INDICATORS = [
    "designed",
    "implemented",
    "optimized",
    "deployed",
    "architected",
    "scalable",
    "integrated",
    "pipeline",
    "microservice",
    "automation"
]

ADVANCED_SKILLS = {
    "cnn",
    "yolo",
    "transformer",
    "computer vision",
    "deep learning",
    "distributed systems"
}


class ComplexityCalculator:
    """
    Evaluates projects and skills to calculate technical complexity scores and normalized signals.
    """

    def _get_project_categories(self, technologies: List[str]) -> Set[str]:
        """
        Identifies unique technology categories from a list of technology names.

        Args:
            technologies: List of technology strings.

        Returns:
            A set of matched category strings (e.g. FRONTEND, BACKEND, DATABASE).
        """
        categories: Set[str] = set()
        if not technologies:
            return categories

        for tech in technologies:
            if not tech:
                continue
            cleaned = tech.strip().lower()
            # 1. Exact lookup
            if cleaned in TECHNOLOGY_CATEGORIES:
                categories.add(TECHNOLOGY_CATEGORIES[cleaned])
            else:
                # 2. Substring lookup
                for key, category in TECHNOLOGY_CATEGORIES.items():
                    if key in cleaned:
                        categories.add(category)
                        break

        return categories

    def _contains_skill(self, skill: str, text: str) -> bool:
        """
        Checks if a skill is present in a text string using boundary-safe regex matching.

        Args:
            skill: Raw skill string.
            text: Text string to search.

        Returns:
            True if the skill matches, False otherwise.
        """
        if not skill or not text:
            return False

        escaped = re.escape(skill)
        pattern = escaped
        if skill[0].isalnum():
            pattern = r"\b" + pattern
        if skill[-1].isalnum():
            pattern = pattern + r"\b"

        return bool(re.search(pattern, text, re.IGNORECASE))

    def calculate_project_complexity(self, project: Project) -> float:
        """
        Calculates a project's complexity score on a scale from 1.0 to 10.0.

        Args:
            project: Project object to evaluate.

        Returns:
            A complexity score float between 1.0 and 10.0.
        """
        if not project:
            logger.warning("Attempted to calculate complexity for an empty project.")
            return 1.0

        description = project.description or ""
        desc_lower = description.lower()
        technologies = project.technologies or []
        techs_lower = [t.lower().strip() for t in technologies if t]

        # 1. Base Score
        score = BASE_SCORE

        # 2. Technology Category Bonus
        categories = self._get_project_categories(technologies)
        category_bonus = min(float(len(categories)), MAX_CATEGORY_BONUS)
        score += category_bonus

        # 3. Domain Complexity Bonus
        domain_matches = sum(1 for kw in HIGH_COMPLEXITY_KEYWORDS if kw in desc_lower)
        domain_bonus = min(float(domain_matches), MAX_DOMAIN_BONUS)
        score += domain_bonus

        # 4. Deployment Bonus
        deployment_matches = 0
        for dep in DEPLOYMENT_TECHNOLOGIES:
            if dep in desc_lower or any(dep in t for t in techs_lower):
                deployment_matches += 1
        deployment_bonus = min(float(deployment_matches), MAX_DEPLOYMENT_BONUS)
        score += deployment_bonus

        # 5. Description Quality Bonus
        desc_matches = sum(1 for ind in ENGINEERING_INDICATORS if ind in desc_lower)
        description_bonus = min(desc_matches * DESCRIPTION_INDICATOR_WEIGHT, MAX_DESCRIPTION_BONUS)
        score += description_bonus

        # 6. Advanced Skill Bonus
        has_advanced = False
        for adv in ADVANCED_SKILLS:
            if adv in desc_lower or any(adv in t for t in techs_lower):
                has_advanced = True
                break
        advanced_bonus = MAX_ADVANCED_BONUS if has_advanced else 0.0
        score += advanced_bonus

        # Final Capped Score
        final_score = min(score, MAX_COMPLEXITY_SCORE)
        
        logger.debug(
            f"Project '{project.name}' details - Category Bonus: {category_bonus}, "
            f"Domain Bonus: {domain_bonus}, Deployment Bonus: {deployment_bonus}, "
            f"Desc Bonus: {description_bonus}, Advanced Bonus: {advanced_bonus}. "
            f"Final Score: {final_score}"
        )
        
        return final_score

    def get_skill_complexity(self, skill: str, profile: ResumeProfile) -> float:
        """
        Generates a normalized complexity signal score for a skill based on the
        most complex project matching the skill.

        Args:
            skill: Raw skill string to analyze.
            profile: The parsed ResumeProfile object.

        Returns:
            A normalized complexity signal score float between 0.0 and 1.0.
        """
        if not profile or not profile.projects:
            logger.info("No projects found in candidate profile. Returning complexity signal 0.0.")
            return 0.0

        matching_projects: List[Project] = []
        for p in profile.projects:
            if not p:
                continue
            
            name = p.name or ""
            desc = p.description or ""
            techs = p.technologies or []

            # Exact, boundary-safe case-insensitive match on name, description, or tech list
            name_match = self._contains_skill(skill, name)
            desc_match = self._contains_skill(skill, desc)
            tech_match = any(self._contains_skill(skill, t) for t in techs if t)

            if name_match or desc_match or tech_match:
                matching_projects.append(p)

        if not matching_projects:
            logger.info(f"Skill '{skill}' not found in any projects. Returning complexity signal 0.0.")
            return 0.0

        # Calculate complexity scores and select the highest
        complexity_scores = [self.calculate_project_complexity(p) for p in matching_projects]
        highest_complexity = max(complexity_scores)

        # Normalize score
        complexity_signal = highest_complexity / MAX_COMPLEXITY_SCORE
        
        logger.info(
            f"Skill '{skill}' matched {len(matching_projects)} project(s). "
            f"Highest complexity: {highest_complexity}. Normalized signal: {complexity_signal}"
        )
        
        return min(max(complexity_signal, 0.0), 1.0)
