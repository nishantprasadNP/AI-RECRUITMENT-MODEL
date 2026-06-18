"""
Confidence calculator for combining normalized signals into a final score and classification.
"""

import logging
from enum import Enum
from typing import Tuple, Any


# Setup logger
logger = logging.getLogger("app.experience_analysis.confidence_calculator")


# Scoring weights and constants to avoid magic numbers
WEIGHT_PROJECT = 0.0
WEIGHT_PROFESSIONAL = 0.30
WEIGHT_DEPTH = 0.45
WEIGHT_COMPLEXITY = 0.25
WEIGHT_ACHIEVEMENT = 0.0

SCALE_FACTOR = 100.0
SIGNAL_MIN = 0.0
SIGNAL_MAX = 1.0

THRESHOLD_WEAK = 25.0
THRESHOLD_MODERATE = 50.0
THRESHOLD_STRONG = 75.0


class ConfidenceLevel(str, Enum):
    """
    Enum representing qualitative levels of confidence evidence.
    """
    WEAK = "Weak Evidence"
    MODERATE = "Moderate Evidence"
    STRONG = "Strong Evidence"
    VERY_STRONG = "Very Strong Evidence"


class SkillConfidenceCalculator:
    """
    Orchestrates confidence score calculation and categorization across normalized signal inputs.
    """

    def _normalize_signal(self, val: Any) -> float:
        """
        Safely normalizes and clamps a value to a float in range [0.0, 1.0].
        If coercion fails, returns 0.0.

        Args:
            val: Input value of any type.

        Returns:
            A float value between 0.0 and 1.0.
        """
        if val is None:
            return SIGNAL_MIN

        try:
            float_val = float(val)
        except (ValueError, TypeError):
            logger.warning(f"Could not convert signal value '{val}' to float. Defaulting to 0.0.")
            return SIGNAL_MIN

        return min(max(float_val, SIGNAL_MIN), SIGNAL_MAX)

    def calculate(
        self,
        professional_signal: float,
        depth_signal: float,
        complexity_signal: float
    ) -> Tuple[float, ConfidenceLevel]:
        """
        Combines all normalized signals into a single score and ConfidenceLevel.

        Args:
            professional_signal: Signal based on role usage.
            depth_signal: Signal based on mention density.
            complexity_signal: Signal based on project sophistication.

        Returns:
            A tuple of (confidence_score, confidence_level).
        """
        # Validate and clamp inputs
        prof = self._normalize_signal(professional_signal)
        depth = self._normalize_signal(depth_signal)
        comp = self._normalize_signal(complexity_signal)

        # Weighted calculation
        raw_score = (
            WEIGHT_DEPTH * depth
            + WEIGHT_PROFESSIONAL * prof
            + WEIGHT_COMPLEXITY * comp
        )

        # Convert to 0-100 scale
        confidence_score = raw_score * SCALE_FACTOR

        # Classify thresholds
        if confidence_score <= THRESHOLD_WEAK:
            level = ConfidenceLevel.WEAK
        elif confidence_score <= THRESHOLD_MODERATE:
            level = ConfidenceLevel.MODERATE
        elif confidence_score <= THRESHOLD_STRONG:
            level = ConfidenceLevel.STRONG
        else:
            level = ConfidenceLevel.VERY_STRONG

        logger.info(
            f"Calculated confidence score: {confidence_score:.2f} ({level.value}) from signals - "
            f"Prof: {prof:.2f}, Depth: {depth:.2f}, Complexity: {comp:.2f}"
        )

        return confidence_score, level


    def get_skill_tier(self, confidence_score: float) -> str:
        """
        Determines the recruiter-friendly skill tier based on the confidence score.

        Tiers:
            90-100 -> Expert
            70-89  -> Advanced
            40-69  -> Intermediate
            0-39   -> Beginner
        """
        # Clamp score just in case
        score = min(max(confidence_score, 0.0), 100.0)
        if score >= 90.0:
            return "Expert"
        elif score >= 70.0:
            return "Advanced"
        elif score >= 40.0:
            return "Intermediate"
        else:
            return "Beginner"

