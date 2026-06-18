"""
Phase 5 §5.7 — Skill Tier Classifier.

Maps a normalized skill_evidence_score (0–100) to a human-readable
evidence tier label.

Tier thresholds (as specified in Phase 5 design):
    90–100  → "Expert Evidence"
    70–89   → "Strong Evidence"
    40–69   → "Moderate Evidence"
    0–39    → "Limited Evidence"

IMPORTANT: Tier labels describe evidence strength, NOT proficiency.
           "Expert Evidence" means there is extensive, multi-source evidence
           that the candidate has used this skill — it does NOT mean
           the candidate is an expert practitioner of the skill.

This class is intentionally pure and stateless. It has no dependencies
and contains no business logic beyond the tier thresholds.
"""

from __future__ import annotations

import logging
from enum import Enum
from typing import Dict

logger = logging.getLogger("app.phase5.scoring.tier_classifier")


# ---------------------------------------------------------------------------
# Tier thresholds — the ONLY hardcoded values in the scoring layer
# ---------------------------------------------------------------------------

class EvidenceTier(str, Enum):
    """
    Canonical evidence tier labels.

    Using an enum ensures that Phase 7, 8, and 9 can import and match
    on tier values without string literals scattered across the codebase.
    """
    EXPERT = "Expert Evidence"
    STRONG = "Strong Evidence"
    MODERATE = "Moderate Evidence"
    LIMITED = "Limited Evidence"


# Threshold boundaries (inclusive lower bound for each tier)
_TIER_THRESHOLDS: tuple[tuple[float, EvidenceTier], ...] = (
    (90.0, EvidenceTier.EXPERT),
    (70.0, EvidenceTier.STRONG),
    (40.0, EvidenceTier.MODERATE),
    (0.0, EvidenceTier.LIMITED),
)


class TierClassifier:
    """
    §5.7 Classifies skill evidence scores into descriptive tier labels.

    Stateless — all methods are pure functions of their inputs.
    """

    def classify(self, skill_evidence_score: float) -> str:
        """
        Maps a single evidence score to its tier label.

        Args:
            skill_evidence_score: Normalized score in range [0, 100].

        Returns:
            One of: "Expert Evidence", "Strong Evidence",
                    "Moderate Evidence", "Limited Evidence".
        """
        # Clamp defensively — scores should already be in [0, 100]
        score = min(max(skill_evidence_score, 0.0), 100.0)

        for threshold, tier in _TIER_THRESHOLDS:
            if score >= threshold:
                label = tier.value
                logger.debug(
                    "TierClassifier: score=%.2f → '%s'", score, label
                )
                return label

        # Unreachable: 0.0 threshold always matches, but satisfies type checker
        return EvidenceTier.LIMITED.value  # pragma: no cover

    def classify_all(self, skill_scores: Dict[str, float]) -> Dict[str, str]:
        """
        Classifies all skills in a score dictionary.

        Args:
            skill_scores: Dict mapping skill_name → skill_evidence_score.

        Returns:
            Dict mapping skill_name → tier label string.
        """
        result = {
            skill: self.classify(score)
            for skill, score in skill_scores.items()
        }

        # Log tier distribution for observability
        from collections import Counter
        distribution = Counter(result.values())
        logger.info(
            "TierClassifier: classified %d skill(s). Distribution: %s",
            len(result),
            dict(distribution),
        )

        return result
