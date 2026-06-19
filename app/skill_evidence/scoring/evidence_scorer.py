"""
Phase 5 §5.6 — Skill Evidence Scoring Engine.

Aggregates all collected evidence weights into a single normalized
`skill_evidence_score` (0–100) per skill.

Scoring Formula:
    raw_score = Σ(weight for each evidence piece)
    normalized_score = min(100, raw_score × SCALING_FACTOR)

Weight schedule (from EvidenceWeight):
    Direct mention (skills section)  → +1.0
    Project technology mention       → +0.8  (per distinct project)
    Experience technology mention    → +0.8  (per distinct role/company)
    Dependency supporting skill      → +0.5  (per supporting skill)
    Inherited project                → +0.3  (per inherited project)

Scaling Factor:
    SCALING_FACTOR = 25.0

Calibration:
    A skill with 1 direct mention + 1 project mention + 2 dependency skills:
    raw = 1.0 + 0.8 + (2 × 0.5) = 3.3
    normalized = min(100, 3.3 × 25) = 82.5 → "Strong Evidence"

    A skills-only mention with no projects or dependencies:
    raw = 1.0
    normalized = min(100, 1.0 × 25) = 25.0 → "Limited Evidence"

    This produces the desired distribution: most evidenced skills land
    in the 40–90 range naturally.

IMPORTANT: This score is NOT proficiency. It represents the strength
           and breadth of observable evidence for the skill.
"""

from __future__ import annotations

import logging
from typing import Dict, List

from app.skill_evidence.models.evidence_models import (
    DependencyEvidence,
    EvidenceWeight,
    InheritedProjectEvidence,
    SkillEvidence,
)

logger = logging.getLogger("app.skill_evidence.scoring.evidence_scorer")

# The only "magic number" in Phase 5 scoring — tuned for the 40–90 target range.
# Increasing this pushes more skills into higher tiers; decreasing compresses scores.
SCALING_FACTOR: float = 25.0


class EvidenceScorer:
    """
    §5.6 Converts multi-source evidence into normalized skill evidence scores.

    This class is intentionally stateless and pure — given the same inputs
    it always produces the same outputs, making it trivially unit-testable.

    Collaborators:
      - SkillEvidence (from EvidenceCollectionEngine)
      - DependencyEvidence (from DependencyExpansionEngine)
      - InheritedProjectEvidence (from ProjectInheritanceEngine)
    """

    def score(
        self,
        evidence_map: Dict[str, SkillEvidence],
        dependency_map: Dict[str, DependencyEvidence],
        inheritance_map: Dict[str, InheritedProjectEvidence],
    ) -> Dict[str, float]:
        """
        Computes normalized evidence scores for all skills.

        Args:
            evidence_map: Direct evidence per skill (§5.1 output).
            dependency_map: Dependency evidence per skill (§5.2 output).
            inheritance_map: Inherited project evidence per skill (§5.3 output).

        Returns:
            Dict mapping skill_name → skill_evidence_score (float 0–100).
        """
        scores: Dict[str, float] = {}

        all_skills = set(evidence_map.keys())

        for skill in all_skills:
            raw_score = self._compute_raw_score(
                skill=skill,
                evidence=evidence_map.get(skill),
                dependency=dependency_map.get(skill),
                inheritance=inheritance_map.get(skill),
            )

            normalized = min(100.0, raw_score * SCALING_FACTOR)
            scores[skill] = round(normalized, 2)

            logger.debug(
                "Skill '%s': raw=%.3f, normalized=%.2f",
                skill, raw_score, normalized,
            )

        logger.info(
            "EvidenceScorer: scored %d skill(s). "
            "Score range: %.1f – %.1f",
            len(scores),
            min(scores.values(), default=0.0),
            max(scores.values(), default=0.0),
        )

        return scores

    # -----------------------------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------------------------

    def _compute_raw_score(
        self,
        skill: str,
        evidence: SkillEvidence | None,
        dependency: DependencyEvidence | None,
        inheritance: InheritedProjectEvidence | None,
    ) -> float:
        """
        Sums all evidence weights for a single skill.

        Each evidence piece contributes exactly the weight assigned to its
        source type by EvidenceWeight. Multiple pieces from the same source
        type can accumulate (e.g., multiple projects).
        """
        raw = 0.0
        breakdown: List[str] = []

        # ----------------------------------------------------------------
        # Direct evidence (§5.1)
        # ----------------------------------------------------------------
        if evidence:
            # Direct mention in skills section
            if evidence.direct_mentions > 0:
                contribution = float(EvidenceWeight.DIRECT) * evidence.direct_mentions
                raw += contribution
                breakdown.append(
                    f"direct×{evidence.direct_mentions}={contribution:.2f}"
                )

            # Each distinct project mention
            if evidence.project_mentions:
                contribution = float(EvidenceWeight.PROJECT) * len(evidence.project_mentions)
                raw += contribution
                breakdown.append(
                    f"projects×{len(evidence.project_mentions)}={contribution:.2f}"
                )

            # Each distinct experience mention
            if evidence.experience_mentions:
                contribution = float(EvidenceWeight.PROJECT) * len(evidence.experience_mentions)
                raw += contribution
                breakdown.append(
                    f"experience×{len(evidence.experience_mentions)}={contribution:.2f}"
                )

        # ----------------------------------------------------------------
        # Dependency evidence (§5.2)
        # ----------------------------------------------------------------
        if dependency and dependency.supporting_skills:
            contribution = float(EvidenceWeight.DEPENDENCY) * len(dependency.supporting_skills)
            raw += contribution
            breakdown.append(
                f"deps×{len(dependency.supporting_skills)}={contribution:.2f}"
            )

        # ----------------------------------------------------------------
        # Inherited project evidence (§5.3)
        # ----------------------------------------------------------------
        if inheritance and inheritance.inherited_projects:
            contribution = float(EvidenceWeight.INHERITED) * len(inheritance.inherited_projects)
            raw += contribution
            breakdown.append(
                f"inherited×{len(inheritance.inherited_projects)}={contribution:.2f}"
            )

        logger.debug("Skill '%s' raw score breakdown: [%s] → %.3f", skill, ", ".join(breakdown), raw)
        return raw
