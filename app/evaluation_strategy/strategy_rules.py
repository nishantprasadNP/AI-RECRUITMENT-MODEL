"""
Library of predefined and extensible evaluation strategy rules in ARIS V2.
"""

from typing import Dict, Any, List
from pydantic import ValidationError
from app.evaluation_strategy.models import EvaluationStrategy
from app.evaluation_strategy.exceptions import InvalidStrategyConfigError, StrategyNotFoundError

# Standard predefined evaluation strategy profiles
DEFAULT_PROFILES: Dict[str, Dict[str, Any]] = {
    "intern_backend": {
        "evaluation_profile": "intern_backend",
        "strictness_level": "low",
        "component_weights": {
            "skills": 0.30,
            "projects": 0.30,
            "experience": 0.15,
            "hard_requirements": 0.15,
            "achievements": 0.10
        },
        "minimum_skill_confidence": 30.0,
        "hard_requirement_tolerance": 50.0
    },
    "new_grad_backend": {
        "evaluation_profile": "new_grad_backend",
        "strictness_level": "low",
        "component_weights": {
            "skills": 0.30,
            "projects": 0.30,
            "experience": 0.15,
            "hard_requirements": 0.15,
            "achievements": 0.10
        },
        "minimum_skill_confidence": 40.0,
        "hard_requirement_tolerance": 50.0
    },
    "mid_backend": {
        "evaluation_profile": "mid_backend",
        "strictness_level": "medium",
        "component_weights": {
            "skills": 0.25,
            "projects": 0.25,
            "experience": 0.25,
            "hard_requirements": 0.15,
            "achievements": 0.10
        },
        "minimum_skill_confidence": 60.0,
        "hard_requirement_tolerance": 50.0
    },
    "senior_backend": {
        "evaluation_profile": "senior_backend",
        "strictness_level": "high",
        "component_weights": {
            "skills": 0.15,
            "projects": 0.20,
            "experience": 0.35,
            "hard_requirements": 0.15,
            "leadership": 0.15
        },
        "minimum_skill_confidence": 80.0,
        "hard_requirement_tolerance": 50.0
    },
    "staff_backend": {
        "evaluation_profile": "staff_backend",
        "strictness_level": "high",
        "component_weights": {
            "skills": 0.10,
            "projects": 0.15,
            "experience": 0.40,
            "hard_requirements": 0.15,
            "leadership": 0.20
        },
        "minimum_skill_confidence": 85.0,
        "hard_requirement_tolerance": 50.0
    },
    "intern_ml": {
        "evaluation_profile": "intern_ml",
        "strictness_level": "low",
        "component_weights": {
            "skills": 0.30,
            "projects": 0.30,
            "experience": 0.15,
            "hard_requirements": 0.15,
            "achievements": 0.10
        },
        "minimum_skill_confidence": 35.0,
        "hard_requirement_tolerance": 50.0
    },
    "mid_ml": {
        "evaluation_profile": "mid_ml",
        "strictness_level": "medium",
        "component_weights": {
            "skills": 0.25,
            "projects": 0.25,
            "experience": 0.25,
            "hard_requirements": 0.15,
            "achievements": 0.10
        },
        "minimum_skill_confidence": 65.0,
        "hard_requirement_tolerance": 50.0
    },
    "senior_ml": {
        "evaluation_profile": "senior_ml",
        "strictness_level": "high",
        "component_weights": {
            "skills": 0.15,
            "projects": 0.20,
            "experience": 0.30,
            "hard_requirements": 0.15,
            "leadership": 0.10,
            "achievements": 0.10
        },
        "minimum_skill_confidence": 80.0,
        "hard_requirement_tolerance": 50.0
    },
    "staff_ml": {
        "evaluation_profile": "staff_ml",
        "strictness_level": "high",
        "component_weights": {
            "skills": 0.10,
            "projects": 0.15,
            "experience": 0.35,
            "hard_requirements": 0.15,
            "leadership": 0.15,
            "achievements": 0.10
        },
        "minimum_skill_confidence": 85.0,
        "hard_requirement_tolerance": 50.0
    }
}


class StrategyRuleLibrary:
    """
    Manages pre-configured evaluation strategies and rules.
    Allows dynamic registration and updating of rules.
    """
    def __init__(self) -> None:
        self._rules: Dict[str, Dict[str, Any]] = dict(DEFAULT_PROFILES)

    def register_profile(self, profile_name: str, config: Dict[str, Any]) -> None:
        """
        Dynamically registers or updates an evaluation strategy profile.

        Args:
            profile_name: Name of the strategy profile.
            config: A dictionary matching the EvaluationStrategy schema.

        Raises:
            InvalidStrategyConfigError: If the configuration does not validate.
        """
        try:
            EvaluationStrategy(**config)
        except ValidationError as e:
            raise InvalidStrategyConfigError(
                f"Invalid strategy configuration for profile '{profile_name}': {e}"
            ) from e

        self._rules[profile_name] = config

    def get_profile_config(self, profile_name: str) -> Dict[str, Any]:
        """
        Retrieves the raw configuration dictionary for a profile.

        Args:
            profile_name: Name of the strategy profile to fetch.

        Returns:
            Dict containing configuration options.

        Raises:
            StrategyNotFoundError: If the profile is not registered.
        """
        if profile_name not in self._rules:
            raise StrategyNotFoundError(f"Strategy profile '{profile_name}' not found in rule library.")
        return self._rules[profile_name]

    def has_profile(self, profile_name: str) -> bool:
        """
        Checks if a profile name exists in the library.
        """
        return profile_name in self._rules

    def list_profiles(self) -> List[str]:
        """
        Returns a list of all registered profile names.
        """
        return list(self._rules.keys())
