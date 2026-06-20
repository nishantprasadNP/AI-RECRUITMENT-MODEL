"""
Evaluation Strategy Engine for Phase 4 in ARIS V2.
"""

import logging
from typing import Optional
from app.role_classification.models import RoleProfile
from app.evaluation_strategy.models import EvaluationStrategy
from app.evaluation_strategy.strategy_rules import StrategyRuleLibrary
from app.evaluation_strategy.exceptions import EvaluationStrategyError, StrategyNotFoundError

logger = logging.getLogger("aris.evaluation_strategy")


class EvaluationStrategyEngine:
    """
    Evaluates a classified RoleProfile to generate a custom, role-aware EvaluationStrategy.
    """
    def __init__(self, rule_library: Optional[StrategyRuleLibrary] = None) -> None:
        self._library = rule_library or StrategyRuleLibrary()

    def generate_strategy(self, role_profile: RoleProfile) -> EvaluationStrategy:
        """
        Consumes a RoleProfile and outputs the corresponding EvaluationStrategy.
        If the exact evaluation profile identifier is not found, resolves to a fallback strategy.

        Args:
            role_profile: The classified RoleProfile object.

        Returns:
            An EvaluationStrategy containing weights and strictness settings.

        Raises:
            EvaluationStrategyError: If generation fails.
        """
        if role_profile is None:
            raise EvaluationStrategyError("RoleProfile cannot be None.")

        profile_id = role_profile.evaluation_profile
        logger.info("Generating evaluation strategy for profile: %s", profile_id)

        if not self._library.has_profile(profile_id):
            fallback_id = self._determine_fallback_profile(role_profile)
            logger.warning(
                "Evaluation profile '%s' not registered. Falling back to '%s'.",
                profile_id,
                fallback_id,
            )
            profile_id = fallback_id

        try:
            config = self._library.get_profile_config(profile_id)
            return EvaluationStrategy(**config)
        except Exception as e:
            raise EvaluationStrategyError(
                f"Failed to generate strategy for profile '{profile_id}': {e}"
            ) from e

    def _determine_fallback_profile(self, role_profile: RoleProfile) -> str:
        """
        Determines a suitable fallback profile when the exact one is not found.
        """
        # Map seniority level to prefix
        seniority_map = {
            "intern": "intern",
            "entry": "intern",
            "junior": "intern",
            "mid_level": "mid",
            "senior": "senior",
            "lead": "senior",
            "manager": "senior",
            "director": "senior",
            "staff": "senior",
        }
        prefix = seniority_map.get(role_profile.seniority.lower(), "mid")

        # Map specialization to clean name (remove '_engineer', '_scientist', etc. if needed)
        spec_clean = role_profile.specialization.lower()
        suffixes_to_remove = ["_engineer", "_scientist", "_manager", "_developer"]
        for suffix in suffixes_to_remove:
            if spec_clean.endswith(suffix):
                spec_clean = spec_clean[:-len(suffix)]
                break

        fallback_candidate = f"{prefix}_{spec_clean}"
        if self._library.has_profile(fallback_candidate):
            return fallback_candidate

        # Try to map based on role family
        family_clean = role_profile.role_family.lower()
        if "data" in family_clean or "ai" in family_clean:
            ml_candidate = f"{prefix}_ml"
            if self._library.has_profile(ml_candidate):
                return ml_candidate
        
        # Default to backend matching seniority
        backend_candidate = f"{prefix}_backend"
        if self._library.has_profile(backend_candidate):
            return backend_candidate

        # Hard fallback
        return "mid_backend"
